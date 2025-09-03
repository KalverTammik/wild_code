"""Overdue / Due Soon pills widget.

Provides two pill buttons inside a small group box plus logic to fetch counts
using two minimal GraphQL queries (first:1) that rely only on pageInfo.total.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QGroupBox, QVBoxLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..utils.api_client import APIClient


class OverdueDueSoonPillsWidget(QWidget):
    # Emitted when user clicks pills (container will handle applying filters)
    overdueClicked = pyqtSignal()
    dueSoonClicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("OverdueDueSoonPillsWidget")
        self._is_loading = False
        self._resolved_due_column: Optional[str] = None  # column variant that worked for counts
        self._days_due_soon: int = 3
        self._overdue_active = False
        self._due_soon_active = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(2)

        self.group = QGroupBox("Urgent!", self)
        self.group.setObjectName("UrgentGroupBox")
        self.group.setToolTip("What needs fast attention")

        shadow = QGraphicsDropShadowEffect(self.group)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(Qt.gray)
        self.group.setGraphicsEffect(shadow)

        pills_layout = QHBoxLayout()
        pills_layout.setContentsMargins(2, 1, 2, 1)
        pills_layout.setSpacing(2)
        self.group.setLayout(pills_layout)
        outer.addWidget(self.group)

        self.overdue_btn = QPushButton("0", self.group)
        self.overdue_btn.setObjectName("PillOverdue")
        # Prevent button from being triggered by Return key
        self.overdue_btn.setAutoDefault(False)
        self.overdue_btn.setDefault(False)
        self.overdue_btn.setCursor(Qt.PointingHandCursor)
        self.overdue_btn.clicked.connect(self.overdueClicked.emit)  # type: ignore

        self.due_soon_btn = QPushButton("0", self.group)
        self.due_soon_btn.setObjectName("PillDueSoon")
        # Prevent button from being triggered by Return key
        self.due_soon_btn.setAutoDefault(False)
        self.due_soon_btn.setDefault(False)
        self.due_soon_btn.setCursor(Qt.PointingHandCursor)
        self.due_soon_btn.clicked.connect(self.dueSoonClicked.emit)  # type: ignore

        pills_layout.addWidget(self.overdue_btn)
        pills_layout.addWidget(self.due_soon_btn)

        # Apply initial styles based on current theme
        try:
            from ..widgets.theme_manager import ThemeManager
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
            if theme == "dark":
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_counts(self, overdue: int, due_soon: int) -> None:
        try:
            self.overdue_btn.setText(str(overdue))
            self.due_soon_btn.setText(str(due_soon))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------
    def refresh_counts_for_projects(self, lang_manager=None, days_due_soon: int = 3) -> None:
        if self._is_loading:
            return
        self._is_loading = True
        self._days_due_soon = days_due_soon
        try:
            self.overdue_btn.setText("…")
            self.due_soon_btn.setText("…")
        except Exception:
            pass
        try:
            api = APIClient(lang_manager)
        except Exception:
            self._is_loading = False
            return

        today = datetime.utcnow().date()
        soon = today + timedelta(days=days_due_soon)
        today_s = today.isoformat()
        soon_s = soon.isoformat()

        query = (
            "query ProjectsCount($first:Int,$where: QueryProjectsWhereWhereConditions){"
            " projects(first:$first, where:$where){ pageInfo{ total } edges{ node { id } } } }"
        )

        def try_fetch(where_obj: Dict[str, Any]) -> Optional[int]:
            try:
                data = api.send_query(query, {"first": 1, "where": where_obj}) or {}
                root = data.get("projects") or {}
                page = root.get("pageInfo") or {}
                total = page.get("total")
                if isinstance(total, int):
                    return total
            except Exception:
                pass
            return None

        column_candidates: List[str] = ["DUE_AT", "dueAt", "DUEAT"]
        lt_ops = ["LT", "lt"]
        gte_ops = ["GTE", "gte"]
        lte_ops = ["LTE", "lte"]

        overdue_total: Optional[int] = None
        due_soon_total: Optional[int] = None

        for col in column_candidates:
            if overdue_total is not None:
                break
            for op in lt_ops:
                where = {"AND": [{"column": col, "operator": op, "value": today_s}]}
                overdue_total = try_fetch(where)
                if overdue_total is not None:
                    self._resolved_due_column = col
                    break

        for col in column_candidates:
            if due_soon_total is not None:
                break
            for gte in gte_ops:
                if due_soon_total is not None:
                    break
                for lte in lte_ops:
                    where = {"AND": [
                        {"column": col, "operator": gte, "value": today_s},
                        {"column": col, "operator": lte, "value": soon_s},
                    ]}
                    due_soon_total = try_fetch(where)
                    if due_soon_total is not None:
                        if not self._resolved_due_column:
                            self._resolved_due_column = col
                        break

        if overdue_total is None:
            overdue_total = 0
        if due_soon_total is None:
            due_soon_total = 0

        def apply():
            self.set_counts(overdue_total or 0, due_soon_total or 0)
            self._is_loading = False

        QTimer.singleShot(0, apply)

    # Helpers consumed by module UIs
    def resolved_due_column(self) -> Optional[str]:
        return self._resolved_due_column

    def build_overdue_where(self, base_and: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        col = self._resolved_due_column or "DUE_AT"
        today = datetime.utcnow().date().isoformat()
        and_list: List[Dict[str, Any]] = list(base_and) if base_and else []
        and_list.append({"column": col, "operator": "LT", "value": today})
        return {"AND": and_list}

    def build_due_soon_where(self, base_and: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        col = self._resolved_due_column or "DUE_AT"
        today = datetime.utcnow().date()
        soon = today + timedelta(days=self._days_due_soon)
        and_list: List[Dict[str, Any]] = list(base_and) if base_and else []
        and_list.extend([
            {"column": col, "operator": "GTE", "value": today.isoformat()},
            {"column": col, "operator": "LTE", "value": soon.isoformat()},
        ])
        return {"AND": and_list}

    # --- Active state management ---
    def set_overdue_active(self, active: bool) -> None:
        self._overdue_active = active
        self._update_button_style(self.overdue_btn, active, is_overdue=True)

    def set_due_soon_active(self, active: bool) -> None:
        self._due_soon_active = active
        self._update_button_style(self.due_soon_btn, active, is_overdue=False)

    def _update_button_style(self, btn: QPushButton, active: bool, is_overdue: bool) -> None:
        try:
            from ..widgets.theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
        except Exception:
            theme = "light"

        if theme == "dark":
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

