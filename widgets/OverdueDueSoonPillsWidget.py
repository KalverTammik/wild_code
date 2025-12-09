"""Overdue / Due Soon pills widget.

Provides two pill buttons inside a small group box plus logic to fetch counts
using two minimal GraphQL queries (first:1) that rely only on pageInfo.total.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QGroupBox, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..python.api_client import APIClient
from ..python.responses import JsonResponseHandler
from ..languages.language_manager import LanguageManager
from ..utils.FilterHelpers.FilterHelper import FilterHelper
from ..languages.translation_keys import TranslationKeys

# Legacy module-level state (kept for compatibility; instance methods use self.*)
OVERDUE_BTN = None
DUE_SOON_BTN = None
IS_LOADING = False
OVERDUE_ACTIVE = False
DUE_SOON_ACTIVE = False

class OverdueDueSoonPillsWidget(QWidget):
    # Emitted when user clicks pills (container will handle applying filters)
    overdueClicked = pyqtSignal()
    dueSoonClicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("OverdueDueSoonPillsWidget")
        self._is_loading = False
        self._days_due_soon: int = 3
        self._overdue_active = False
        self._due_soon_active = False
        self._lang = LanguageManager()  # Ensure _lang is initialized

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        #import translation keys

        title = self._lang.translate(TranslationKeys.URGENT_GROUP_TITLE)
        self.group = QGroupBox(title or "GroupBoxTitle", self)
        self.group.setObjectName("GroupBoxFrame")
        self.group.setToolTip(self._lang.translate(TranslationKeys.URGENT_TOOLTIP))
        pills_layout = QHBoxLayout()
        pills_layout.setContentsMargins(6, 4, 6, 4)
        pills_layout.setSpacing(4)
        self.group.setLayout(pills_layout)
        layout.addWidget(self.group)

        self.overdue_btn = QPushButton(self.group)
        self.overdue_btn.setObjectName("PillOverdue")
        self.overdue_btn.setCheckable(True)
        # Prevent button from being triggered by Return key
        self.overdue_btn.setAutoDefault(False)
        self.overdue_btn.setDefault(False)
        self.overdue_btn.setCursor(Qt.PointingHandCursor)
        self.overdue_btn.clicked.connect(self.overdueClicked.emit)  # type: ignore

        self.due_soon_btn = QPushButton(self.group)
        self.due_soon_btn.setObjectName("PillDueSoon")
        self.due_soon_btn.setCheckable(True)
        # Prevent button from being triggered by Return key
        self.due_soon_btn.setAutoDefault(False)
        self.due_soon_btn.setDefault(False)
        self.due_soon_btn.setCursor(Qt.PointingHandCursor)
        self.due_soon_btn.clicked.connect(self.dueSoonClicked.emit)  # type: ignore

        pills_layout.addWidget(self.overdue_btn)
        pills_layout.addWidget(self.due_soon_btn)

        self.overdue_btn.setText("…")
        self.due_soon_btn.setText("…")

        # Default look keeps native QGroupBox styling; no extra theme plumbing needed.

    def retheme(self) -> None:
        """No-op: native widgets already pick up theme automatically."""

    def load_first_overdue_by_module(self, module) -> None:
        if IS_LOADING:
            return

        # log_debug(f"[OverdueDueSoonPillsWidget] Refreshing counts for module: {module.value.capitalize() + 's'}")

        IS_LOADING = True

        def apply(overdue_total, due_soon_total):
            self.set_counts(overdue_total, due_soon_total)
            IS_LOADING = False

        overdue_total, due_soon_total = OverdueDueSoonPillsUtils.refresh_counts_for_module(module)
        
        QTimer.singleShot(0, lambda: apply(overdue_total, due_soon_total))

    def set_counts(self, overdue: int, due_soon: int) -> None:
        """Update this widget's pill labels with counts."""
        self.overdue_btn.setText(str(overdue))
        self.due_soon_btn.setText(str(due_soon))


    # --- Active state management ---
    def set_overdue_active(self, active: bool) -> None:
        global OVERDUE_ACTIVE
        OVERDUE_ACTIVE = active
        self._overdue_active = active
        if self.overdue_btn:
            self.overdue_btn.setChecked(active)

    def set_due_soon_active(self, active: bool) -> None:
        global DUE_SOON_ACTIVE
        DUE_SOON_ACTIVE = active
        self._due_soon_active = active
        if self.due_soon_btn:
            self.due_soon_btn.setChecked(active)


class UIControllers:

    @staticmethod
    def build_query(module) -> str:
        base_name = module.value
        capitalized_name = base_name.capitalize() + "s"
        plural_name = base_name + "s"
        # avoid f-strings with literal braces - build with .format / concatenation
        q = "query {}Count($first:Int,$where: Query{}WhereWhereConditions)".format(capitalized_name, capitalized_name)
        query = (
            q + " { " + plural_name + "(first:$first, where:$where){ pageInfo{ total } edges{ node { id } } } }"
        )
        return query


    @staticmethod
    def try_fetch(module, where_obj: Dict[str, Any]) -> Optional[int]:
        try:
            api = APIClient()
        except Exception:
            OverdueDueSoonPillsWidget._is_loading = False
            return

        plural_name = module.value + "s"
        try:
            query = UIControllers.build_query(module)
            data = api.send_query(query, {"first": 1, "where": where_obj}, return_raw=True) or {}
            page = JsonResponseHandler.get_page_info_from_path(data, [plural_name])
            total = page.get("total")
            if isinstance(total, int):
                return total
        except Exception:
            pass
        return None



class OverdueDueSoonPillsLogic:
    """
    Handles the logic and state management for the OverdueDueSoonPillsWidget.
    """
    @staticmethod
    def set_counts(overdue_values, btn1, btn2):
        btn1.setText(str(overdue_values[0]))
        btn2.setText(str(overdue_values[1]))


class OverdueDueSoonPillsUtils:
    """
    Contains shared utility functions for the OverdueDueSoonPillsWidget.
    """

    _due_at_column = "DUE_AT"
    _days_due_soon = 3

    @staticmethod
    def _normalize_and_list(base_query):
        """Return a well-formed AND list from optional base_query.
        Accepts list[dict], dict, or None. Any other type returns empty list.
        This avoids accidental list(str) behavior producing per-character entries.
        """
        if base_query is None:
            return []
        if isinstance(base_query, list):
            # Copy to avoid mutating caller's list
            return [x for x in base_query if isinstance(x, dict)]
        if isinstance(base_query, dict):
            return [base_query]
        # Unknown type; ignore to keep schema valid
        return []

    @staticmethod
    def build_overdue_where(base_query=None):
        today = datetime.now().date().isoformat()
        and_list = OverdueDueSoonPillsUtils._normalize_and_list(base_query)
        and_list.append({"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "LT", "value": today})
        return {"AND": and_list}

    @staticmethod
    def build_due_soon_where(base_query=None, days=None):
        # Keep backward compatibility: if callers pass ("DUE_AT", 3) we'll ignore the string
        # and use provided days to override the default window.
        today = datetime.now().date().isoformat()
        days_window = days if isinstance(days, int) and days > 0 else OverdueDueSoonPillsUtils._days_due_soon
        soon = (datetime.now().date() + timedelta(days=days_window)).isoformat()
        and_list = OverdueDueSoonPillsUtils._normalize_and_list(base_query)
        and_list.extend([
            {"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "GTE", "value": today},
            {"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "LTE", "value": soon},
        ])
        return {"AND": and_list}

    @staticmethod
    def refresh_counts_for_module(module):
        api_client = APIClient()
        today = datetime.now().date()
        soon = today + timedelta(days=OverdueDueSoonPillsUtils._days_due_soon)
        today_s = today.isoformat()
        soon_s = soon.isoformat()

        base_name = module.value
        capitalized_name = base_name.capitalize() + "s"
        plural_name = base_name + "s"
        q = f"query {capitalized_name}Count($first:Int,$where: Query{capitalized_name}WhereWhereConditions)"
        query = (
            q + " { " + plural_name + "(first:$first, where:$where){ pageInfo{ total } edges{ node { id } } } }"
        )

        def try_fetch(where_obj):
            try:
                data = api_client.send_query(query, {"first": 1, "where": where_obj}, return_raw=True) or {}
                page = JsonResponseHandler.get_page_info_from_path(data, [plural_name])
                total = page.get("total")
                if isinstance(total, int):
                    return total
            except Exception:
                pass
            return None

        overdue_total = try_fetch({"AND": [{"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "LT", "value": today_s}]})
        due_soon_total = try_fetch({"AND": [
            {"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "GTE", "value": today_s},
            {"column": OverdueDueSoonPillsUtils._due_at_column, "operator": "LTE", "value": soon_s}
        ]})

        overdue_total = overdue_total or 0
        due_soon_total = due_soon_total or 0

        return (overdue_total, due_soon_total)


class OverdueDueSoonPillsActionHelper:
    """Shared actions for applying overdue/due-soon filters across modules."""

    @staticmethod
    def apply_due_filter(module, *, is_overdue: bool, base_query=None, days: Optional[int] = None) -> None:
        feed_logic = getattr(module, "feed_logic", None)
        if feed_logic is None:
            feed_cls = getattr(module, "FEED_LOGIC_CLS", None)
            module_key = getattr(module, "module_key", None)
            query_file = getattr(module, "QUERY_FILE", None)
            lang_manager = getattr(module, "lang_manager", None)
            if feed_cls is None or module_key is None or query_file is None:
                return
            module.feed_logic = feed_cls(module_key, query_file, lang_manager)
            feed_logic = module.feed_logic

        where = (
            OverdueDueSoonPillsUtils.build_overdue_where(base_query)
            if is_overdue
            else OverdueDueSoonPillsUtils.build_due_soon_where(base_query, days=days)
        )

        tags_filter = getattr(module, "tags_filter", None)
        tags_ids = FilterHelper.selected_ids(tags_filter) if tags_filter else []
        build_has_tags = getattr(module, "_build_has_tags_condition", None)
        if callable(build_has_tags):
            has_tags_filter = build_has_tags(tags_ids)
        else:
            default_mode = getattr(module, "tags_match_mode", None)
            has_tags_filter = FilterHelper.build_has_tags_condition(
                tags_ids, match_mode=default_mode
            )

        feed_load_engine = getattr(module, "feed_load_engine", None)
        if feed_load_engine is not None and getattr(feed_load_engine, "buffer", None) is not None:
            feed_load_engine.buffer.clear()

        feed_logic.set_where(where if where and where.get("AND") else None)
        if has_tags_filter is not None:
            feed_logic.set_extra_arguments(hasTags=has_tags_filter)

        feed_layout = getattr(module, "feed_layout", None)
        empty_state = getattr(module, "_empty_state", None)
        if hasattr(module, "clear_feed"):
            module.clear_feed(feed_layout, empty_state)

        scroll_area = getattr(module, "scroll_area", None)
        if scroll_area is not None and scroll_area.verticalScrollBar() is not None:
            scroll_area.verticalScrollBar().setValue(0)

        if feed_load_engine is not None:
            feed_load_engine.schedule_load()

    @staticmethod
    def set_active_pill_states(pills_widget, *, is_overdue: bool) -> None:
        if pills_widget is None:
            return
        pills_widget.set_overdue_active(is_overdue)
        pills_widget.set_due_soon_active(not is_overdue)

    @staticmethod
    def refresh_counts(pills_widget, module_enum) -> None:
        if pills_widget is None or module_enum is None:
            return
        overdue_total, due_soon_total = OverdueDueSoonPillsUtils.refresh_counts_for_module(module_enum)
        pills_widget.set_counts(overdue_total, due_soon_total)


class OverduePillsMixin:
    """Mixin to wire overdue/due-soon pills with unified handling."""

    def wire_overdue_pills(self, parent_container=None) -> None:
        self.overdue_pills = OverdueDueSoonPillsWidget()
        self.overdue_pills.overdueClicked.connect(lambda: self._on_due_pill_clicked(True))
        self.overdue_pills.dueSoonClicked.connect(lambda: self._on_due_pill_clicked(False))

        target = parent_container or getattr(self, "toolbar_area", None)
        if target is not None:
            if hasattr(target, "add_right"):
                target.add_right(self.overdue_pills)
            elif hasattr(target, "addWidget"):
                target.addWidget(self.overdue_pills)

    def _on_due_pill_clicked(self, is_overdue: bool) -> None:
        OverdueDueSoonPillsActionHelper.set_active_pill_states(self.overdue_pills, is_overdue=is_overdue)
        OverdueDueSoonPillsActionHelper.apply_due_filter(self, is_overdue=is_overdue)

    def refresh_overdue_counts(self, module_enum) -> None:
        OverdueDueSoonPillsActionHelper.refresh_counts(getattr(self, "overdue_pills", None), module_enum)

