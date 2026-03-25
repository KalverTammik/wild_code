from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
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
from ...python.api_actions import APIModuleActions
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ..DateHelpers import DateHelpers
from ..theme_manager import ThemeManager
from .TaskFilePreviewDialog import TaskFilePreviewDialog


class TaskFilesDialog(QDialog):
    def __init__(
        self,
        *,
        item_id: str,
        item_name: str = "",
        module_name: str = Module.TASK.value,
        lang_manager=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item_id = str(item_id or "").strip()
        self._item_name = str(item_name or "").strip()
        self._module_name = str(module_name or Module.TASK.value).strip().lower() or Module.TASK.value
        self._files: list[dict] = []

        self.setModal(True)
        self.setObjectName("TaskFilesDialog")
        self.setMinimumWidth(860)
        self.setMinimumHeight(420)
        self.setWindowTitle(
            self._lang.translate(TranslationKeys.TASK_FILES_DIALOG_TITLE).format(
                name=self._item_name or self._item_id
            )
        )

        ThemeManager.apply_module_style(
            self,
            [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_CARD, QssPaths.MESSAGE_BOX],
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self._count_label = QLabel(self)
        self._count_label.setObjectName("TaskFilesCountLabel")
        layout.addWidget(self._count_label)

        self._table = QTableWidget(0, 5, self)
        self._table.setObjectName("TaskFilesTable")
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.setHorizontalHeaderLabels(
            [
                self._lang.translate(TranslationKeys.TASK_FILES_COLUMN_NAME),
                self._lang.translate(TranslationKeys.TASK_FILES_COLUMN_SIZE),
                self._lang.translate(TranslationKeys.TASK_FILES_COLUMN_TYPE),
                self._lang.translate(TranslationKeys.TASK_FILES_COLUMN_UPLOADER),
                self._lang.translate(TranslationKeys.TASK_FILES_COLUMN_CREATED),
            ]
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._update_button_states)
        self._table.itemDoubleClicked.connect(lambda *_: self._preview_selected())
        layout.addWidget(self._table, 1)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)

        self._refresh_button = QPushButton(self._lang.translate(TranslationKeys.TASK_FILES_REFRESH), self)
        self._refresh_button.setProperty("variant", ButtonVariant.GHOST)
        self._refresh_button.clicked.connect(self._load_files)
        button_row.addWidget(self._refresh_button)

        self._upload_button = QPushButton(self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD), self)
        self._upload_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._upload_button.clicked.connect(self._upload_files)
        button_row.addWidget(self._upload_button)

        self._open_button = QPushButton(self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW), self)
        self._open_button.setProperty("variant", ButtonVariant.GHOST)
        self._open_button.clicked.connect(self._preview_selected)
        button_row.addWidget(self._open_button)

        self._delete_button = QPushButton(self._lang.translate(TranslationKeys.TASK_FILES_DELETE), self)
        self._delete_button.setProperty("variant", ButtonVariant.GHOST)
        self._delete_button.clicked.connect(self._delete_selected)
        button_row.addWidget(self._delete_button)

        button_row.addStretch(1)

        close_button = QPushButton(self._lang.translate(TranslationKeys.CLOSE), self)
        close_button.setProperty("variant", ButtonVariant.GHOST)
        close_button.clicked.connect(self.accept)
        button_row.addWidget(close_button)

        layout.addLayout(button_row)
        self._update_button_states()
        self._load_files()

    def _run_with_busy_cursor(self, callback):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            return callback()
        finally:
            QApplication.restoreOverrideCursor()

    def _load_files(self) -> None:
        files = self._run_with_busy_cursor(
            lambda: APIModuleActions.get_module_files(self._module_name, self._item_id)
        )
        if files is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.TASK_FILES_LOAD_FAILED).format(
                    name=self._item_name or self._item_id
                ),
            )
            return

        self._files = list(files)
        self._populate_table()
        self._update_button_states()

    def _populate_table(self) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        locale = QLocale.system()
        for file_info in self._files:
            row = self._table.rowCount()
            self._table.insertRow(row)

            name = str(file_info.get("fileName") or file_info.get("uuid") or "-")
            size = str(file_info.get("humanReadableSize") or "").strip() or self._fallback_size(file_info.get("size"))
            mime_type = str(file_info.get("mimeType") or file_info.get("ext") or "-")
            uploader = APIModuleActions.user_display_name(file_info.get("uploader")) or "–"
            created = self._format_created_at(file_info.get("createdAt"), locale)

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, dict(file_info))
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, QTableWidgetItem(size))
            self._table.setItem(row, 2, QTableWidgetItem(mime_type))
            self._table.setItem(row, 3, QTableWidgetItem(uploader))
            self._table.setItem(row, 4, QTableWidgetItem(created))

        count = len(self._files)
        if count <= 0:
            self._count_label.setText(self._lang.translate(TranslationKeys.TASK_FILES_EMPTY))
        else:
            self._count_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_COUNT).format(count=count)
            )
        self._table.setSortingEnabled(True)
        self._table.sortItems(4, Qt.DescendingOrder)

    @staticmethod
    def _fallback_size(raw_size) -> str:
        try:
            size = int(raw_size)
        except (TypeError, ValueError):
            return "–"
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def _format_created_at(value, locale: QLocale) -> str:
        parsed = DateHelpers.parse_iso(str(value or "").strip())
        if parsed is None:
            return "–"
        try:
            return locale.toString(parsed, QLocale.ShortFormat)
        except Exception:
            return parsed.strftime("%Y-%m-%d %H:%M")

    def _selected_file(self) -> Optional[dict]:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self._table.item(row, 0)
        if item is None:
            return None

        payload = item.data(Qt.UserRole)
        return dict(payload or {}) if isinstance(payload, dict) else None

    def _update_button_states(self) -> None:
        has_selection = self._selected_file() is not None
        self._open_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _require_selected_file(self) -> Optional[dict]:
        file_info = self._selected_file()
        if file_info is not None:
            return file_info

        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.WARNING),
            self._lang.translate(TranslationKeys.TASK_FILES_NO_SELECTION),
        )
        return None

    def _preview_selected(self) -> None:
        file_info = self._require_selected_file()
        if file_info is None:
            return

        file_uuid = str(file_info.get("uuid") or "").strip()
        if not file_uuid:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name_from_info(file_info)
                ),
            )
            return

        dialog = TaskFilePreviewDialog(
            file_info=file_info,
            lang_manager=self._lang,
            parent=self,
        )
        dialog.exec_()

    @staticmethod
    def _file_name_from_info(file_info: Optional[dict]) -> str:
        data = file_info if isinstance(file_info, dict) else {}
        return str(data.get("fileName") or data.get("uuid") or "-")

    def _upload_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_DIALOG_TITLE),
            "",
            self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_DIALOG_FILTER),
        )
        if not paths:
            return

        uploaded_names: list[str] = []
        failed_names: list[str] = []

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            for path in paths:
                normalized_path = str(path or "").strip()
                if not normalized_path:
                    continue
                uploaded = APIModuleActions.upload_module_file(self._module_name, self._item_id, normalized_path)
                target_name = os.path.basename(normalized_path) or normalized_path
                if isinstance(uploaded, dict) and str(uploaded.get("uuid") or "").strip():
                    uploaded_names.append(target_name)
                else:
                    failed_names.append(target_name)
                QApplication.processEvents()
        finally:
            QApplication.restoreOverrideCursor()

        if uploaded_names:
            self._load_files()

        if uploaded_names and not failed_names:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.SUCCESS),
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_SUCCESS).format(
                    count=len(uploaded_names)
                ),
            )
            return

        if uploaded_names and failed_names:
            failed_preview = ", ".join(failed_names[:5])
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_PARTIAL).format(
                    uploaded=len(uploaded_names),
                    failed=len(failed_names),
                    failed_preview=failed_preview,
                ),
            )
            return

        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_FAILED),
        )

    def _delete_selected(self) -> None:
        file_info = self._require_selected_file()
        if file_info is None:
            return

        file_uuid = str(file_info.get("uuid") or "").strip()
        file_name = str(file_info.get("fileName") or file_uuid or "-")
        if not file_uuid:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.TASK_FILES_DELETE_FAILED).format(name=file_name),
            )
            return

        confirmed = ModernMessageDialog.ask_yes_no(
            self._lang.translate(TranslationKeys.TASK_FILES_DELETE_CONFIRM_TITLE),
            self._lang.translate(TranslationKeys.TASK_FILES_DELETE_CONFIRM_MESSAGE).format(name=file_name),
            yes_label=self._lang.translate(TranslationKeys.DELETE),
            no_label=self._lang.translate(TranslationKeys.CANCEL_BUTTON),
            default=self._lang.translate(TranslationKeys.CANCEL_BUTTON),
        )
        if not confirmed:
            return

        deleted = self._run_with_busy_cursor(
            lambda: APIModuleActions.delete_file(file_uuid)
        )
        if not isinstance(deleted, dict):
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.TASK_FILES_DELETE_FAILED).format(name=file_name),
            )
            return

        self._load_files()
        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.TASK_FILES_DELETE_SUCCESS).format(name=file_name),
        )
