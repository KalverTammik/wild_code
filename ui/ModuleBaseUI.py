# -*- coding: utf-8 -*-
"""
ModuleBaseUI – residentne feed'i UI-baas QGIS pluginale.

Põhimõtted:
- Ainult progressiivne laadimine (drip → muidu schedule_load), ilma MAX_CARDS piiranguta.
- Esmatäide: tilguta kuni scrollbar aktiveerub (või andmed lõppevad).
- Scrolli sündmused on idempotentselt ühendatud.
- Kaarti lisades ei käivita scroll-handlerit (_ignore_scroll_event).
"""
from typing import Optional, Callable, Sequence
from qgis.core import QgsSettings
from PyQt5.QtCore import Qt, QTimer, QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea

from ..widgets.DataDisplayWidgets.ModuleFeedBuilder import ModuleFeedBuilder
from ..ui.ToolbarArea import ModuleToolbarArea
from ..widgets.FeedCounterWidget import FeedCounterWidget
from .mixins.dedupe_mixin import DedupeMixin
from .mixins.feed_counter_mixin import FeedCounterMixin
from .mixins.progressive_load_mixin import ProgressiveLoadMixin
from ..feed.feed_load_engine import FeedLoadEngine
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..constants.settings_keys import SettingsService
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.messagesHelper import ModernMessageDialog



class ModuleBaseUI(DedupeMixin, FeedCounterMixin, ProgressiveLoadMixin, QWidget):
    """Unified base UI for module feeds.
    """

    PREFETCH_PX: int = 300  # default; ProgressiveLoadMixin also uses this
    LOAD_DEBOUNCE_MS: int = 80


    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None) -> None:
        QWidget.__init__(self, parent)
        DedupeMixin.__init__(self)
        FeedCounterMixin.__init__(self)
        ProgressiveLoadMixin.__init__(self)

        self.lang_manager = lang_manager
        self._settings_service = SettingsService()
        self._filter_widgets = []

        self.status_filter = None
        self.type_filter = None
        self.tags_filter = None
        self.tags_match_mode = "ANY"

        # Preference loading guards
        self._status_filter_signal_connected = False
        self._type_filter_signal_connected = False
        self._tags_filter_signal_connected = False
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False
        self._tags_preferences_loaded = False

        self.feed_layout = None

        self.feed_load_engine = None
        self.feed_logic = None
        self._extract_item_id_error_logged = False

        self.layout = QVBoxLayout(self)
        self.toolbar_area = ModuleToolbarArea(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("ModuleScrollArea")
        self.scroll_area.setWidgetResizable(True)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        toolbar_layout.setSpacing(6)
        self.toolbar_area.setLayout(toolbar_layout)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(4, 2, 4, 2)
        footer_layout.setSpacing(6)

        self.footer_area = QWidget(self)
        self.footer_area.setLayout(footer_layout)
        self.feed_counter = FeedCounterWidget(self.footer_area)
        self.footer_area.layout().addWidget(self.feed_counter)

        self.layout.addWidget(self.toolbar_area)
        self.layout.addWidget(self.scroll_area, 1)
        self.layout.addWidget(self.footer_area)

        self._activated = False

    def _extract_item_id(self, item):  # pragma: no cover - default hook
        """Subclasses can override to provide stable IDs for dedupe."""
        return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def activate(self) -> None:
        """Activate (idempotent)."""
        if self._activated:
            return
        self._activated = True

        
        if self.feed_load_engine is None:
            self.init_feed_engine(self.load_next_batch, debounce_ms=self.LOAD_DEBOUNCE_MS)

        self.reset_feed_session()

        self._connect_scroll_signals()


    def deactivate(self) -> None:
        """Deactivate and optionally cancel engine work."""
        self._activated = False
        engine = self.feed_load_engine
        engine.reset()




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

        layout = self.feed_layout
        if layout is None:
            return
        stable_id = self._safe_extract_item_id(item)
        force_accept = layout.count() <= 2
        is_duplicate = False
        if not force_accept:
            if self._mark_or_skip_duplicate(item):
                is_duplicate = True
        if is_duplicate:
            return
        if force_accept and stable_id is not None:
            if stable_id not in self._seen_item_ids:
                self._seen_item_ids.add(stable_id)
        insert_index = 1 if insert_at_top else max(0, layout.count() - 1)
        self._ignore_scroll_event = True
        try:
            # Pass module name to card creation for number display settings
            module_name = getattr(self, 'name', None) or getattr(self, 'module_name', 'default')
            card = ModuleFeedBuilder.create_item_card(item, module_name=module_name, lang_manager=self.lang_manager)
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
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
                           retheme_func: Optional[Callable[[], None]] = None,
                           insert_at_top: bool = False):
        self._extract_item_id_error_logged = False
        items = self._fetch_next_batch_safe()
        if items is None:
            return []

        engine = self.feed_load_engine
        if engine is None:
            return []

        engine.progressive_insert_func = (
            lambda item: self._progressive_insert_card(item, insert_at_top=insert_at_top)
        )

        filtered = self._filter_new_items(items)

        self._schedule_post_batch_updates(retheme_func)

        return filtered

    # --- Batch helpers -------------------------------------------------
    def _fetch_next_batch_safe(self) -> Optional[list]:
        feed_logic = self.feed_logic
        if feed_logic is None:
            return None
        try:
            return feed_logic.fetch_next_batch() or []
        except Exception as exc:
            session_msg = LanguageManager.translate_static(TranslationKeys.SESSION_EXPIRED)
            if session_msg and str(exc) == session_msg:
                heading = LanguageManager.translate_static(TranslationKeys.SESSION_EXPIRED_TITLE)
                ModernMessageDialog.Warning_messages_modern(heading, session_msg)
                return None
            raise

    def _filter_new_items(self, items) -> list:
        if not items:
            return []

        seen = self._seen_item_ids
        filtered = []
        for item in items:
            stable_id = self._safe_extract_item_id(item)
            if stable_id is not None and stable_id in seen:
                continue
            filtered.append(item)
        return filtered

    def _schedule_post_batch_updates(self, retheme_func: Optional[Callable[[], None]]):
        if self.scroll_area is not None:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        QTimer.singleShot(0, self._initial_autofill_tick)
        QTimer.singleShot(0, self._update_counter_snapshot)

        if retheme_func:
            retheme_func()

    def _update_counter_snapshot(self):
        feed_logic = self.feed_logic
        total = feed_logic.total_count if feed_logic else None
        try:
            loaded = self._compute_loaded_cards()
        except Exception:
            loaded = 0
        try:
            self._set_feed_counter(loaded, total)
        except Exception:
            pass

    def clear_feed(self, feed_layout, empty_state: Optional[QWidget] = None) -> None:
        if getattr(self, '_clearing_feed', False) or feed_layout is None:
            return
        self._clearing_feed = True
        try:
            while feed_layout.count() > 2:
                item = feed_layout.takeAt(1)
                widget = item.widget() if item else None
                if widget:
                    widget.deleteLater()
            if empty_state:
                empty_state.setVisible(False)
            self._reset_dedupe()
        finally:
            self._clearing_feed = False
        self._update_feed_counter_live()

    def reset_feed_session(self):
        """Hard reset before (re)opening a feed: clears UI cards, dedupe, engine buffer, and pagination."""
        layout = getattr(self, 'feed_layout', None)
        if layout:
            while layout.count() > 2:
                item = layout.takeAt(1)
                widget = item.widget() if item else None
                if widget:
                    widget.deleteLater()

        self._reset_dedupe()

        if self.feed_load_engine:
            self.feed_load_engine.reset()

        feed_logic = self.feed_logic
        if feed_logic and hasattr(feed_logic, 'reset_pagination'):
            feed_logic.reset_pagination()


 
    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_extract_item_id(self, item) -> Optional[str]:
        try:
            return self._extract_item_id(item)
        except Exception as exc:
            if not self._extract_item_id_error_logged:
                self._extract_item_id_error_logged = True
                try:
                    print(f"[ModuleBaseUI] _extract_item_id failed: {exc}")
                except Exception:
                    pass
            return None

    def _build_has_tags_condition(
        self,
        tag_ids: Sequence[str],
        *,
        match_mode: Optional[str] = None,
    ) -> Optional[dict]:
        """Map tag selections to Kavitro QueryProjectsHasTagsWhereHasConditions.

        Reference: Kavitro docs › GraphQL › Inputs › QueryProjectsHasTagsWhereHasConditions.
        """
        ids = [str(tag_id).strip() for tag_id in tag_ids if tag_id]
        if not ids:
            return None

        mode = (match_mode or self.tags_match_mode or "ANY").upper()
        if mode == "ALL":
            return {
                "AND": [
                    {"column": "ID", "operator": "EQ", "value": tag_id}
                    for tag_id in ids
                ]
            }

        return {"column": "ID", "operator": "IN", "value": ids}
