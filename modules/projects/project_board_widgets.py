from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...constants.module_icons import ModuleIconPaths
from ...widgets.DataDisplayWidgets.MainStatusWidget import MainStatusWidget
from ...constants.file_paths import QssPaths
from ...widgets.theme_manager import ThemeManager, Theme, is_dark


class ProjectBoardItemWidget(QFrame):
    def __init__(self, item_data: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProjectBoardItemWidget")

        payload = item_data if isinstance(item_data, dict) else {"primary": str(item_data or "-")}
        status_payload = self._status_payload(payload)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        if status_payload is not None:
            root.addWidget(MainStatusWidget(status_payload, parent=self), 0)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        primary_label = QLabel(str(payload.get("primary") or "-"), self)
        primary_label.setObjectName("ProjectBoardItemPrimary")
        primary_label.setWordWrap(True)
        primary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(primary_label)

        secondary_text = str(payload.get("secondary") or "").strip()
        if secondary_text:
            secondary_label = QLabel(secondary_text, self)
            secondary_label.setObjectName("ProjectBoardItemSecondary")
            secondary_label.setWordWrap(True)
            secondary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(secondary_label)

        root.addWidget(content, 1)

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])
        for child in self.findChildren(QWidget):
            child_retheme = getattr(child, "retheme", None)
            if callable(child_retheme):
                child_retheme()

    @staticmethod
    def _status_payload(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        status_text = str(payload.get("status") or "").strip()
        if not status_text:
            return None
        return {
            "status": {
                "id": str(payload.get("status_id") or "").strip(),
                "name": status_text,
                "color": str(payload.get("status_color") or "cccccc"),
                "type": str(payload.get("status_type") or "").strip(),
            }
        }


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
        self._accent_color = str(color or "#d0d5dd")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QLabel(str(title or "-"), self)
        title_label.setObjectName("ProjectBoardSectionTitle")
        title_label.setAlignment(Qt.AlignCenter)
        self._title_label = title_label
        layout.addWidget(title_label)

        if not groups:
            empty_label = QLabel(str(empty_text or "-"), self)
            empty_label.setObjectName("ProjectBoardEmptyLabel")
            empty_label.setWordWrap(True)
            empty_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            layout.addWidget(empty_label)
            layout.addStretch(1)
            self.retheme()
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
            group_title.setObjectName("ProjectBoardGroupTitle")
            group_title.setWordWrap(True)
            group_row.addWidget(group_title, 1, Qt.AlignVCenter)
            layout.addLayout(group_row)

            for item_payload in group.get("items") or []:
                layout.addWidget(ProjectBoardItemWidget(item_payload, self))

        layout.addStretch(1)
        self.retheme()

    def _apply_section_theme(self) -> None:
        theme_name = ThemeManager.effective_theme()
        dark_theme = is_dark(theme_name) if theme_name in (Theme.DARK, Theme.LIGHT, Theme.SYSTEM) else False
        background = "#202830" if dark_theme else "#ffffff"
        self.setStyleSheet(
            "QFrame#ProjectBoardSectionWidget {"
            f"border: 1px solid {self._accent_color};"
            "border-radius: 8px;"
            f"background: {background};"
            "}"
        )
        self._title_label.setStyleSheet(f"color: {self._accent_color}; font-weight: 600;")

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])
        self._apply_section_theme()
        for child in self.findChildren(QWidget):
            if child is self:
                continue
            child_retheme = getattr(child, "retheme", None)
            if callable(child_retheme):
                child_retheme()


class ProjectBoardOverviewWidget(QWidget):
    COLUMN_MIN_WIDTH = 280
    COLUMN_SPACING = 12

    def __init__(self, board_data: Optional[dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProjectBoardOverviewWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._column_count = 0

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
            section.setMinimumWidth(self.COLUMN_MIN_WIDTH)
            columns_row.addWidget(section, 1)
            self._column_count += 1

        layout.addLayout(columns_row)

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])
        for child in self.findChildren(QWidget):
            child_retheme = getattr(child, "retheme", None)
            if callable(child_retheme):
                child_retheme()

    def preferred_dialog_width(self) -> int:
        margins = self.layout().contentsMargins() if self.layout() is not None else None
        left_right = (margins.left() + margins.right()) if margins is not None else 0
        column_count = max(1, int(self._column_count or 0))
        content_width = (column_count * self.COLUMN_MIN_WIDTH) + ((column_count - 1) * self.COLUMN_SPACING)
        return content_width + left_right