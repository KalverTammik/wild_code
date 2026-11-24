# pyright: reportMissingImports=false
from __future__ import annotations

import html
import os
import threading
from typing import Optional

from qgis.PyQt.QtCore import Qt, QSize, QTimer, pyqtSlot
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...ui.messages_helper import ModernMessageDialog
from ...utils.security_boundaries import resolve_allowed_external_extension
from ...ui.theme_manager import ThemeManager
from .task_file_external_open import (
    cleanup_external_temp_files,
    embedded_pdf_runtime_support,
    materialize_remote_file_to_temp,
    open_in_default_application,
    open_local_path,
)
from .task_file_identity import (
    PDF_EXTENSIONS,
    PDF_MIME_TYPES,
    decode_text,
    file_name,
    human_readable_size,
    is_image,
    preview_identity,
    preview_kind,
    safe_int,
)
from .task_file_pdf_preview import TaskFilePdfPreviewMixin


class _ExternalDownloadState:
    """Shared between the dialog and its download worker. The worker thread only writes
    plain numbers here; the dialog reads them from a timer, so no widget is touched off
    the GUI thread."""

    def __init__(self) -> None:
        self.cancel_event = threading.Event()
        self.done_bytes = 0
        self.total_bytes: Optional[int] = None

    def record(self, done_bytes: int, total_bytes: Optional[int]) -> None:
        self.done_bytes = int(done_bytes or 0)
        self.total_bytes = total_bytes


class TaskFilePreviewDialog(TaskFilePdfPreviewMixin, QDialog):
    IMAGE_PREVIEW_MAX_BYTES = 25 * 1024 * 1024
    PDF_PREVIEW_MAX_BYTES = 40 * 1024 * 1024
    TEXT_PREVIEW_MAX_BYTES = 512 * 1024
    PDF_PREVIEW_MAX_PAGES = 10
    PDF_RENDER_SIZE = QSize(1200, 1600)
    DOWNLOAD_PROGRESS_INTERVAL_MS = 250

    @classmethod
    def open_preview(
        cls,
        *,
        file_info: Optional[dict] = None,
        local_file_path: str = "",
        local_title: str = "",
        lang_manager=None,
        parent=None,
        compact: bool = False,
        lazy: bool = False,
    ):
        resolved_lang = lang_manager or LanguageManager()
        mime_type, ext = preview_identity(file_info=file_info, local_file_path=local_file_path)

        if mime_type in PDF_MIME_TYPES or ext in PDF_EXTENSIONS:
            # Without PDF support the dialog still opens, with a notice in place of the
            # preview, so the file can be opened with **Open externally**.
            supported, runtime_info = cls.embedded_pdf_runtime_support()
            return cls(
                file_info=file_info,
                local_file_path=local_file_path,
                local_title=local_title,
                lang_manager=resolved_lang,
                parent=parent,
                pdf_runtime_unsupported=None if supported else dict(runtime_info or {}),
            )

        return cls(
            file_info=file_info,
            local_file_path=local_file_path,
            local_title=local_title,
            lang_manager=lang_manager,
            parent=parent,
            compact=compact,
            lazy=lazy,
        )

    @classmethod
    def is_image_preview_candidate(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> bool:
        return is_image(*preview_identity(file_info=file_info, local_file_path=local_file_path))

    @classmethod
    def is_internal_preview_candidate(
        cls,
        *,
        file_info: Optional[dict] = None,
        local_file_path: str = "",
    ) -> bool:
        return preview_kind(*preview_identity(file_info=file_info, local_file_path=local_file_path)) != "unsupported"

    @classmethod
    def embedded_pdf_runtime_support(cls) -> tuple[bool, dict[str, str]]:
        return embedded_pdf_runtime_support()

    @classmethod
    def open_in_default_application(
        cls,
        *,
        file_info: Optional[dict] = None,
        local_file_path: str = "",
        user_confirmed: bool = False,
    ) -> bool:
        return open_in_default_application(
            file_info=file_info,
            local_file_path=local_file_path,
            user_confirmed=user_confirmed,
        )

    @classmethod
    def resolve_file_name(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> str:
        return file_name(file_info=file_info, local_file_path=local_file_path)

    def __init__(
        self,
        *,
        file_info: Optional[dict] = None,
        local_file_path: str = "",
        local_title: str = "",
        lang_manager=None,
        parent=None,
        compact: bool = False,
        lazy: bool = False,
        pdf_runtime_unsupported: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        # Qt/PyQt versions when QtWebEngine cannot show PDFs; None when it can.
        self._pdf_runtime_unsupported = (
            dict(pdf_runtime_unsupported) if isinstance(pdf_runtime_unsupported, dict) else None
        )
        self._download_state: Optional[_ExternalDownloadState] = None
        self._download_worker = None
        self._download_timer = QTimer(self)
        self._download_timer.setInterval(self.DOWNLOAD_PROGRESS_INTERVAL_MS)
        self._download_timer.timeout.connect(self._update_download_progress)
        self._file_info = dict(file_info or {})
        self._local_file_path = str(local_file_path or "").strip()
        self._local_title = str(local_title or "").strip()
        self._compact_mode = bool(compact)
        self._lazy_preview = bool(lazy)
        self._last_url: str = ""
        self._pdf_temp_path: str = ""
        self._web_view = None
        self._preview_worker = None
        self._preview_thread = None
        # Remote previews load on a worker (2026-11-24): the fetch used to block QGIS before the dialog showed.
        self._preview_apply = None
        self._preview_closed = False
        self._external_open_extension = resolve_allowed_external_extension(
            api_extension=self._file_info.get("ext"),
            file_name=self._file_info.get("fileName"),
            local_file_path=self._local_file_path,
        )

        self.setModal(True)
        self.setObjectName("TaskFilePreviewDialog")
        if self._compact_mode:
            self.setMinimumSize(420, 320)
            self.resize(520, 380)
        else:
            self.setMinimumSize(760, 520)
        self.setWindowTitle(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TITLE).format(
                name=self._local_title or self._file_name()
            )
        )

        ThemeManager.apply_module_style(
            self,
            [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO, QssPaths.MESSAGE_BOX],
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._meta_label = QLabel(self)
        self._meta_label.setWordWrap(True)
        self._meta_label.setTextFormat(Qt.RichText)
        self._meta_label.setObjectName("TaskFilePreviewMeta")
        layout.addWidget(self._meta_label)

        self._notice_label = QLabel(self)
        self._notice_label.setWordWrap(True)
        self._notice_label.setTextFormat(Qt.PlainText)
        self._notice_label.setObjectName("TaskFilePreviewNotice")
        self._notice_label.hide()
        layout.addWidget(self._notice_label)

        self._content_frame = QFrame(self)
        self._content_frame.setObjectName("TaskFilePreviewFrame")
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        layout.addWidget(self._content_frame, 1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)

        self._open_external_button = QPushButton(
            self._lang.translate(TranslationKeys.TASK_FILES_OPEN),
            self,
        )
        self._open_external_button.setProperty("variant", ButtonVariant.GHOST)
        self._open_external_button.clicked.connect(self._open_externally)
        self._open_external_button.setEnabled(bool(self._external_open_extension))
        if not self._external_open_extension:
            tooltip = (
                self._lang.translate(TranslationKeys.TASK_FILES_EXTERNAL_OPEN_BLOCKED).format(
                    name=self._local_title or self._file_name()
                )
            )
            self._open_external_button.setToolTip(self._plain_text_as_rich_text(tooltip))
        buttons.addWidget(self._open_external_button)

        self._cancel_download_button = QPushButton(
            self._lang.translate(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOAD_CANCEL),
            self,
        )
        self._cancel_download_button.setProperty("variant", ButtonVariant.GHOST)
        self._cancel_download_button.clicked.connect(self._cancel_external_download)
        self._cancel_download_button.hide()
        buttons.addWidget(self._cancel_download_button)

        buttons.addStretch(1)

        close_button = QPushButton(self._lang.translate(TranslationKeys.CLOSE), self)
        close_button.setProperty("variant", ButtonVariant.GHOST)
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

        self._set_meta_text()
        if self._should_lazy_load_image_preview():
            self._show_placeholder(self._lang.translate(TranslationKeys.LOADING))
            QTimer.singleShot(0, self._start_lazy_image_preview_load)
        else:
            self._load_preview()

    def _file_name(self) -> str:
        return file_name(file_info=self._file_info, local_file_path=self._local_file_path)

    def _file_uuid(self) -> str:
        return str(self._file_info.get("uuid") or "").strip()

    def _file_mime(self) -> str:
        return preview_identity(file_info=self._file_info, local_file_path=self._local_file_path)[0]

    def _file_ext(self) -> str:
        return preview_identity(file_info=self._file_info, local_file_path=self._local_file_path)[1]

    def _set_meta_text(self) -> None:
        name = self._file_name()
        if self._local_file_path:
            size = human_readable_size(safe_int(os.path.getsize(self._local_file_path)) if os.path.exists(self._local_file_path) else None)
            uploader = self._lang.translate(TranslationKeys.TASK_FILE_LOCAL_FILE)
        else:
            size = str(self._file_info.get("humanReadableSize") or "").strip() or "–"
            uploader = APIModuleActions.user_display_name(self._file_info.get("uploader")) or "–"
        mime_type = self._file_mime() or self._file_ext() or "–"
        self._meta_label.setText(
            f"<b>{self._escape_rich_text(name)}</b><br>"
            f"{self._escape_rich_text(mime_type)} • "
            f"{self._escape_rich_text(size)} • "
            f"{self._escape_rich_text(uploader)}"
        )

    @staticmethod
    def _escape_rich_text(value) -> str:
        return html.escape(str(value or ""), quote=True)

    @staticmethod
    def _plain_text_as_rich_text(value) -> str:
        return Qt.convertFromPlainText(str(value or ""), Qt.WhiteSpaceNormal)

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _set_notice(self, message: str = "") -> None:
        text = str(message or "").strip()
        if not text:
            self._notice_label.clear()
            self._notice_label.hide()
            return
        self._notice_label.setText(text)
        self._notice_label.show()

    def _show_placeholder(self, message: str) -> None:
        self._set_notice("")
        self._clear_content()
        label = QLabel(message, self._content_frame)
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        label.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(label, 1, Qt.AlignCenter)

    def _show_failed(self) -> None:
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(name=self._file_name())
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._release_dialog_resources()
        super().closeEvent(event)

    def done(self, result: int) -> None:  # Qt override: **Close** (accept) skips closeEvent
        self._release_dialog_resources()
        super().done(result)

    def _release_dialog_resources(self) -> None:
        try:
            self._stop_preview_fetch()
            self._stop_external_download()
            self._cleanup_pdf_temp_file()
            cleanup_external_temp_files()
        except Exception as exc:  # noqa: BLE001 - closing must never fail
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_preview_close_cleanup_failed")

    def _should_lazy_load_image_preview(self) -> bool:
        if not self._lazy_preview or self._local_file_path:
            return False
        return self._resolve_preview_kind() == "image"

    def _start_lazy_image_preview_load(self) -> None:
        file_uuid = self._file_uuid()
        if not file_uuid:
            self._show_failed()
            return
        self._load_image_preview(file_uuid)

    def _fetch_preview_in_background(self, file_uuid: str, max_bytes: int, apply) -> None:
        """Fetch a remote preview on a worker and hand the payload to ``apply`` in the GUI thread.

        The dialog shows **Loading** meanwhile; a result after the dialog closed is dropped.
        Signals go to bound methods of the dialog, so Qt queues them to the GUI thread.
        """
        if self._preview_thread is not None or self._preview_closed:
            return
        self._show_placeholder(self._lang.translate(TranslationKeys.LOADING))
        self._preview_apply = apply
        worker = FunctionWorker(APIModuleActions.fetch_file_preview_payload, file_uuid, max_bytes=max_bytes)
        worker.finished.connect(self._handle_preview_payload)
        worker.error.connect(self._handle_preview_error)
        self._preview_worker = worker
        self._preview_thread = start_worker(worker, on_thread_finished=self._cleanup_preview_worker)

    @pyqtSlot(object)
    def _handle_preview_payload(self, payload: object) -> None:
        try:
            apply = self._preview_apply
            self._preview_apply = None
            if apply is None or self._preview_closed:
                return
            if not isinstance(payload, dict):
                self._show_failed()
                return
            apply(payload)
        except Exception as exc:  # Qt slot: nothing may escape
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_preview_apply_failed")
            self._show_failed()

    @pyqtSlot(str)
    def _handle_preview_error(self, _message: str) -> None:
        self._handle_preview_payload(None)

    def _stop_preview_fetch(self) -> None:
        self._preview_closed = True
        self._preview_apply = None
        worker = self._preview_worker
        if worker is not None:
            try:
                worker.detach()
                worker.cancel()
            except RuntimeError:  # worker already deleted
                pass

    def _cleanup_preview_worker(self) -> None:
        self._preview_worker = None
        self._preview_thread = None

    def _load_preview(self) -> None:
        if self._local_file_path:
            self._load_local_preview()
            return

        file_uuid = self._file_uuid()
        if not file_uuid:
            self._show_failed()
            return

        preview_kind = self._resolve_preview_kind()
        if preview_kind == "image":
            self._load_image_preview(file_uuid)
            return
        if preview_kind == "pdf":
            self._load_pdf_preview(file_uuid)
            return
        if preview_kind == "text":
            self._load_text_preview(file_uuid)
            return

        self._set_notice("")
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
        )

    def _resolve_preview_kind(self) -> str:
        return preview_kind(self._file_mime(), self._file_ext())

    def _load_image_preview(self, file_uuid: str) -> None:
        size_bytes = safe_int(self._file_info.get("size"))
        if size_bytes is not None and size_bytes > self.IMAGE_PREVIEW_MAX_BYTES:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        self._fetch_preview_in_background(file_uuid, self.IMAGE_PREVIEW_MAX_BYTES, self._apply_image_preview_payload)

    def _apply_image_preview_payload(self, payload: dict) -> None:
        if not isinstance(payload, dict):
            self._show_failed()
            return

        self._last_url = str(payload.get("url") or "").strip()
        if payload.get("truncated"):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        content = payload.get("content") or b""
        pixmap = QPixmap()
        if not pixmap.loadFromData(content):
            self._show_failed()
            return

        self._set_notice("")
        self._clear_content()

        image_label = QLabel(self._content_frame)
        image_label.setAlignment(Qt.AlignCenter)
        max_width = 640 if self._compact_mode else 1280
        max_height = 420 if self._compact_mode else 960
        scaled = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled)

        container = QWidget(self._content_frame)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.addWidget(image_label, 1, Qt.AlignCenter)

        scroll = QScrollArea(self._content_frame)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)
        self._content_layout.addWidget(scroll, 1)

    def _load_text_preview(self, file_uuid: str) -> None:
        self._fetch_preview_in_background(file_uuid, self.TEXT_PREVIEW_MAX_BYTES, self._apply_text_preview_payload)

    def _apply_text_preview_payload(self, payload: dict) -> None:
        self._last_url = str(payload.get("url") or "").strip()
        content = payload.get("content") or b""
        text = decode_text(content)

        editor = QPlainTextEdit(self._content_frame)
        editor.setReadOnly(True)
        editor.setPlainText(text)
        editor.setLineWrapMode(QPlainTextEdit.NoWrap)

        self._clear_content()
        self._content_layout.addWidget(editor, 1)

        if payload.get("truncated"):
            preview_kb = max(1, self.TEXT_PREVIEW_MAX_BYTES // 1024)
            self._set_notice(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TRUNCATED).format(
                    count=preview_kb
                )
            )
        else:
            self._set_notice("")

    def _open_externally(self) -> None:
        try:
            self._open_externally_unguarded()
        except Exception as exc:  # noqa: BLE001 - a button slot must not raise
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_external_open_failed")
            self._finish_external_download_ui()
            self._show_open_failed()

    def _open_externally_unguarded(self) -> None:
        if self._download_state is not None:
            return

        extension = resolve_allowed_external_extension(
            api_extension=self._file_info.get("ext"),
            file_name=self._file_info.get("fileName"),
            local_file_path=self._local_file_path,
        )
        if not extension:
            message = self._lang.translate(
                TranslationKeys.TASK_FILES_EXTERNAL_OPEN_BLOCKED
            ).format(
                name=self._local_title or self._file_name()
            )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._plain_text_as_rich_text(message),
                parent=self,
            )
            return

        yes_label = self._lang.translate(TranslationKeys.YES)
        no_label = self._lang.translate(TranslationKeys.NO)
        confirmation = self._lang.translate(
            TranslationKeys.TASK_FILES_EXTERNAL_OPEN_CONFIRM
        ).format(
            name=self._local_title or self._file_name(),
            extension=extension,
        )
        choice = ModernMessageDialog.ask_choice_modern(
            self._lang.translate(TranslationKeys.CONFIRM),
            self._plain_text_as_rich_text(confirmation),
            buttons=[yes_label, no_label],
            parent=self,
            default=no_label,
            cancel=no_label,
        )
        if choice != yes_label:
            return

        if not self._local_file_path:
            self._start_external_download(extension)
            return

        if self.open_in_default_application(
            file_info=self._file_info,
            local_file_path=self._local_file_path,
            user_confirmed=True,
        ):
            return
        self._show_open_failed()

    def _show_open_failed(self) -> None:
        message = self._lang.translate(TranslationKeys.TASK_FILES_OPEN_FAILED).format(
            name=self._file_name()
        )
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._plain_text_as_rich_text(message),
            parent=self,
        )

    # --- background download for Open externally ---------------------------------------

    def _start_external_download(self, extension: str) -> None:
        """Download the remote file on a worker; the dialog stays usable and can cancel."""
        state = _ExternalDownloadState()
        size = safe_int(self._file_info.get("size"))
        state.total_bytes = size if size and size > 0 else None
        worker = FunctionWorker(
            materialize_remote_file_to_temp,
            dict(self._file_info),
            allowed_extension=extension,
            cancel_event=state.cancel_event,
            progress=state.record,
        )
        worker.finished.connect(
            lambda path, current=state: self._handle_external_download_finished(current, path)
        )
        worker.error.connect(
            lambda message, current=state: self._handle_external_download_error(current, message)
        )
        self._download_state = state
        self._download_worker = worker
        self._open_external_button.setEnabled(False)
        self._cancel_download_button.show()
        self._update_download_progress()
        self._download_timer.start()
        start_worker(worker, on_thread_finished=lambda current=worker: self._forget_download_worker(current))

    def _update_download_progress(self) -> None:
        state = self._download_state
        if state is None:
            return
        done = human_readable_size(state.done_bytes)
        if state.total_bytes:
            text = self._lang.translate(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOADING).format(
                done=done,
                total=human_readable_size(state.total_bytes),
            )
        else:
            text = self._lang.translate(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOADING_NO_SIZE).format(
                done=done,
            )
        self._set_notice(text)

    def _handle_external_download_finished(self, state: _ExternalDownloadState, path: object) -> None:
        try:
            if state is not self._download_state or state.cancel_event.is_set():
                return
            self._finish_external_download_ui()
            if path and open_local_path(str(path)):
                return
            self._show_open_failed()
        except Exception as exc:  # noqa: BLE001 - a signal slot must not raise
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_external_open_failed")

    def _handle_external_download_error(self, state: _ExternalDownloadState, _message: str) -> None:
        try:
            if state is not self._download_state or state.cancel_event.is_set():
                return
            self._finish_external_download_ui()
            self._show_open_failed()
        except Exception as exc:  # noqa: BLE001 - a signal slot must not raise
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_external_open_failed")

    def _cancel_external_download(self) -> None:
        try:
            if self._download_state is None:
                return
            self._stop_external_download()
            self._set_notice(self._lang.translate(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOAD_CANCELLED))
        except Exception as exc:  # noqa: BLE001 - a button slot must not raise
            PythonFailLogger.log_exception(exc, module="ui", event="task_file_external_download_cancel_failed")

    def _stop_external_download(self) -> None:
        """Cancel a running download: the worker removes the partial file at its next chunk
        and its outcome is ignored. The worker is not detached, because its finished/error
        signal is what ends its thread."""
        state = self._download_state
        if state is None:
            return
        state.cancel_event.set()
        cancel = getattr(self._download_worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._finish_external_download_ui()

    def _finish_external_download_ui(self) -> None:
        self._download_state = None
        self._download_timer.stop()
        self._cancel_download_button.hide()
        self._open_external_button.setEnabled(bool(self._external_open_extension))
        self._set_notice("")

    def _forget_download_worker(self, worker) -> None:
        if self._download_worker is worker:
            self._download_worker = None

