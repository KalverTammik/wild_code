from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..constants.button_props import ButtonSize, ButtonVariant
from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from .theme_manager import ThemeManager


class PropertyArchivePlanDialog(QDialog):
    """Read-only review of missing-property actions before they are applied."""

    def __init__(self, *, scope, candidates: list[dict], parent=None, lang_manager=None):
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self.setWindowTitle(self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_TITLE))
        self.setModal(True)
        self.resize(900, 480)
        self.setMinimumSize(720, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        scope_text = self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_SCOPE).format(
            county=scope.county,
            municipality=scope.municipality,
            settlements=", ".join(scope.settlements),
        )
        scope_label = QLabel(scope_text, self)
        scope_label.setObjectName("FilterTitle")
        scope_label.setWordWrap(True)
        layout.addWidget(scope_label)

        intro = QLabel(
            self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_INTRO).format(
                count=len(candidates),
            ),
            self,
        )
        intro.setWordWrap(True)
        intro.setObjectName("SelectionInfo")
        layout.addWidget(intro)

        table = QTableWidget(len(candidates), 5, self)
        table.setObjectName("PropertyArchivePlanTable")
        table.setHorizontalHeaderLabels(
            [
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_TUNNUS),
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_SETTLEMENT),
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_MAP),
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_BACKEND),
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_COLUMN_NOTE),
            ]
        )
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)

        for row, candidate in enumerate(candidates):
            values = (
                candidate.get("tunnus") or "",
                candidate.get("settlement") or "",
                self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_MAP_MOVE),
                candidate.get("backend_label") or "",
                candidate.get("note") or "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(int(Qt.AlignLeft | Qt.AlignVCenter))
                table.setItem(row, column, item)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        table.resizeRowsToContents()
        layout.addWidget(table, 1)

        completeness_checkbox = QCheckBox(
            self._lang.translate(
                TranslationKeys.PROPERTY_ARCHIVE_PLAN_COMPLETENESS_CONFIRM
            ),
            self,
        )
        layout.addWidget(completeness_checkbox)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton(
            self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_CANCEL), self
        )
        cancel_button.setProperty("variant", ButtonVariant.GHOST)
        cancel_button.setProperty("btnSize", ButtonSize.SMALL)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)

        confirm_button = QPushButton(
            self._lang.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_CONFIRM), self
        )
        confirm_button.setObjectName("ConfirmButton")
        confirm_button.setProperty("variant", ButtonVariant.SUCCESS)
        confirm_button.clicked.connect(self.accept)
        confirm_button.setDefault(True)
        confirm_button.setEnabled(False)
        completeness_checkbox.toggled.connect(confirm_button.setEnabled)
        buttons.addWidget(confirm_button)
        layout.addLayout(buttons)

        ThemeManager.apply_app_style(self, [QssPaths.MAIN, QssPaths.BUTTONS])

    @classmethod
    def confirm(cls, *, scope, candidates: list[dict], parent=None, lang_manager=None) -> bool:
        dialog = cls(
            scope=scope,
            candidates=candidates,
            parent=parent,
            lang_manager=lang_manager,
        )
        return dialog.exec_() == QDialog.Accepted
