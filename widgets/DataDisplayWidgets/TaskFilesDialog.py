from __future__ import annotations

import os
from typing import Optional

from qgis.PyQt.QtCore import QLocale, Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
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
from ...python.workers import FunctionWorker, start_worker
from ...ui.messages_helper import ModernMessageDialog
from ...constants.module_names import Module
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.date_helpers import DateHelpers
from ...ui.theme_manager import ThemeManager
from .TaskFilePreviewDialog import TaskFilePreviewDialog



class _SortableItem(QTableWidgetItem):
    """A cell shown as text but sorted by a value: dates and sizes sorted as text came out of order."""

    def __init__(self, text: str, sort_key) -> None:
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other) -> bool:
        if isinstance(other, _SortableItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)

class TaskFilesDialog(QDialog):
    def __init__(
        self,
        *,
        item_id: str,
        item_name: str = "",
        module_name: str = Module.TASK.value,
        parent=None,
        initial_files: Optional[list[dict]] = None,
    ) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._item_id = str(item_id or "").strip()
        self._item_name = str(item_name or "").strip()
        self._module_name = str(module_name or Module.TASK.value).strip().lower() or Module.TASK.value
        self._files: list[dict] = []
        self._loading = False
        self._load_worker = None
        self._load_thread = None
        # Upload runs one background request per file (audit 09, 2026-11-24): it used to block the window.
        self._uploading = False
        self._upload_queue: list[str] = []
        self._upload_total = 0
        self._upload_current = ""
        self._upload_done: list[str] = []
        self._upload_failed = ""
        self._upload_cancelled = False
        self._upload_worker = None

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
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
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

        self._cancel_upload_button = QPushButton(self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_CANCEL), self)
        self._cancel_upload_button.setProperty("variant", ButtonVariant.WARNING)
        self._cancel_upload_button.clicked.connect(self._cancel_upload)
        self._cancel_upload_button.setVisible(False)
        button_row.addWidget(self._cancel_upload_button)

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
        if initial_files is None:
            self._load_files()
        else:
            self._files = [dict(file_info) for file_info in initial_files]
            self._populate_table()
            self._update_button_states()

    def _run_with_busy_cursor(self, callback):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            return callback()
        finally:
            QApplication.restoreOverrideCursor()

    def _load_files(self) -> None:
        if self._loading:
            return
        self._loading = True
        self._count_label.setText(self._lang.translate(TranslationKeys.LOADING))
        self._refresh_button.setEnabled(False)
        self._upload_button.setEnabled(False)
        self._update_button_states()
        worker = FunctionWorker(APIModuleActions.get_module_files, self._module_name, self._item_id)
        worker.finished.connect(self._files_loaded)
        worker.error.connect(self._files_failed)
        self._load_worker = worker
        self._load_thread = start_worker(worker)

    @pyqtSlot(str)
    def _files_failed(self, _message: str) -> None:
        self._files_loaded(None)

    @pyqtSlot(object)
    def _files_loaded(self, files) -> None:
        self._loading = False
        self._refresh_button.setEnabled(True)
        self._upload_button.setEnabled(True)
        if files is None:
            # The old rows may name files that are gone or changed: no preview or delete from them.
            self._files = []
            self._table.setRowCount(0)
            self._count_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_LOAD_FAILED).format(
                    name=self._item_name or self._item_id
                )
            )
            self._refresh_button.setText(self._lang.translate(TranslationKeys.CARD_LOAD_RETRY))
            self._update_button_states()
            return
        self._refresh_button.setText(self._lang.translate(TranslationKeys.TASK_FILES_REFRESH))
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
            name_item.setData(Qt.ItemDataRole.UserRole, dict(file_info))
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, _SortableItem(size, self._size_sort_key(file_info.get("size"))))
            self._table.setItem(row, 2, QTableWidgetItem(mime_type))
            self._table.setItem(row, 3, QTableWidgetItem(uploader))
            parsed = DateHelpers.parse_iso(str(file_info.get("createdAt") or "").strip())
            self._table.setItem(row, 4, _SortableItem(created, parsed.isoformat() if parsed is not None else ""))

        count = len(self._files)
        if count <= 0:
            self._count_label.setText(self._lang.translate(TranslationKeys.TASK_FILES_EMPTY))
        else:
            self._count_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_COUNT).format(count=count)
            )
        self._table.setSortingEnabled(True)
        self._table.sortItems(4, Qt.SortOrder.DescendingOrder)

    @staticmethod
    def _size_sort_key(raw_size) -> int:
        try:
            return int(raw_size)
        except (TypeError, ValueError):
            return -1

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
            return locale.toString(parsed, QLocale.FormatType.ShortFormat)
        except TypeError:  # value Qt cannot convert
            return parsed.strftime("%Y-%m-%d %H:%M")

    def _selected_file(self) -> Optional[dict]:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self._table.item(row, 0)
        if item is None:
            return None

        payload = item.data(Qt.ItemDataRole.UserRole)
        return dict(payload or {}) if isinstance(payload, dict) else None

    def _update_button_states(self) -> None:
        has_selection = not self._loading and not self._uploading and self._selected_file() is not None
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

        dialog = TaskFilePreviewDialog.open_preview(
            file_info=file_info,
            parent=self,
        )
        if dialog is not None:
            dialog.exec()

    @staticmethod
    def _file_name_from_info(file_info: Optional[dict]) -> str:
        data = file_info if isinstance(file_info, dict) else {}
        return str(data.get("fileName") or data.get("uuid") or "-")

    @staticmethod
    def _base_name(path: str) -> str:
        return os.path.basename(path) or path

    def _upload_files(self) -> None:
        """Upload the chosen files one by one in the background; the window stays usable.

        Each file is its own request, so Cancel stops the queue after the file in flight
        (a started upload cannot be taken back). The first unconfirmed file stops the queue.
        """
        try:
            if self._uploading:
                return
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_DIALOG_TITLE),
                "",
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_DIALOG_FILTER),
            )
            queue = [str(path or "").strip() for path in (paths or [])]
            queue = [path for path in queue if path]
            if not queue:
                return

            self._uploading = True
            self._upload_queue = queue
            self._upload_total = len(queue)
            self._upload_current = ""
            self._upload_done = []
            self._upload_failed = ""
            self._upload_cancelled = False
            self._refresh_button.setEnabled(False)
            self._upload_button.setEnabled(False)
            self._cancel_upload_button.setEnabled(True)
            self._cancel_upload_button.setVisible(True)
            self._update_button_states()
            self._start_next_upload()
        except Exception as exc:  # button callback: nothing may escape
            PythonFailLogger.log_exception(exc, module=self._module_name, event="task_files_upload_start_failed")
            self._finish_upload()

    def _start_next_upload(self) -> None:
        if self._upload_cancelled or self._upload_failed or not self._upload_queue:
            self._finish_upload()
            return
        path = self._upload_queue.pop(0)
        self._upload_current = path
        index = self._upload_total - len(self._upload_queue)
        self._count_label.setText(
            self._lang.translate(TranslationKeys.TASK_FILES_UPLOADING).format(
                index=index, total=self._upload_total, name=self._base_name(path))
        )
        worker = FunctionWorker(APIModuleActions.upload_module_file, self._module_name, self._item_id, path)
        worker.finished.connect(self._upload_file_finished)
        worker.error.connect(self._upload_file_failed)
        self._upload_worker = worker
        start_worker(worker)

    @pyqtSlot(object)
    def _upload_file_finished(self, uploaded) -> None:
        try:
            if not self._uploading:
                return
            self._upload_worker = None
            name = self._base_name(self._upload_current)
            if isinstance(uploaded, dict) and str(uploaded.get("uuid") or "").strip():
                self._upload_done.append(name)
            else:
                self._upload_failed = name
            self._start_next_upload()
        except Exception as exc:  # Qt slot: nothing may escape
            PythonFailLogger.log_exception(exc, module=self._module_name, event="task_files_upload_step_failed")
            self._finish_upload()

    @pyqtSlot(str)
    def _upload_file_failed(self, _message: str) -> None:
        self._upload_file_finished(None)

    def _cancel_upload(self) -> None:
        try:
            if not self._uploading:
                return
            self._upload_cancelled = True
            self._cancel_upload_button.setEnabled(False)
            self._count_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_CANCELLING).format(
                    name=self._base_name(self._upload_current))
            )
        except Exception as exc:  # button callback: nothing may escape
            PythonFailLogger.log_exception(exc, module=self._module_name, event="task_files_upload_cancel_failed")

    def _finish_upload(self) -> None:
        if not self._uploading:
            return
        uploaded = list(self._upload_done)
        failed = self._upload_failed
        pending_names = [self._base_name(path) for path in self._upload_queue]
        cancelled = self._upload_cancelled and not failed
        self._uploading = False
        self._upload_queue = []
        self._upload_worker = None
        self._cancel_upload_button.setVisible(False)
        self._upload_button.setEnabled(True)
        self._refresh_button.setEnabled(True)
        self._update_button_states()

        # Refresh also after an uncertain response: the last file may be saved.
        self._load_files()
        if failed:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_STOPPED).format(
                    uploaded=len(uploaded), failed=failed,
                    pending=len(pending_names), pending_names=", ".join(pending_names)),
            )
        elif cancelled and pending_names:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_CANCELLED).format(
                    uploaded=len(uploaded), pending=len(pending_names), pending_names=", ".join(pending_names)),
            )
        else:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.SUCCESS),
                self._lang.translate(TranslationKeys.TASK_FILES_UPLOAD_SUCCESS).format(count=len(uploaded)),
            )

    def done(self, result: int) -> None:  # noqa: D401 - Qt override
        """Closing stops the upload queue; the file in flight finishes on the server unseen."""
        if self._uploading:
            self._upload_cancelled = True
            self._upload_queue = []
            self._uploading = False
            worker = self._upload_worker
            self._upload_worker = None
            if worker is not None:
                try:
                    worker.detach()
                except RuntimeError:  # worker already deleted
                    pass
        super().done(result)

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
