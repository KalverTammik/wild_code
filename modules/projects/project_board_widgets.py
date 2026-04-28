from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...constants.module_icons import ModuleIconPaths
from ...utils.status_color_helper import StatusColorHelper
from ...widgets.theme_manager import ThemeManager


class ProjectBoardItemWidget(QFrame):
    def __init__(self, item_data: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProjectBoardItemWidget")
        self.setStyleSheet(
            "QFrame#ProjectBoardItemWidget {"
            "border: 1px solid #d9dee7;"
            "border-radius: 6px;"
            "background: #fbfcfe;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        payload = item_data if isinstance(item_data, dict) else {"primary": str(item_data or "-")}

        primary_label = QLabel(str(payload.get("primary") or "-"), self)
        primary_label.setWordWrap(True)
        primary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        primary_label.setStyleSheet("font-weight: 600; color: #243447;")
        layout.addWidget(primary_label)

        secondary_text = str(payload.get("secondary") or "").strip()
        if secondary_text:
            secondary_label = QLabel(secondary_text, self)
            secondary_label.setWordWrap(True)
            secondary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            secondary_label.setStyleSheet("color: #667085; font-size: 11px;")
            layout.addWidget(secondary_label)

        status_text = str(payload.get("status") or "").strip()
        if status_text:
            status_row = QHBoxLayout()
            status_row.setContentsMargins(0, 0, 0, 0)
            status_row.addStretch(1)

            bg, fg, border = StatusColorHelper.upgrade_status_color(
                str(payload.get("status_color") or "cccccc")
            )

            status_badge = QLabel(status_text, self)
            status_badge.setAlignment(Qt.AlignCenter)
            status_badge.setStyleSheet(
                f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
                f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
                f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
                "border-radius: 6px;"
                "padding: 2px 8px;"
                "font-size: 11px;"
                "font-weight: 500;"
            )
            status_row.addWidget(status_badge)
            layout.addLayout(status_row)


class ProjectBoardSectionWidget(QFrame):
    def __init__(
        self,
        *,
        title: str,
        color: str,
        groups: list[dict[str, Any]],
        empty_text: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("ProjectBoardSectionWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(
            "QFrame#ProjectBoardSectionWidget {"
            f"border: 1px solid {color};"
            "border-radius: 8px;"
            "background: #ffffff;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QLabel(str(title or "-"), self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-weight: 600;")
        layout.addWidget(title_label)

        if not groups:
            empty_label = QLabel(str(empty_text or "-"), self)
            empty_label.setWordWrap(True)
            empty_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            empty_label.setStyleSheet("color: #667085;")
            layout.addWidget(empty_label)
            layout.addStretch(1)
            return

        for group in groups:
            group_row = QHBoxLayout()
            group_row.setContentsMargins(0, 0, 0, 0)
            group_row.setSpacing(6)

            module_key = str(group.get("module_key") or "").strip().lower()
            icon_path = ModuleIconPaths.get_module_icon(module_key) if module_key else ""
            if icon_path:
                icon_label = QLabel(self)
                icon_label.setPixmap(ThemeManager.get_qicon(icon_path).pixmap(14, 14))
                group_row.addWidget(icon_label, 0, Qt.AlignVCenter)

            group_title = QLabel(str(group.get("title") or "-"), self)
            group_title.setWordWrap(True)
            group_title.setStyleSheet("font-weight: 600; color: #243447;")
            group_row.addWidget(group_title, 1, Qt.AlignVCenter)
            layout.addLayout(group_row)

            for item_payload in group.get("items") or []:
                layout.addWidget(ProjectBoardItemWidget(item_payload, self))

        layout.addStretch(1)


class ProjectBoardOverviewWidget(QWidget):
    def __init__(self, board_data: Optional[dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProjectBoardOverviewWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        data = board_data if isinstance(board_data, dict) else {}
        columns_row = QHBoxLayout()
        columns_row.setContentsMargins(0, 0, 0, 0)
        columns_row.setSpacing(12)

        columns = data.get("columns") if isinstance(data.get("columns"), list) else []
        for column_data in columns:
            if not isinstance(column_data, dict):
                continue
            section = ProjectBoardSectionWidget(
                title=str(column_data.get("title") or "-"),
                color=str(column_data.get("color") or "#d0d5dd"),
                groups=list(column_data.get("groups") or []),
                empty_text=str(column_data.get("empty_text") or "-"),
                parent=self,
            )
            columns_row.addWidget(section, 1)

        layout.addLayout(columns_row)