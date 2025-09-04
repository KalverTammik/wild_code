# -*- coding: utf-8 -*-
"""
ModuleBaseUI – residentne feed'i UI-baas QGIS pluginale.

Põhimõtted:
- Ainult progressiivne laadimine (drip → muidu schedule_load), ilma MAX_CARDS piiranguta.
- Esmatäide: tilguta kuni scrollbar aktiveerub (või andmed lõppevad).
- Scrolli sündmused on idempotentselt ühendatud.
- Kaarti lisades ei käivita scroll-handlerit (_ignore_scroll_event).
"""

from typing import Optional, Callable

from PyQt5.QtCore import Qt, QTimer, QCoreApplication, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from ..widgets.DataDisplayWidgets.ModuleFeedBuilder import ModuleFeedBuilder
from ..ui.ToolbarArea import ToolbarArea
from ..widgets.FeedCounterWidget import FeedCounterWidget
from ..widgets.OverdueDueSoonPillsWidget import OverdueDueSoonPillsWidget
from .mixins.dedupe_mixin import DedupeMixin
from .mixins.feed_counter_mixin import FeedCounterMixin
from .mixins.progressive_load_mixin import ProgressiveLoadMixin
from ..feed.feed_load_engine import FeedLoadEngine
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..utils.logger import debug as log_debug
import traceback


class ModuleBaseUI(DedupeMixin, FeedCounterMixin, ProgressiveLoadMixin, QWidget):
    """Unified base UI for module feeds.

    Composition:
      - DedupeMixin: duplicate card suppression.
      - FeedCounterMixin: loaded/total counter utilities.
      - ProgressiveLoadMixin: scroll, viewport fullness & initial autofill helpers.

    Responsibilities kept here:
      - Layout scaffold (toolbar, display, footer).
      - Wiring to FeedLoadEngine.
      - Card construction + theming.
      - Public process_next_batch API used by modules.
    """

    PREFETCH_PX: int = 300  # default; ProgressiveLoadMixin also uses this

    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None) -> None:
        QWidget.__init__(self, parent)
        DedupeMixin.__init__(self)
        FeedCounterMixin.__init__(self)
        ProgressiveLoadMixin.__init__(self)

        self.lang_manager = lang_manager

        self.feed_load_engine = None  # set via init_feed_engine

        # Layout scaffold
        self.layout = QVBoxLayout(self)
        self.toolbar_area = ToolbarArea(self)
        self.display_area = QWidget(self)
        self.footer_area = QWidget(self)
        self.layout.addWidget(self.toolbar_area)
        self.layout.addWidget(self.display_area, 1)
        self.layout.addWidget(self.footer_area)
        self.display_area.setLayout(QVBoxLayout())
        # Footer now horizontal to place counters + pills side by side
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(4, 2, 4, 2)
        footer_layout.setSpacing(6)
        self.footer_area.setLayout(footer_layout)
        self.feed_counter = FeedCounterWidget(self.footer_area)
        self.footer_area.layout().addWidget(self.feed_counter)
        # Overdue / due soon pills now migrate to toolbar (right side) next to refresh
        self.overdue_pills = None

        # Verbose flag: when True, short debug prints go to stdout
        self.verbose = False

        self._activated = False

        # Add refresh button & pills (right side)
        try:
            # Use a cross symbol to indicate cancel/clear action visually
            self._refresh_button = QPushButton("✖")
            self._refresh_button.setObjectName("FeedRefreshButton")
            # Prevent button from being triggered by Return key
            self._refresh_button.setAutoDefault(False)
            self._refresh_button.setDefault(False)
            # Make the cross less visually dominant and the button circular.
            # Use a fixed square size and a border-radius = half size to get a round button.
            try:
                size_px = 28
                self._refresh_button.setFixedSize(size_px, size_px)
                # lighter glyph, small font, transparent background and round shape
                self._refresh_button.setStyleSheet(
                    "color: #b0b0b0; font-size: 14px; background: transparent; border: 0px;"
                    f"border-radius: {int(size_px/2)}px; padding: 0px;"
                )
                self._refresh_button.setFlat(True)
                # Store original style for hover revert and enable hover behavior
                try:
                    self._refresh_button._orig_fixed_size = (size_px, size_px)
                    self._refresh_button._orig_style = self._refresh_button.styleSheet()
                    self._refresh_button._orig_text = self._refresh_button.text()
                    # Install event filter so we can emulate themeSwitchButton hover behavior
                    self._refresh_button.installEventFilter(self)
                except Exception:
                    pass
            except Exception:
                pass
            self._refresh_button.clicked.connect(self._on_refresh_clicked)  # type: ignore[attr-defined]
            # Create pills widget owned by toolbar for visual proximity (placed just left of refresh)
            try:
                self.overdue_pills = OverdueDueSoonPillsWidget(self.toolbar_area, self.lang_manager)
            except Exception:
                self.overdue_pills = None
            if self.overdue_pills:
                self.toolbar_area.add_right(self._refresh_button)
            self.toolbar_area.add_right(self.overdue_pills)
        except Exception:
            pass

    def set_verbose(self, enabled: bool) -> None:
        self.verbose = bool(enabled)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def activate(self) -> None:
        """Activate (idempotent)."""
        if self._activated:
            return
        self._activated = True
        # Start with a fresh feed session (dedupe, buffer, pagination) before first fetch
        try:
            self.reset_feed_session()
        except Exception:
            try:
                print("[FeedSession] reset_feed_session failed during activate")
            except Exception:
                pass
        try:
            if hasattr(self, 'status_filter') and self.status_filter:
                self.status_filter.ensure_loaded()
                # Load and apply saved status preferences if the method exists
                if hasattr(self, '_load_and_apply_status_preferences'):
                    self._load_and_apply_status_preferences()
        except Exception:
            pass
        try:
            if hasattr(self, 'type_filter') and self.type_filter:
                self.type_filter.ensure_loaded()
                # Load and apply saved type preferences if the method exists
                if hasattr(self, '_load_and_apply_type_preferences'):
                    self._load_and_apply_type_preferences()
        except Exception:
            pass
        try:
            if hasattr(self, 'tags_filter') and self.tags_filter:
                self.tags_filter.ensure_loaded()
                # Load and apply saved tags preferences if the method exists
                if hasattr(self, '_load_and_apply_tags_preferences'):
                    self._load_and_apply_tags_preferences()
        except Exception:
            pass
        self._connect_scroll_signals()

    def deactivate(self) -> None:
        """Deactivate and optionally cancel engine work."""
        self._activated = False
        engine = getattr(self, 'feed_load_engine', None)
        if engine and hasattr(engine, 'cancel'):
            try:
                engine.cancel()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Refresh button handler
    # ------------------------------------------------------------------
    def _on_refresh_clicked(self):
        """Hard refresh: reset session then trigger a fresh scheduled load."""
        # Clear filters (they are reactive themselves) before resetting
        try:
            toolbar = getattr(self, 'toolbar_area', None)
            if toolbar and hasattr(toolbar, 'filter_widgets'):
                for _name, widget in list(toolbar.filter_widgets.items()):
                    try:
                        if hasattr(widget, 'set_selected_ids'):
                            widget.set_selected_ids([])  # type: ignore[attr-defined]
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Reset preferences loaded flags so they can be reloaded
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False
        self._tags_preferences_loaded = False
        try:
            self.reset_feed_session()
        except Exception:
            pass
        try:
            eng = getattr(self, 'feed_load_engine', None)
            if eng:
                eng.schedule_load()
            else:
                # Fallback: directly pull a batch if engine not yet wired
                self.process_next_batch()
        except Exception:
            pass

    def eventFilter(self, watched, event):
        """Handle hover for the refresh button to mimic theme switch hover styles.

        On hover enter: show text 'Tühjenda' and apply theme-appropriate hover background/text.
        On hover leave: revert to original compact circular style.
        """
        try:
            if watched is getattr(self, '_refresh_button', None):
                # Determine theme
                from ..widgets.theme_manager import ThemeManager
                theme = ThemeManager.load_theme_setting() if hasattr(ThemeManager, 'load_theme_setting') else 'light'
                if event.type() == QEvent.Enter or event.type() == QEvent.HoverEnter:
                    try:
                        # Expand a bit to show text and apply hover colors matching header.qss
                        if theme == 'dark':
                            hover_bg = '#00796b'
                            hover_color = 'white'
                        else:
                            hover_bg = '#e1e4e8'
                            hover_color = '#000000'
                        # Slightly widen the button to fit text while keeping height
                        h, w = getattr(self._refresh_button, '_orig_fixed_size', (28, 28))
                        self._refresh_button.setFixedSize(w + 34, h)
                        self._refresh_button.setText('Tühjenda')
                        self._refresh_button.setStyleSheet(f"background: {hover_bg}; color: {hover_color}; border-radius: {int(h/2)}px; padding: 4px 8px; border: none;")
                    except Exception:
                        pass
                    return True
                elif event.type() == QEvent.Leave or event.type() == QEvent.HoverLeave:
                    try:
                        # Revert to original compact circle
                        h, w = getattr(self._refresh_button, '_orig_fixed_size', (28, 28))
                        self._refresh_button.setFixedSize(h, w)
                        self._refresh_button.setText(getattr(self._refresh_button, '_orig_text', '✖'))
                        self._refresh_button.setStyleSheet(getattr(self._refresh_button, '_orig_style', ''))
                    except Exception:
                        pass
                    return True
        except Exception:
            pass
        return super().eventFilter(watched, event)

    # ------------------------------------------------------------------
    # Feed engine wiring
    # ------------------------------------------------------------------
    def init_feed_engine(self, batch_loader: Callable, debounce_ms: int = 80) -> None:
        self.feed_load_engine = FeedLoadEngine(batch_loader, debounce_ms=debounce_ms)
        self.feed_load_engine.attach(parent_ui=self)
        # Ensure dedupe state is fresh when engine is initialized to avoid
        # skipping items that may have been marked seen during a previous session.
        try:
            self._reset_dedupe()
        except Exception:
            pass
        self._connect_scroll_signals()

    def _connect_scroll_signals(self) -> None:  # override precedence -> ProgressiveLoadMixin
        super()._connect_scroll_signals()  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Card insertion
    # ------------------------------------------------------------------
    def _progressive_insert_card(self, item, insert_at_top: bool = False) -> None:
        layout = getattr(self, 'feed_layout', None)
        if layout is None:
            return
    # Extract stable id (no verbose debug prints retained)
        stable_id = None
        try:
            if hasattr(self, '_extract_item_id'):
                stable_id = self._extract_item_id(item)
        except Exception:
            stable_id = None
        # If layout still empty (no real cards yet) we forcibly accept first batch even if dedupe thinks duplicate
        force_accept = False
        try:
            if layout.count() <= 2:  # only structural widgets present
                force_accept = True
        except Exception:
            pass
        is_duplicate = False
        if not force_accept:
            if self._mark_or_skip_duplicate(item):
                is_duplicate = True
        if is_duplicate:
            return
        # If we force accepted (layout empty), mark ID as seen manually so subsequent items don't double-evaluate
        if force_accept and stable_id is not None:
            try:
                if stable_id not in getattr(self, '_seen_item_ids', set()):
                    self._seen_item_ids.add(stable_id)
            except Exception:
                pass
        insert_index = 1 if insert_at_top else max(0, layout.count() - 1)
        self._ignore_scroll_event = True
        try:
            # Pass module name to card creation for number display settings
            module_name = getattr(self, 'name', None) or getattr(self, 'module_name', 'default')
            card = ModuleFeedBuilder.create_item_card(item, module_name=module_name)
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            # (Prints removed – keep console clean; BatchSummary remains elsewhere)
            layout.insertWidget(insert_index, card)
            QCoreApplication.processEvents()
            try:
                self._update_feed_counter_live()
            except Exception:
                pass
        except Exception as e:
            try:  # logging is best-effort
                print(f"[ModuleBaseUI] Failed to build card: {e}")
            except Exception:
                pass
        finally:
            self._ignore_scroll_event = False

    # ------------------------------------------------------------------
    # Batch processing API
    # ------------------------------------------------------------------
    def process_next_batch(self,
                           revision: Optional[int] = None,
                           log_func: Optional[Callable[[str], None]] = None,
                           retheme_func: Optional[Callable[[], None]] = None,
                           insert_at_top: bool = False):
        try:
            items = self.feed_logic.fetch_next_batch() or []
        except Exception as e:
            msg = str(e)
            if hasattr(self, 'lang_manager') and msg == self.lang_manager.translate("session_expired"):
                return []
            if hasattr(self, 'lang') and msg == self.lang.translate("session_expired"):
                return []
            raise
    # (Fetch summary print removed – BatchSummary will cover counts)
        if not getattr(self, 'feed_load_engine', None):
            if log_func:
                log_func("[ModuleBaseUI] FeedLoadEngine not initialized")
            return []

        # Let engine manage buffering; set engine hook and compute filtered items
        self.feed_load_engine.progressive_insert_func = (
            lambda x: self._progressive_insert_card(x, insert_at_top=insert_at_top)
        )

        filtered = []
        if items:
            seen = getattr(self, '_seen_item_ids', set())
            for it in items:
                try:
                    stable_id = None
                    try:
                        stable_id = self._extract_item_id(it)
                    except Exception:
                        pass
                    if stable_id is not None and stable_id in seen:
                        continue
                except Exception:
                    # On any dedupe-check failure, keep the item
                    filtered.append(it)
                    continue
                filtered.append(it)

        # UI updates (keep these local to the UI; engine will buffer returned items)
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        QTimer.singleShot(0, self._initial_autofill_tick)

        def update_counter_after_autofill():
            fl = getattr(self, 'feed_logic', None)
            total = getattr(fl, 'total_count', None) if fl else None
            loaded = 0
            layout = getattr(self, 'feed_layout', None)
            if layout is not None:
                loaded = layout.count() - 2 if layout.count() > 2 else 0
            self._set_feed_counter(loaded, total)

        QTimer.singleShot(0, update_counter_after_autofill)
        if retheme_func:
            retheme_func()

        # Return the (possibly filtered) items to the caller (FeedLoadEngine will extend its buffer once).
        try:
            layout = getattr(self, 'feed_layout', None)
            loaded_now = (layout.count() - 2) if layout and layout.count() > 2 else 0
            print(f"[BatchSummary] batch_items={len(items)} buffered={len(filtered)} loaded_now={loaded_now} duplicates_skipped={getattr(self,'_duplicate_skip_count',0)} seen={len(getattr(self,'_seen_item_ids',[]))} token={id(getattr(self,'_dedupe_session_token',None))}")
        except Exception:
            pass
        return filtered

    # Scroll handlers -> inherited from ProgressiveLoadMixin

    # Counter helpers -> inherited from FeedCounterMixin

    def clear_feed(self, feed_layout, empty_state: Optional[QWidget] = None) -> None:
        if getattr(self, '_clearing_feed', False):
            return
        self._clearing_feed = True
        try:
            while feed_layout.count() > 2:
                idx = 1
                item = feed_layout.takeAt(idx)
                w = item.widget()
                if w:
                    w.deleteLater()
            if empty_state:
                empty_state.setVisible(False)
            self._reset_dedupe()
        finally:
            self._clearing_feed = False
        try:
            self._update_feed_counter_live()
        except Exception:
            pass

    # Progressive load helpers -> inherited from ProgressiveLoadMixin

    def reset_feed_session(self):
        """Hard reset before (re)opening a feed: clears UI cards, dedupe, engine buffer, and pagination."""
        try:
            # Clear cards except header/footer placeholders
            layout = getattr(self, 'feed_layout', None)
            if layout:
                while layout.count() > 2:
                    item = layout.takeAt(1)
                    w = item.widget() if item else None
                    if w:
                        w.deleteLater()
        except Exception:
            pass
        # Reset dedupe
        try:
            self._reset_dedupe()
        except Exception:
            pass
        # Reset engine
        eng = getattr(self, 'feed_load_engine', None)
        if eng:
            try:
                eng.reset()
            except Exception:
                pass
        # Reset pagination on feed_logic if provided
        fl = getattr(self, 'feed_logic', None)
        if fl and hasattr(fl, 'reset_pagination'):
            try:
                fl.reset_pagination()
            except Exception:
                pass
        try:
            print(f"[FeedSession] reset complete; seen={len(getattr(self,'_seen_item_ids', []))}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Status Preferences Management
    # ------------------------------------------------------------------
    def _load_and_apply_status_preferences(self):
        """Load saved status preferences and apply them to the status filter.
        
        This is a generic implementation that works for any module with a status_filter.
        Subclasses can override this method if they need custom behavior.
        """
        log_debug(f"[{self.__class__.__name__}] _load_and_apply_status_preferences called")
        
        if not hasattr(self, 'status_filter') or not self.status_filter:
            log_debug(f"[{self.__class__.__name__}] No status_filter found")
            return
        
        # Check if status filter is loaded
        if not getattr(self.status_filter, '_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Status filter not loaded yet, deferring preferences loading")
            # Connect to selectionChanged signal to load preferences when filter is ready
            # Only connect if not already connected
            if not getattr(self, '_status_filter_signal_connected', False):
                try:
                    self.status_filter.selectionChanged.connect(self._on_status_filter_loaded)
                    self._status_filter_signal_connected = True
                    log_debug(f"[{self.__class__.__name__}] Connected to status filter selectionChanged signal")
                except Exception as e:
                    log_debug(f"[{self.__class__.__name__}] Failed to connect to selectionChanged: {e}")
            return
        
        # Prevent loading multiple times
        if getattr(self, '_status_preferences_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Status preferences already loaded, skipping")
            return
            
        try:
            # StatusFilterWidget should already be loaded when filters are first used
            # Load saved status preferences for this module
            preferred_statuses = self._load_status_preferences_from_settings()
            log_debug(f"[{self.__class__.__name__}] Loaded preferences from settings: {preferred_statuses}")
            
            if preferred_statuses:
                log_debug(f"[{self.__class__.__name__}] Applying saved status preferences: {preferred_statuses}")
                # Set the selected IDs on the status filter
                self.status_filter.set_selected_ids(list(preferred_statuses))
                # The selectionChanged signal will be emitted automatically, triggering filter updates
            else:
                log_debug(f"[{self.__class__.__name__}] No saved status preferences found")
                
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading status preferences: {e}")
            import traceback
            log_debug(f"[{self.__class__.__name__}] Traceback: {traceback.format_exc()}")
        
        # Mark as loaded to prevent multiple calls
        self._status_preferences_loaded = True
        log_debug(f"[{self.__class__.__name__}] Status preferences loading complete")

    def _on_status_filter_loaded(self):
        """Called when the status filter finishes loading for the first time."""
        log_debug(f"[{self.__class__.__name__}] Status filter loaded, applying preferences")
        
        # Disconnect the signal to avoid multiple calls
        try:
            self.status_filter.selectionChanged.disconnect(self._on_status_filter_loaded)
            self._status_filter_signal_connected = False
        except Exception:
            pass
        
        # Now load and apply the preferences
        self._load_and_apply_status_preferences()

    def _load_status_preferences_from_settings(self) -> set:
        """Load status preferences directly from QGIS settings.
        
        This is a generic implementation that uses the module's NAME attribute
        to create a unique settings key.
        """
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            key = f"wild_code/modules/{self.NAME}/preferred_statuses"
            log_debug(f"[{self.__class__.__name__}] Loading settings from key: {key}")
            preferred_statuses = s.value(key, "") or ""
            log_debug(f"[{self.__class__.__name__}] Raw settings value: '{preferred_statuses}'")

            if preferred_statuses:
                result = set(preferred_statuses.split(","))
                log_debug(f"[{self.__class__.__name__}] Parsed status IDs: {result}")
                return result
            log_debug(f"[{self.__class__.__name__}] No status preferences found in settings")
            return set()
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading status preferences from settings: {e}")
            return set()

    # ------------------------------------------------------------------
    # Type Preferences Management
    # ------------------------------------------------------------------
    def _load_and_apply_type_preferences(self):
        """Load saved type preferences and apply them to the type filter.
        
        This is a generic implementation that works for any module with a type_filter.
        Subclasses can override this method if they need custom behavior.
        """
        log_debug(f"[{self.__class__.__name__}] _load_and_apply_type_preferences called")
        
        if not hasattr(self, 'type_filter') or not self.type_filter:
            log_debug(f"[{self.__class__.__name__}] No type_filter found")
            return
        
        # Check if type filter is loaded
        if not getattr(self.type_filter, '_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Type filter not loaded yet, deferring preferences loading")
            # Connect to selectionChanged signal to load preferences when filter is ready
            # Only connect if not already connected
            if not getattr(self, '_type_filter_signal_connected', False):
                try:
                    self.type_filter.selectionChanged.connect(self._on_type_filter_loaded)
                    self._type_filter_signal_connected = True
                    log_debug(f"[{self.__class__.__name__}] Connected to type filter selectionChanged signal")
                except Exception as e:
                    log_debug(f"[{self.__class__.__name__}] Failed to connect to selectionChanged: {e}")
            return
        
        # Prevent loading multiple times
        if getattr(self, '_type_preferences_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Type preferences already loaded, skipping")
            return
            
        try:
            # TypeFilterWidget should already be loaded when filters are first used
            # Load saved type preferences for this module
            preferred_types = self._load_type_preferences_from_settings()
            log_debug(f"[{self.__class__.__name__}] Loaded type preferences from settings: {preferred_types}")
            
            if preferred_types:
                log_debug(f"[{self.__class__.__name__}] Applying saved type preferences: {preferred_types}")
                # Set the selected IDs on the type filter
                self.type_filter.set_selected_ids(list(preferred_types))
                # The selectionChanged signal will be emitted automatically, triggering filter updates
            else:
                log_debug(f"[{self.__class__.__name__}] No saved type preferences found")
                
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading type preferences: {e}")
            import traceback
            log_debug(f"[{self.__class__.__name__}] Traceback: {traceback.format_exc()}")
        
        # Mark as loaded to prevent multiple calls
        self._type_preferences_loaded = True
        log_debug(f"[{self.__class__.__name__}] Type preferences loading complete")

    def _on_type_filter_loaded(self):
        """Called when the type filter finishes loading for the first time."""
        log_debug(f"[{self.__class__.__name__}] Type filter loaded, applying preferences")
        
        # Disconnect the signal to avoid multiple calls
        try:
            self.type_filter.selectionChanged.disconnect(self._on_type_filter_loaded)
            self._type_filter_signal_connected = False
        except Exception:
            pass
        
        # Now load and apply the preferences
        self._load_and_apply_type_preferences()

    def _load_type_preferences_from_settings(self) -> set:
        """Load type preferences directly from QGIS settings.
        
        This is a generic implementation that uses the module's NAME attribute
        to create a unique settings key.
        """
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            key = f"wild_code/modules/{self.NAME}/preferred_types"
            log_debug(f"[{self.__class__.__name__}] Loading type settings from key: {key}")
            preferred_types = s.value(key, "") or ""
            log_debug(f"[{self.__class__.__name__}] Raw type settings value: '{preferred_types}'")

            if preferred_types:
                result = set(preferred_types.split(","))
                log_debug(f"[{self.__class__.__name__}] Parsed type IDs: {result}")
                return result
            log_debug(f"[{self.__class__.__name__}] No type preferences found in settings")
            return set()
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading type preferences from settings: {e}")
            return set()

    # ------------------------------------------------------------------
    # Tags Preferences Management
    # ------------------------------------------------------------------
    def _load_and_apply_tags_preferences(self):
        """Load saved tags preferences and apply them to the tags filter.
        
        This is a generic implementation that works for any module with a tags_filter.
        Subclasses can override this method if they need custom behavior.
        """
        log_debug(f"[{self.__class__.__name__}] _load_and_apply_tags_preferences called")
        
        if not hasattr(self, 'tags_filter') or not self.tags_filter:
            log_debug(f"[{self.__class__.__name__}] No tags_filter found")
            return
        
        # Check if tags filter is loaded
        if not getattr(self.tags_filter, '_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Tags filter not loaded yet, deferring preferences loading")
            # Connect to selectionChanged signal to load preferences when filter is ready
            # Only connect if not already connected
            if not getattr(self, '_tags_filter_signal_connected', False):
                try:
                    self.tags_filter.selectionChanged.connect(self._on_tags_filter_loaded)
                    self._tags_filter_signal_connected = True
                    log_debug(f"[{self.__class__.__name__}] Connected to tags filter selectionChanged signal")
                except Exception as e:
                    log_debug(f"[{self.__class__.__name__}] Failed to connect to selectionChanged: {e}")
            return
        
        # Prevent loading multiple times
        if getattr(self, '_tags_preferences_loaded', False):
            log_debug(f"[{self.__class__.__name__}] Tags preferences already loaded, skipping")
            return
            
        try:
            # TagsFilterWidget should already be loaded when filters are first used
            # Load saved tags preferences for this module
            preferred_tags = self._load_tags_preferences_from_settings()
            log_debug(f"[{self.__class__.__name__}] Loaded tags preferences from settings: {preferred_tags}")
            
            if preferred_tags:
                log_debug(f"[{self.__class__.__name__}] Applying saved tags preferences: {preferred_tags}")
                # Set the selected IDs on the tags filter
                self.tags_filter.set_selected_ids(list(preferred_tags))
                # The selectionChanged signal will be emitted automatically, triggering filter updates
            else:
                log_debug(f"[{self.__class__.__name__}] No saved tags preferences found")
                
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading tags preferences: {e}")
            import traceback
            log_debug(f"[{self.__class__.__name__}] Traceback: {traceback.format_exc()}")
        
        # Mark as loaded to prevent multiple calls
        self._tags_preferences_loaded = True
        log_debug(f"[{self.__class__.__name__}] Tags preferences loading complete")

    def _on_tags_filter_loaded(self):
        """Called when the tags filter finishes loading for the first time."""
        log_debug(f"[{self.__class__.__name__}] Tags filter loaded, applying preferences")
        
        # Disconnect the signal to avoid multiple calls
        try:
            self.tags_filter.selectionChanged.disconnect(self._on_tags_filter_loaded)
            self._tags_filter_signal_connected = False
        except Exception:
            pass
        
        # Now load and apply the preferences
        self._load_and_apply_tags_preferences()

    def _load_tags_preferences_from_settings(self) -> set:
        """Load tags preferences directly from QGIS settings.
        
        This is a generic implementation that uses the module's NAME attribute
        to create a unique settings key.
        """
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            key = f"wild_code/modules/{self.NAME}/preferred_tags"
            log_debug(f"[{self.__class__.__name__}] Loading tags settings from key: {key}")
            preferred_tags = s.value(key, "") or ""
            log_debug(f"[{self.__class__.__name__}] Raw tags settings value: '{preferred_tags}'")

            if preferred_tags:
                result = set(preferred_tags.split(","))
                log_debug(f"[{self.__class__.__name__}] Parsed tag IDs: {result}")
                return result
            log_debug(f"[{self.__class__.__name__}] No tags preferences found in settings")
            return set()
        except Exception as e:
            log_debug(f"[{self.__class__.__name__}] Error loading tags preferences from settings: {e}")
            return set()
