from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors


class PriorityWidget(QWidget):
    _ICON_NAMES = {
        "URGENT": IconNames.PRIORITY_URGENT,
        "HIGH": IconNames.PRIORITY_HIGH,
        "MEDIUM": IconNames.PRIORITY_MEDIUM,
        "LOW": IconNames.PRIORITY_LOW,
    }

    def __init__(
        self,
        item_data=None,
        *,
        priority: Optional[str] = None,
        parent=None,
        lang_manager=None,
    ):
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(1)

        self.priority_label = QLabel(self)
        self.priority_label.setObjectName("PriorityLabel")
        self.priority_label.setAlignment(Qt.AlignCenter)
        self.priority_label.setScaledContents(False)
        row.addWidget(self.priority_label, 0, Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addLayout(row)

        resolved_priority = str(priority or DataDisplayExtractors.extract_priority(item_data) or "").strip().upper()
        self.set_priority(resolved_priority)

    def set_priority(self, priority: str) -> None:
        normalized = str(priority or "").strip().upper()
        if not normalized:
            self.setVisible(False)
            return

        label_text = APIModuleActions.task_priority_label(normalized, lang_manager=self._lang)
        self.priority_label.setToolTip(
            f"{self._lang.translate(TranslationKeys.WORKS_CREATE_PRIORITY_LABEL)}: {label_text}"
        )
        icon_path = IconNames.get_icon(self._ICON_NAMES.get(normalized, IconNames.PRIORITY_MEDIUM))
        icon_pixmap = QPixmap(icon_path)
        if not icon_pixmap.isNull():
            self.priority_label.setPixmap(
                icon_pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.priority_label.clear()
        self.priority_label.setFixedSize(16, 16)
        self.setVisible(True)