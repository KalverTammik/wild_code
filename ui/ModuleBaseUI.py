# -*- coding: utf-8 -*-
from __future__ import annotations
"""
ModuleBaseUI – residentne feed'i UI-baas QGIS pluginale.

Põhimõtted:
- Ainult progressiivne laadimine (drip → muidu schedule_load), ilma MAX_CARDS piiranguta.
- Esmatäide: tilguta kuni scrollbar aktiveerub (või andmed lõppevad).
- Scrolli sündmused on idempotentselt ühendatud.
- Kaarti lisades ei käivita scroll-handlerit (_ignore_scroll_event).
"""
from typing import Optional, Callable, TYPE_CHECKING, Protocol, Any
import gc
from PyQt5.QtCore import Qt, QTimer, QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea

from ..ui.ToolbarArea import ModuleToolbarArea
from ..widgets.FeedCounterWidget import FeedCounterWidget
from ..ui.module_card_factory import ModuleCardFactory
from .mixins.dedupe_mixin import DedupeMixin
from .mixins.feed_counter_mixin import FeedCounterMixin
from .mixins.progressive_load_mixin import ProgressiveLoadMixin
from ..feed.feed_load_engine import FeedLoadEngine
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ..Logs.switch_logger import SwitchLogger
from ..Logs.python_fail_logger import PythonFailLogger
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from .mixins.token_mixin import TokenMixin

if TYPE_CHECKING:
    from ..utils.api_error_handling import ApiErrorKind
    class EmptyStateWidgetProtocol(Protocol):
        def setText(self, text: str) -> None: ...
        def setVisible(self, visible: bool) -> None: ...
        def raise_(self) -> None: ...

    class FeedLogicProtocol(Protocol):
        total_count: Optional[int]
        last_response: Optional[object]
        last_error_kind: Optional[ApiErrorKind]
        last_error_message: Optional[str]

        def fetch_next_batch(self) -> list[dict[str, Any]]: ...
        def set_single_item_mode(self, value: bool) -> None: ...
        def set_extra_arguments(self, *args, **kwargs) -> None: ...
        def reset_pagination(self) -> None: ...


class FeedSessionController:
    """Encapsulate feed session lifecycle operations for ModuleBaseUI."""

    def __init__(self, ui: "ModuleBaseUI") -> None:
        self._ui = ui

    def reset_session(self) -> None:
        """Hard reset before (re)opening a feed."""
        self.reset_feed_ui_state()

    def reset_feed_ui_state(self) -> None:
        layout = self._ui.feed_layout
        if layout:
            while layout.count() > 2:
                item = layout.takeAt(1)
                widget = item.widget() if item else None
                if widget:
                    widget.deleteLater()

        self._ui._reset_dedupe()

        if self._ui.feed_load_engine:
            self._ui.feed_load_engine.reset()

        feed_logic = self._ui.active_feed_logic
        if feed_logic:
            reset_fn = getattr(feed_logic, "reset_pagination", None)
            if callable(reset_fn):
                reset_fn()
            else:
                try:
                    PythonFailLogger.log(
                        "module_base_reset_pagination_missing",
                        module=getattr(self._ui, "module_key", None),
                    )
                except Exception:
                    pass

    def clear_feed(self, feed_layout: Optional[QVBoxLayout], empty_state: Optional["EmptyStateWidgetProtocol"] = None) -> None:
        if getattr(self._ui, "_clearing_feed", False) or feed_layout is None:
            return
        self._ui._clearing_feed = True
        try:
            while feed_layout.count() > 2:
                item = feed_layout.takeAt(1)
                widget = item.widget() if item else None
                if widget:
                    widget.deleteLater()
            if empty_state:
                empty_state.setVisible(False)
            self._ui._reset_dedupe()
        finally:
            self._ui._clearing_feed = False
        self._ui._update_feed_counter_live()

    def deactivate_session(self) -> None:
        engine = self._ui.feed_load_engine
        if engine:
            engine.reset()
            engine.progressive_insert_func = None
            engine.parent_ui = None

        # Aggressively drop UI widgets and dedupe state to free memory when module hides
        self.clear_feed(self._ui.feed_layout, self._ui.empty_state)

        # Release cached responses/extra args so objects can be collected
        feed_logic = self._ui.feed_logic
        if feed_logic:
            feed_logic.set_single_item_mode(False)
            feed_logic.set_extra_arguments()
            feed_logic.last_response = None

        # Encourage Python to reclaim Qt object graphs sooner
        gc.collect()


class ModuleBaseUI(DedupeMixin, FeedCounterMixin, ProgressiveLoadMixin, TokenMixin, QWidget):
    """Unified base UI for module feeds.
    """

    PREFETCH_PX: int = 300  # default; ProgressiveLoadMixin also uses this
    LOAD_DEBOUNCE_MS: int = 80


    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None) -> None:
        QWidget.__init__(self, parent)
        DedupeMixin.__init__(self)
        FeedCounterMixin.__init__(self)
        ProgressiveLoadMixin.__init__(self)
        TokenMixin.__init__(self)

        self.lang_manager = lang_manager
        self._settings_logic = SettingsLogic()
        self._filter_widgets: list[QWidget] = []

        self.status_filter: Optional[QWidget] = None
        self.type_filter: Optional[QWidget] = None
        self.tags_filter: Optional[QWidget] = None
        self.tags_match_mode = "ANY"

        # Preference loading guards
        self._status_filter_signal_connected = False
        self._type_filter_signal_connected = False
        self._tags_filter_signal_connected = False
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False
        self._tags_preferences_loaded = False

        self.feed_layout: Optional[QVBoxLayout] = None

        self.feed_load_engine: Optional[FeedLoadEngine] = None
        self.feed_logic: FeedLogicProtocol | None = None
        self._empty_state: Optional["EmptyStateWidgetProtocol"] = None
        self._feed_session = FeedSessionController(self)

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
        self._active_token = 0
        self._visible_once = False

    def _extract_item_id(self, item: dict[str, Any]) -> Optional[str]:  # pragma: no cover - default hook
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
        self._show_loading_placeholder()
        if self.isVisible():
            self._ensure_first_visible()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._activated:
            self._ensure_first_visible()

    def _ensure_first_visible(self) -> None:
        if self._visible_once:
            return
        self._visible_once = True
        if self.feed_load_engine is None:
            self.init_feed_engine(self.load_next_batch, debounce_ms=self.LOAD_DEBOUNCE_MS)
        self.reset_feed_session()
        self._connect_scroll_signals()
        self.on_first_visible()

    def on_first_visible(self) -> None:
        """Hook for subclasses to start heavy loads when first visible."""
        return None


    def deactivate(self) -> None:
        """Deactivate and optionally cancel engine work."""
        self._activated = False
        self._visible_once = False
        self._feed_session.deactivate_session()

    def is_token_active(self, token: int) -> bool:
        return super().is_token_active(token)

    @property
    def active_feed_logic(self) -> FeedLogicProtocol | None:
        return self.feed_logic

    @property
    def empty_state(self) -> EmptyStateWidgetProtocol | None:
        return self._empty_state





    # ------------------------------------------------------------------
    # Feed engine wiring
    # ------------------------------------------------------------------
    def init_feed_engine(self, batch_loader: Callable, debounce_ms: int = 80) -> None:
        self.feed_load_engine = FeedLoadEngine(batch_loader, debounce_ms=debounce_ms)
        self.feed_load_engine.attach(parent_ui=self)
        # Ensure dedupe state is fresh when engine is initialized to avoid
        # skipping items that may have been marked seen during a previous session.
        self._reset_dedupe()
        self._connect_scroll_signals()

    def _connect_scroll_signals(self) -> None:  # override precedence -> ProgressiveLoadMixin
        super()._connect_scroll_signals()  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Card insertion
    # ------------------------------------------------------------------
    def _progressive_insert_card(self, item: dict[str, Any], insert_at_top: bool = False) -> None:
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
            card = ModuleCardFactory.create_card(item, self.lang_manager)
            layout.insertWidget(insert_index, card)
            QCoreApplication.processEvents()
            self._hide_loading_placeholder()
            self._update_feed_counter_live()
        finally:
            self._ignore_scroll_event = False

    # ------------------------------------------------------------------
    # Batch processing API
    # ------------------------------------------------------------------
    def process_next_batch(self,
                           revision: Optional[int] = None,
                           retheme_func: Optional[Callable[[], None]] = None,
                           insert_at_top: bool = False) -> list[dict[str, Any]]:
        if not getattr(self, "_activated", False):
            return []
        feed_logic = self.active_feed_logic
        if feed_logic is None:
            return []
        items = feed_logic.fetch_next_batch() or []
        try:
            module_key = getattr(self, "module_key", None) or getattr(self, "name", None) or ""
            SwitchLogger.log(
                "feed_batch_result",
                module=str(module_key),
                extra={
                    "count": len(items),
                    "has_more": getattr(feed_logic, "has_more", None),
                    "single": getattr(feed_logic, "_single_item_mode", None),
                },
            )
        except Exception:
            pass

        if not items:
            message = feed_logic.last_error_message
            self._show_empty_state(message or "No values found!")
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

    def _show_empty_state(self, message: Optional[str] = None) -> None:
        """Display a friendly empty-state card when no items are returned."""
        empty_state = self.empty_state
        feed_layout = self.feed_layout
        if not empty_state or not feed_layout:
            return
        if not message:
            lang_manager = self.lang_manager or LanguageManager()
            message = lang_manager.translate(TranslationKeys.NO_VALUES_FOUND)

        empty_state.setText(message)
        empty_state.setVisible(True)
        empty_state.raise_()

    def _show_loading_placeholder(self) -> None:
        empty_state = self.empty_state
        if not empty_state:
            return
        lang_manager = self.lang_manager or LanguageManager()
        empty_state.setText(lang_manager.translate(TranslationKeys.LOADING))
        empty_state.setVisible(True)
        empty_state.raise_()

    def _hide_loading_placeholder(self) -> None:
        empty_state = self.empty_state
        if not empty_state:
            return
        try:
            if empty_state.isVisible():
                empty_state.setVisible(False)
        except Exception:
            pass

    def _filter_new_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    def _schedule_post_batch_updates(self, retheme_func: Optional[Callable[[], None]]) -> None:
        if self.scroll_area is not None:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        QTimer.singleShot(0, self._initial_autofill_tick)
        QTimer.singleShot(0, self._update_counter_snapshot)

        if retheme_func:
            retheme_func()

    def _update_counter_snapshot(self) -> None:
        if not getattr(self, "_activated", False):
            return
        feed_logic = self.active_feed_logic
        total = feed_logic.total_count if feed_logic else None
        loaded = self._compute_loaded_cards()
        self._set_feed_counter(loaded, total)

    def clear_feed(self, feed_layout: Optional[QVBoxLayout], empty_state: Optional["EmptyStateWidgetProtocol"] = None) -> None:
        self._feed_session.clear_feed(feed_layout, empty_state)

    def reset_feed_session(self) -> None:
        """Hard reset before (re)opening a feed: clears UI cards, dedupe, engine buffer, and pagination."""
        self._feed_session.reset_session()


 
    def get_widget(self) -> QWidget:
        """Return self as the widget for module system compatibility."""
        return self

    def _reset_feed_ui_state(self) -> None:
        self._feed_session.reset_feed_ui_state()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_extract_item_id(self, item: dict[str, Any]) -> Optional[str]:
        return self._extract_item_id(item)



