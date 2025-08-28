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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        DedupeMixin.__init__(self)
        FeedCounterMixin.__init__(self)
        ProgressiveLoadMixin.__init__(self)

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
            self._refresh_button.setToolTip("Tühista / Värskenda")
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
                self.overdue_pills = OverdueDueSoonPillsWidget(self.toolbar_area)
            except Exception:
                self.overdue_pills = None
            if self.overdue_pills:
                self.toolbar_area.add_right(self.overdue_pills)
            self.toolbar_area.add_right(self._refresh_button)
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
