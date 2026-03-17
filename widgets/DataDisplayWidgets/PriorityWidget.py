from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors


class PriorityWidget(QWidget):
    _PALETTE = {
        "URGENT": {
            "bg": (254, 226, 226),
            "fg": (153, 27, 27),
            "border": (239, 68, 68),
        },
        "HIGH": {
            "bg": (255, 237, 213),
            "fg": (154, 52, 18),
            "border": (249, 115, 22),
        },
        "MEDIUM": {
            "bg": (254, 249, 195),
            "fg": (133, 77, 14),
            "border": (234, 179, 8),
        },
        "LOW": {
            "bg": (220, 252, 231),
            "fg": (22, 101, 52),
            "border": (34, 197, 94),
        },
    }
    _DEFAULT_PALETTE = {
        "bg": (229, 231, 235),
        "fg": (55, 65, 81),
        "border": (156, 163, 175),
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
        row.addWidget(self.priority_label, 0, Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addLayout(row)

        resolved_priority = str(priority or DataDisplayExtractors.extract_priority(item_data) or "").strip().upper()
        self.set_priority(resolved_priority)

    def set_priority(self, priority: str) -> None:
        normalized = str(priority or "").strip().upper()
        if not normalized:
            self.setVisible(False)
            return

        palette = self._PALETTE.get(normalized, self._DEFAULT_PALETTE)
        label_text = APIModuleActions.task_priority_label(normalized, lang_manager=self._lang)
        self.priority_label.setText(label_text)
        self.priority_label.setToolTip(
            f"{self._lang.translate(TranslationKeys.WORKS_CREATE_PRIORITY_LABEL)}: {label_text}"
        )
        self.priority_label.setStyleSheet(
            "QLabel#PriorityLabel {"
            f"background-color: rgb({palette['bg'][0]},{palette['bg'][1]},{palette['bg'][2]});"
            f"color: rgb({palette['fg'][0]},{palette['fg'][1]},{palette['fg'][2]});"
            f"border: 1px solid rgb({palette['border'][0]},{palette['border'][1]},{palette['border'][2]});"
            "border-radius: 6px;"
            "padding: 2px 8px;"
            "font-weight: 600;"
            "font-size: 10px;"
            "}"
        )
        text_width = self.priority_label.fontMetrics().horizontalAdvance(label_text)
        self.priority_label.setFixedWidth(max(56, min(104, text_width + 20)))
        self.setVisible(True)