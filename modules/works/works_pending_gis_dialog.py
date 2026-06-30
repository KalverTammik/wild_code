from __future__ import annotations

from typing import Callable, Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager


class WorksPendingGisDialog(QDialog):
    def __init__(
        self,
        *,
        rows: Iterable[dict[str, object]],
        on_open: Callable[[int, QDialog], bool],
        lang_manager=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._rows = list(rows or [])
        self._on_open = on_open
        self._table: QTableWidget | None = None

        self.setModal(True)
        self.setObjectName("WorksPendingGisDialog")
        self.setWindowTitle(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE))
        self.resize(820, 460)

        self._build_ui()
        self._populate_rows()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE), self)
        title.setObjectName("ExtraInfoDialogTitle")
        root.addWidget(title)

        intro = QLabel(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_INTRO), self)
        intro.setWordWrap(True)
        root.addWidget(intro)

        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(
            [
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_COL_ID),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_COL_TITLE),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_COL_TYPE),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_COL_STATUS),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_COL_UPDATED),
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.itemDoubleClicked.connect(lambda *_: self._open_selected())
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        root.addWidget(self._table, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        cancel_btn = QPushButton(self._lang.translate(TranslationKeys.CANCEL_BUTTON), self)
        cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        open_btn = QPushButton(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_OPEN_SELECTED), self)
        open_btn.setProperty("variant", ButtonVariant.PRIMARY)
        open_btn.clicked.connect(self._open_selected)
        buttons.addWidget(open_btn)

        for button in (cancel_btn, open_btn):
            button.setAutoDefault(False)
            button.setDefault(False)

        root.addLayout(buttons)

    def _populate_rows(self) -> None:
        if self._table is None:
            return

        self._table.setRowCount(len(self._rows))
        for row_index, payload in enumerate(self._rows):
            feature_id = int(payload.get("feature_id") or 0)
            values = (
                str(feature_id),
                str(payload.get("title") or ""),
                str(payload.get("type_label") or payload.get("type_id") or ""),
                str(payload.get("status_label") or payload.get("status_id") or ""),
                str(payload.get("updated_at") or ""),
            )
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if column_index == 0:
                    item.setData(Qt.UserRole, feature_id)
                self._table.setItem(row_index, column_index, item)

        if self._rows:
            self._table.selectRow(0)

    def _open_selected(self) -> None:
        if self._table is None:
            return
        row = self._table.currentRow()
        if row < 0:
            return

        item = self._table.item(row, 0)
        if item is None:
            return

        feature_id = item.data(Qt.UserRole)
        try:
            feature_id_int = int(feature_id)
        except (TypeError, ValueError):
            return

        if self._on_open(feature_id_int, self):
            self.accept()
