"""Overdue / Due Soon pills widget.

Provides two pill buttons inside a small group box plus logic to fetch counts
using two minimal GraphQL queries (first:1) that rely only on pageInfo.total.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QGroupBox, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..python.api_client import APIClient
from ..python.responses import JsonResponseHandler
from ..languages.language_manager import LanguageManager
from datetime import datetime, timedelta
from ..widgets.theme_manager import ThemeManager, Theme, is_dark, IntensityLevels, styleExtras, ThemeShadowColors
# from ..utils.logger import debug as log_debug

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
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.group = QGroupBox(self._lang.translate("urgent_group_title"), self)
        self.group.setObjectName("UrgentGroupBox")
        self.group.setToolTip(self._lang.translate("urgent_tooltip"))

        shadow_color = ThemeShadowColors.BLUE
        styleExtras.apply_chip_shadow(
            element=self.group, 
            color=shadow_color, 
            blur_radius=16, 
            x_offset=2, 
            y_offset=2, 
            alpha_level=IntensityLevels.MEDIUM
            )

        pills_layout = QHBoxLayout()
        pills_layout.setContentsMargins(2, 1, 2, 1)
        pills_layout.setSpacing(2)
        self.group.setLayout(pills_layout)
        layout.addWidget(self.group)

        self.overdue_btn = QPushButton(self.group)
        self.overdue_btn.setObjectName("PillOverdue")
        # Prevent button from being triggered by Return key
        self.overdue_btn.setAutoDefault(False)
        self.overdue_btn.setDefault(False)
        self.overdue_btn.setCursor(Qt.PointingHandCursor)
        self.overdue_btn.clicked.connect(self.overdueClicked.emit)  # type: ignore

        self.due_soon_btn = QPushButton(self.group)
        self.due_soon_btn.setObjectName("PillDueSoon")
        # Prevent button from being triggered by Return key
        self.due_soon_btn.setAutoDefault(False)
        self.due_soon_btn.setDefault(False)
        self.due_soon_btn.setCursor(Qt.PointingHandCursor)
        self.due_soon_btn.clicked.connect(self.dueSoonClicked.emit)  # type: ignore

        pills_layout.addWidget(self.overdue_btn)
        pills_layout.addWidget(self.due_soon_btn)

        self.overdue_btn.setText("…")
        self.due_soon_btn.setText("…")

        # Apply initial styles based on current theme
        try:
            initial_theme = ThemeManager.load_theme_setting()
        except Exception:
            initial_theme = "light"
        self._apply_mock_styles(theme=initial_theme)

    def retheme(self) -> None:
        """Reapply styles based on current theme. Called by dialog's theme toggle sweep."""
        try:
            from ..widgets.theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
            self._apply_mock_styles(theme=theme)
            # Re-apply active styles if any
            if self._overdue_active:
                self._update_button_style(self.overdue_btn, True, True)
            if self._due_soon_active:
                self._update_button_style(self.due_soon_btn, True, False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_mock_styles(self, theme: str = "light") -> None:
        try:
            if is_dark(ThemeManager.effective_theme()):
                group_border = "rgba(255,255,255,20)"
                group_bg = "rgba(50,50,50,0.95)"
                title_color = "#ff6b6b"
                overdue_bg = "#b71c1c"
                overdue_hover = "#d32f2f"
                due_soon_bg = "#f57f17"
                due_soon_hover = "#fb8c00"
                due_soon_color = "#fff"
                hover_border = "#ffab40"
                hover_bg = "rgba(80,80,80,0.98)"
            else:
                group_border = "rgba(255,255,255,80)"
                group_bg = "rgba(255,255,255,0.95)"
                title_color = "#c62828"
                overdue_bg = "#c62828"
                overdue_hover = "#e53935"
                due_soon_bg = "#f9a825"
                due_soon_hover = "#fbc02d"
                due_soon_color = "#222"
                hover_border = "#ff7043"
                hover_bg = "rgba(255,235,205,0.98)"

            base_group = (
                f"QGroupBox#UrgentGroupBox {{ border: 1.5px solid {group_border}; border-radius:6px; margin-top:8px; padding-top:8px; background:{group_bg}; }}"
                f"QGroupBox#UrgentGroupBox::title {{ subcontrol-origin: margin; left:2px; padding:0 8px; font-weight:600; font-size:8px; color:{title_color}; }}"
            )
            overdue_style = (
                f"QPushButton#PillOverdue {{ background:{overdue_bg}; color:white; border:none; border-radius:6px; padding:2px 2px; font-weight:600; font-size:10px; min-width:20px;}}"
                f"QPushButton#PillOverdue:hover {{ background:{overdue_hover}; }}"
            )
            due_soon_style = (
                f"QPushButton#PillDueSoon {{ background:{due_soon_bg}; color:{due_soon_color}; border:none; border-radius:6px; padding:2px 2px; font-weight:600; font-size:10px; min-width:20px;}}"
                f"QPushButton#PillDueSoon:hover {{ background:{due_soon_hover}; }}"
            )
            hover_wrap = f"QGroupBox#UrgentGroupBox:hover {{ border:1.5px solid {hover_border}; background:{hover_bg}; }}"
            self.group.setStyleSheet(base_group + overdue_style + due_soon_style + hover_wrap)
        except Exception:
            pass

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

        OVERDUE_ACTIVE = active
        self._update_button_style(self.overdue_btn, active, is_overdue=True)

    def set_due_soon_active(self, active: bool) -> None:
        DUE_SOON_ACTIVE = active
        self._update_button_style(self.due_soon_btn, active, is_overdue=False)

    def _update_button_style(self, btn: QPushButton, active: bool, is_overdue: bool) -> None:
        
        theme = ThemeManager.load_theme_setting()

        if btn is None:
            return

        if is_dark(ThemeManager.effective_theme()):
            base_color = "#b71c1c" if is_overdue else "#f57f17"
            active_color = "#ff5722" if is_overdue else "#ff9800"
            hover_color = "#d32f2f" if is_overdue else "#fb8c00"
            text_color = "white" if is_overdue else "#fff"
            border_color = "#fff"
        else:
            base_color = "#c62828" if is_overdue else "#f9a825"
            active_color = "#ff5722" if is_overdue else "#ff9800"
            hover_color = "#e53935" if is_overdue else "#fbc02d"
            text_color = "white" if is_overdue else "#222"
            border_color = "#fff"

        color = active_color if active else base_color
        border = f"border: 2px solid {border_color};" if active else ""
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 2px 2px;
                font-weight: 600;
                font-size: 10px;
                min-width: 20px;
                {border}
            }}
            QPushButton:hover {{
                background: {hover_color};
            }}
        """)


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

