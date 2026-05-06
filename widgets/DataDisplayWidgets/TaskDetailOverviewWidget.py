from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...python.responses import DataDisplayExtractors
from ..theme_manager import ThemeManager
from .HtmlDescriptionWidget import HtmlDescriptionWidget
from .TaskFilePreviewDialog import TaskFilePreviewDialog


class _FilePreviewSquareButton(QPushButton):
    THUMB_SIZE = 25
    THUMB_MAX_BYTES = 2 * 1024 * 1024

    def __init__(self, *, file_info: dict, icon_path: str, lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._file_info = dict(file_info or {})
        self._fallback_icon_path = str(icon_path or "").strip()
        self._preview_worker = None
        self._preview_thread = None

        self.setObjectName("TaskFilesSummaryPreviewButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setFixedSize(self.THUMB_SIZE, self.THUMB_SIZE)
        self.setStyleSheet("padding: 0; margin: 0;")
        self._apply_fallback_icon()

        if TaskFilePreviewDialog.is_image_preview_candidate(file_info=self._file_info):
            self._start_thumbnail_load()

    def _apply_fallback_icon(self) -> None:
        icon = QIcon(self._fallback_icon_path)
        self.setIcon(icon)
        self.setIconSize(self.size())

    def _start_thumbnail_load(self) -> None:
        file_uuid = str(self._file_info.get("uuid") or "").strip()
        if not file_uuid or self._preview_thread is not None:
            return

        worker = FunctionWorker(self._fetch_thumbnail_payload, file_uuid)
        worker.finished.connect(self._handle_thumbnail_loaded)
        worker.error.connect(self._handle_thumbnail_error)
        self._preview_worker = worker
        self._preview_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _fetch_thumbnail_payload(self, file_uuid: str):
        return APIModuleActions.fetch_file_preview_payload(
            file_uuid,
            max_bytes=self.THUMB_MAX_BYTES,
        )

    def _handle_thumbnail_loaded(self, payload: object) -> None:
        if not isinstance(payload, dict):
            return

        content = payload.get("content") or b""
        pixmap = QPixmap()
        if not pixmap.loadFromData(content):
            return

        scaled = pixmap.scaled(
            self.THUMB_SIZE,
            self.THUMB_SIZE,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.setIcon(QIcon(scaled))
        self.setIconSize(self.size())

    def _handle_thumbnail_error(self, _message: str) -> None:
        return

    def _cleanup_worker(self) -> None:
        self._preview_worker = None
        self._preview_thread = None


class TaskFilesSummaryWidget(QWidget):
    MAX_VISIBLE_FILES = 5
    _ICON_DIR = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "Fileicons")
    )
    _EXTENSION_ICON_MAP = {
        "asice": "Digidoc_512.png",
        "bdoc": "Digidoc_512.png",
        "cad": "cad.png",
        "ddoc": "Digidoc_512.png",
        "dgn": "dgn.png",
        "doc": "doc.png",
        "docx": "docx.png",
        "dwg": "cad.png",
        "dxf": "cad.png",
        "htm": "html.png",
        "html": "html.png",
        "jpeg": "jpg.png",
        "jpg": "jpg.png",
        "mov": "mov.png",
        "mp4": "mov.png",
        "ods": "sheet.png",
        "pdf": "pdf-file-format.png",
        "png": "jpg.png",
        "rtf": "doc.png",
        "txt": "txt.png",
        "xls": "sheet.png",
        "xlsx": "xlsx.png",
        "zip": "zip.png",
    }
    _MIME_ICON_MAP = {
        "application/pdf": "pdf-file-format.png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx.png",
        "application/msword": "doc.png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx.png",
        "application/vnd.ms-excel": "sheet.png",
        "application/zip": "zip.png",
        "application/x-zip-compressed": "zip.png",
        "text/html": "html.png",
        "text/plain": "txt.png",
        "image/jpeg": "jpg.png",
        "image/png": "jpg.png",
        "video/quicktime": "mov.png",
        "video/mp4": "mov.png",
    }

    def __init__(self, *, item_id: str, item_name: str = "", module_name: str = "task", lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item_id = str(item_id or "").strip()
        self._item_name = str(item_name or self._item_id).strip()
        self._module_name = str(module_name or "task").strip().lower() or "task"
        self._files: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(6)

        self._title_label = QLabel(self._lang.translate(TranslationKeys.TASK_FILES_ACTION), self)
        self._title_label.setObjectName("TaskFilesSummaryTitle")
        layout.addWidget(self._title_label)

        self._count_label = QLabel(self)
        self._count_label.setObjectName("TaskFilesSummaryCount")
        self._count_label.setWordWrap(True)
        layout.addWidget(self._count_label)

        self._list_host = QWidget(self)
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        layout.addWidget(self._list_host)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("TaskFilesSummaryStatus")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._load_files()
        self.retheme()

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO, QssPaths.BUTTONS])

    def _load_files(self) -> None:
        if not APIModuleActions._file_query_name(self._module_name):
            self.hide()
            return

        files = APIModuleActions.get_module_files(self._module_name, self._item_id)
        if files is None:
            self._files = []
            self._count_label.setText("")
            self._status_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_LOAD_FAILED).format(
                    name=self._item_name or self._item_id,
                )
            )
            self._rebuild_file_rows()
            return

        self._files = list(files)
        count = len(self._files)
        if count <= 0:
            self._count_label.setText(self._lang.translate(TranslationKeys.TASK_FILES_EMPTY))
        else:
            self._count_label.setText(
                self._lang.translate(TranslationKeys.TASK_FILES_COUNT).format(count=count)
            )

        hidden_count = max(0, count - self.MAX_VISIBLE_FILES)
        if hidden_count > 0:
            self._status_label.setText(
                self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=hidden_count).strip()
            )
        else:
            self._status_label.setText("")

        self._rebuild_file_rows()

    def _rebuild_file_rows(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._files:
            return

        for file_info in self._files[: self.MAX_VISIBLE_FILES]:
            row = QWidget(self._list_host)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            icon_label = QLabel(row)
            icon_label.setObjectName("TaskFilesSummaryIcon")
            icon = QIcon(self._icon_path_for_file(file_info))
            pixmap = icon.pixmap(18, 18)
            icon_label.setPixmap(pixmap)
            icon_label.setFixedSize(18, 18)
            row_layout.addWidget(icon_label, 0, Qt.AlignTop)

            file_name = TaskFilePreviewDialog.resolve_file_name(file_info=file_info)
            button = QPushButton(file_name or "-", row)
            button.setObjectName("TaskFilesSummaryButton")
            button.setProperty("variant", "ghost")
            button.setCursor(Qt.PointingHandCursor)
            button.setFlat(True)
            button.setStyleSheet("text-align: left; padding: 0;")
            button.clicked.connect(
                lambda _checked=False, payload=dict(file_info): self._open_preview(payload)
            )
            row_layout.addWidget(button, 1)

            if TaskFilePreviewDialog.is_image_preview_candidate(file_info=file_info):
                preview_button = _FilePreviewSquareButton(
                    file_info=file_info,
                    icon_path=self._icon_path_for_file(file_info),
                    lang_manager=self._lang,
                    parent=row,
                )
                preview_button.clicked.connect(
                    lambda _checked=False, payload=dict(file_info): self._open_preview(payload)
                )
                row_layout.addWidget(preview_button, 0, Qt.AlignTop)

            self._list_layout.addWidget(row)

        self._list_layout.addStretch(1)

    def _icon_path_for_file(self, file_info: dict) -> str:
        file_name = TaskFilePreviewDialog.resolve_file_name(file_info=file_info)
        ext = ""
        if "." in file_name:
            ext = file_name.rsplit(".", 1)[-1].strip().lower()

        mime_type = str(file_info.get("mimeType") or "").strip().lower()
        icon_name = self._EXTENSION_ICON_MAP.get(ext) or self._MIME_ICON_MAP.get(mime_type) or "unknown-type.png"
        return os.path.join(self._ICON_DIR, icon_name)

    def _open_preview(self, file_info: dict) -> None:
        is_image = TaskFilePreviewDialog.is_image_preview_candidate(file_info=file_info)
        dialog = TaskFilePreviewDialog.open_preview(
            file_info=file_info,
            lang_manager=self._lang,
            parent=self.window(),
            compact=is_image,
            lazy=is_image,
        )
        if dialog is not None:
            dialog.exec_()


class TaskDetailOverviewWidget(QWidget):
    def __init__(
        self,
        *,
        item_data: Optional[dict],
        description_html: str = "",
        detail_widget: Optional[QWidget] = None,
        module_name: str = "task",
        lang_manager=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item_data = item_data if isinstance(item_data, dict) else {}
        self._module_name = str(module_name or "task").strip().lower() or "task"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if detail_widget is not None:
            detail_widget.setParent(self)
            layout.addWidget(detail_widget)
        else:
            description_widget = HtmlDescriptionWidget(str(description_html or ""), self, inline=True)
            layout.addWidget(description_widget)

        item_id = DataDisplayExtractors.extract_item_id(self._item_data)
        item_name = DataDisplayExtractors.extract_item_name(self._item_data) or item_id
        if item_id:
            files_widget = TaskFilesSummaryWidget(
                item_id=item_id,
                item_name=item_name,
                module_name=self._module_name,
                lang_manager=self._lang,
                parent=self,
            )
            layout.addWidget(files_widget)

        layout.addStretch(1)
        self.retheme()

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO, QssPaths.BUTTONS])
