# pyright: reportMissingImports=false
from __future__ import annotations

import mimetypes
import os
import tempfile
from typing import Optional

import requests
from qgis.PyQt.QtCore import Qt, QSize, QUrl, QTimer
from qgis.PyQt.QtGui import QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import (
    QApplication,
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
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import loadWebpage
from ..theme_manager import ThemeManager


class TaskFilePreviewDialog(QDialog):
    IMAGE_PREVIEW_MAX_BYTES = 25 * 1024 * 1024
    PDF_PREVIEW_MAX_BYTES = 40 * 1024 * 1024
    TEXT_PREVIEW_MAX_BYTES = 512 * 1024
    PDF_PREVIEW_MAX_PAGES = 10
    PDF_RENDER_SIZE = QSize(1200, 1600)
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "gif", "webp", "svg"}
    PDF_EXTENSIONS = {"pdf"}
    TEXT_EXTENSIONS = {
        "txt", "log", "csv", "tsv", "json", "xml", "yml", "yaml", "md", "py",
        "js", "ts", "css", "html", "htm", "sql", "ini", "cfg", "qml",
    }
    TEXT_MIME_TYPES = {
        "application/json",
        "application/xml",
        "application/javascript",
        "application/x-yaml",
        "application/yaml",
        "image/svg+xml",
    }
    PDF_MIME_TYPES = {"application/pdf"}
    FORCE_EXTERNAL_EXTENSIONS = set()
    FORCE_EXTERNAL_MIME_TYPES = set()
    _EXTERNAL_TEMP_FILES: set[str] = set()

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
        mime_type, ext = cls._resolve_preview_identity(file_info=file_info, local_file_path=local_file_path)

        if mime_type in cls.PDF_MIME_TYPES or ext in cls.PDF_EXTENSIONS:
            supported, runtime_info = cls.embedded_pdf_runtime_support()
            if not supported:
                ModernMessageDialog.show_warning(
                    resolved_lang.translate(TranslationKeys.WARNING),
                    resolved_lang.translate(TranslationKeys.TASK_FILES_PDF_RUNTIME_UNSUPPORTED).format(
                        qt_version=runtime_info.get("qt") or "unknown",
                        pyqt_version=runtime_info.get("pyqt") or "unknown",
                    ),
                )
                return None

            return cls(
                file_info=file_info,
                local_file_path=local_file_path,
                local_title=local_title,
                lang_manager=lang_manager,
                parent=parent,
            )

        if cls.should_force_external_open(file_info=file_info, local_file_path=local_file_path):
            if cls.open_in_default_application(file_info=file_info, local_file_path=local_file_path):
                return None

            ModernMessageDialog.show_warning(
                resolved_lang.translate(TranslationKeys.ERROR),
                resolved_lang.translate(TranslationKeys.TASK_FILES_OPEN_FAILED).format(
                    name=cls.resolve_file_name(file_info=file_info, local_file_path=local_file_path)
                ),
            )
            return None

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
        mime_type, ext = cls._resolve_preview_identity(file_info=file_info, local_file_path=local_file_path)
        return mime_type.startswith("image/") or ext in cls.IMAGE_EXTENSIONS

    @classmethod
    def should_force_external_open(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> bool:
        mime_type, ext = cls._resolve_preview_identity(file_info=file_info, local_file_path=local_file_path)
        return mime_type in cls.FORCE_EXTERNAL_MIME_TYPES or ext in cls.FORCE_EXTERNAL_EXTENSIONS

    @classmethod
    def embedded_pdf_runtime_support(cls) -> tuple[bool, dict[str, str]]:
        qt_version = "unknown"
        pyqt_version = "unknown"

        try:
            from qgis.PyQt.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

            qt_version = str(QT_VERSION_STR or "unknown")
            pyqt_version = str(PYQT_VERSION_STR or "unknown")
        except Exception:
            pass

        try:
            from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView  # noqa: F401

            return bool(hasattr(QWebEngineSettings, "PdfViewerEnabled")), {
                "qt": qt_version,
                "pyqt": pyqt_version,
            }
        except Exception:
            return False, {
                "qt": qt_version,
                "pyqt": pyqt_version,
            }

    @classmethod
    def open_in_default_application(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> bool:
        normalized_local_path = str(local_file_path or "").strip()
        if normalized_local_path:
            return cls._open_local_path_in_default_application(normalized_local_path)

        data = file_info if isinstance(file_info, dict) else {}
        temp_path = cls._materialize_remote_file_to_temp(data)
        if not temp_path:
            return False
        return cls._open_local_path_in_default_application(temp_path)

    @classmethod
    def _open_local_path_in_default_application(cls, path: str) -> bool:
        normalized_path = str(path or "").strip()
        if not normalized_path or not os.path.exists(normalized_path):
            return False

        try:
            if hasattr(os, "startfile"):
                os.startfile(normalized_path)  # type: ignore[attr-defined]
                return True
        except Exception:
            pass

        try:
            return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path)))
        except Exception:
            return False

    @classmethod
    def _materialize_remote_file_to_temp(cls, file_info: Optional[dict]) -> str:
        data = file_info if isinstance(file_info, dict) else {}
        file_uuid = str(data.get("uuid") or "").strip()
        if not file_uuid:
            return ""

        url = APIModuleActions.create_file_download_link(file_uuid) or ""
        if not url:
            return ""

        file_name = cls.resolve_file_name(file_info=data)
        ext = str(data.get("ext") or "").strip().lower().lstrip(".")
        suffix = f".{ext}" if ext else os.path.splitext(file_name)[1]
        if not suffix:
            suffix = ".bin"

        cls._cleanup_missing_temp_paths()

        try:
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = str(handle.name or "")
            with handle:
                with requests.get(url, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            handle.write(chunk)
        except Exception:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return ""

        if not temp_path or not os.path.exists(temp_path):
            return ""

        cls._EXTERNAL_TEMP_FILES.add(temp_path)
        return temp_path

    @classmethod
    def _cleanup_missing_temp_paths(cls) -> None:
        cls._EXTERNAL_TEMP_FILES = {
            path for path in cls._EXTERNAL_TEMP_FILES
            if str(path or "").strip() and os.path.exists(path)
        }

    @classmethod
    def resolve_file_name(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> str:
        normalized_local_path = str(local_file_path or "").strip()
        if normalized_local_path:
            return os.path.basename(normalized_local_path) or normalized_local_path or "-"
        data = file_info if isinstance(file_info, dict) else {}
        return str(data.get("fileName") or data.get("uuid") or "-")

    @classmethod
    def _resolve_preview_identity(cls, *, file_info: Optional[dict] = None, local_file_path: str = "") -> tuple[str, str]:
        normalized_local_path = str(local_file_path or "").strip()
        if normalized_local_path:
            guessed, _ = mimetypes.guess_type(normalized_local_path)
            mime_type = str(guessed or "").strip().lower()
            ext = os.path.splitext(normalized_local_path)[1].strip().lower().lstrip(".")
            return mime_type, ext

        data = file_info if isinstance(file_info, dict) else {}
        mime_type = str(data.get("mimeType") or "").strip().lower()
        ext = str(data.get("ext") or "").strip().lower().lstrip(".")
        return mime_type, ext

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
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
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
        self._meta_label.setObjectName("TaskFilePreviewMeta")
        layout.addWidget(self._meta_label)

        self._notice_label = QLabel(self)
        self._notice_label.setWordWrap(True)
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
        buttons.addWidget(self._open_external_button)

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

    def _run_with_busy_cursor(self, callback):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            return callback()
        finally:
            QApplication.restoreOverrideCursor()

    def _file_name(self) -> str:
        if self._local_file_path:
            return os.path.basename(self._local_file_path) or self._local_file_path or "-"
        return str(self._file_info.get("fileName") or self._file_info.get("uuid") or "-")

    def _file_uuid(self) -> str:
        return str(self._file_info.get("uuid") or "").strip()

    def _file_mime(self) -> str:
        if self._local_file_path:
            guessed, _ = mimetypes.guess_type(self._local_file_path)
            return str(guessed or "").strip().lower()
        return str(self._file_info.get("mimeType") or "").strip().lower()

    def _file_ext(self) -> str:
        if self._local_file_path:
            return os.path.splitext(self._local_file_path)[1].strip().lower().lstrip(".")
        return str(self._file_info.get("ext") or "").strip().lower().lstrip(".")

    def _set_meta_text(self) -> None:
        name = self._file_name()
        if self._local_file_path:
            size = self._human_readable_size(self._safe_int(os.path.getsize(self._local_file_path)) if os.path.exists(self._local_file_path) else None)
            uploader = "Local file"
        else:
            size = str(self._file_info.get("humanReadableSize") or "").strip() or "–"
            uploader = APIModuleActions.user_display_name(self._file_info.get("uploader")) or "–"
        mime_type = self._file_mime() or self._file_ext() or "–"
        self._meta_label.setText(
            f"<b>{name}</b><br>{mime_type} • {size} • {uploader}"
        )

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
        label.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(label, 1, Qt.AlignCenter)

    def _release_web_view(self) -> None:
        if self._web_view is None:
            return

        web_view = self._web_view

        try:
            web_view.stop()
        except Exception:
            pass

        try:
            web_view.setUrl(QUrl("about:blank"))
        except Exception:
            pass

        try:
            web_view.deleteLater()
        except Exception:
            pass

        self._web_view = None

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._cleanup_pdf_temp_file()
        super().closeEvent(event)

    def _should_lazy_load_image_preview(self) -> bool:
        if not self._lazy_preview or self._local_file_path:
            return False
        return self._resolve_preview_kind() == "image"

    def _start_lazy_image_preview_load(self) -> None:
        file_uuid = self._file_uuid()
        if not file_uuid:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        if self._preview_thread is not None:
            return

        worker = FunctionWorker(self._fetch_image_preview_payload, file_uuid)
        worker.finished.connect(self._handle_lazy_image_preview_loaded)
        worker.error.connect(self._handle_lazy_image_preview_error)
        self._preview_worker = worker
        self._preview_thread = start_worker(worker, on_thread_finished=self._cleanup_preview_worker)

    def _fetch_image_preview_payload(self, file_uuid: str):
        return APIModuleActions.fetch_file_preview_payload(
            file_uuid,
            max_bytes=self.IMAGE_PREVIEW_MAX_BYTES,
        )

    def _handle_lazy_image_preview_loaded(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return
        self._apply_image_preview_payload(payload)

    def _handle_lazy_image_preview_error(self, _message: str) -> None:
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _cleanup_preview_worker(self) -> None:
        self._preview_worker = None
        self._preview_thread = None

    def _load_preview(self) -> None:
        if self._local_file_path:
            self._load_local_preview()
            return

        file_uuid = self._file_uuid()
        if not file_uuid:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
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

    def _load_local_preview(self) -> None:
        if not self._local_file_path or not os.path.exists(self._local_file_path):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        preview_kind = self._resolve_preview_kind()
        if preview_kind != "pdf":
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
            )
            return

        try:
            size_bytes = os.path.getsize(self._local_file_path)
        except Exception:
            size_bytes = None
        if size_bytes is not None and size_bytes > self.PDF_PREVIEW_MAX_BYTES:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        try:
            from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
        except ImportError:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
            )
            return

        if self._load_pdf_webengine_preview(
            self._local_file_path,
            webengine_settings_cls=QWebEngineSettings,
            webengine_view_cls=QWebEngineView,
        ):
            self._last_url = QUrl.fromLocalFile(self._local_file_path).toString()
            return

        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _resolve_preview_kind(self) -> str:
        mime_type = self._file_mime()
        ext = self._file_ext()

        if mime_type in self.PDF_MIME_TYPES or ext in self.PDF_EXTENSIONS:
            return "pdf"
        if mime_type.startswith("image/") or ext in self.IMAGE_EXTENSIONS:
            return "image"
        if mime_type.startswith("text/") or mime_type in self.TEXT_MIME_TYPES or ext in self.TEXT_EXTENSIONS:
            return "text"
        return "unsupported"

    def _load_pdf_preview(self, file_uuid: str) -> None:
        size_bytes = self._safe_int(self._file_info.get("size"))
        if size_bytes is not None and size_bytes > self.PDF_PREVIEW_MAX_BYTES:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        try:
            # inline import: QtWebEngine is optional in some QGIS Qt5 builds; import lazily to avoid breaking plugin startup.
            from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
        except ImportError:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
            )
            return

        payload = self._run_with_busy_cursor(
            lambda: APIModuleActions.fetch_file_preview_payload(
                file_uuid,
                max_bytes=self.PDF_PREVIEW_MAX_BYTES,
            )
        )
        if not isinstance(payload, dict):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        self._last_url = str(payload.get("url") or "").strip()
        if payload.get("truncated"):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        content = payload.get("content") or b""
        if not content:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        temp_path = self._write_pdf_temp_file(content)
        if not temp_path:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        if self._load_pdf_webengine_preview(
            temp_path,
            webengine_settings_cls=QWebEngineSettings,
            webengine_view_cls=QWebEngineView,
        ):
            return

        self._cleanup_pdf_temp_file()
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _load_pdf_webengine_preview(
        self,
        temp_path: str,
        *,
        webengine_settings_cls,
        webengine_view_cls,
    ) -> bool:
        self._release_web_view()
        self._set_notice("")
        self._clear_content()

        try:
            web_view = webengine_view_cls(self._content_frame)
        except Exception:
            return False

        try:
            settings = web_view.settings()
        except Exception:
            settings = None

        if settings is not None:
            if hasattr(webengine_settings_cls, "PdfViewerEnabled"):
                try:
                    settings.setAttribute(webengine_settings_cls.PdfViewerEnabled, True)
                except Exception:
                    pass

            if hasattr(webengine_settings_cls, "PluginsEnabled"):
                try:
                    settings.setAttribute(webengine_settings_cls.PluginsEnabled, True)
                except Exception:
                    pass

        try:
            web_view.loadFinished.connect(self._handle_pdf_web_view_loaded)
        except Exception:
            pass

        self._web_view = web_view
        self._content_layout.addWidget(web_view, 1)

        try:
            web_view.setUrl(QUrl.fromLocalFile(temp_path))
        except Exception:
            try:
                web_view.load(QUrl.fromLocalFile(temp_path))
            except Exception:
                self._release_web_view()
                self._clear_content()
                return False

        return True

    def _handle_pdf_web_view_loaded(self, ok: bool) -> None:
        if ok or not self.isVisible():
            return

        self._cleanup_pdf_temp_file()
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _write_pdf_temp_file(self, content: bytes) -> str:
        self._cleanup_pdf_temp_file()
        try:
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            with handle:
                handle.write(content)
            self._pdf_temp_path = str(handle.name or "")
            return self._pdf_temp_path
        except Exception:
            self._pdf_temp_path = ""
            return ""

    def _cleanup_pdf_temp_file(self) -> None:
        self._release_web_view()

        path = str(self._pdf_temp_path or "").strip()
        self._pdf_temp_path = ""
        if not path:
            return

        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _load_image_preview(self, file_uuid: str) -> None:
        size_bytes = self._safe_int(self._file_info.get("size"))
        if size_bytes is not None and size_bytes > self.IMAGE_PREVIEW_MAX_BYTES:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        payload = self._run_with_busy_cursor(
            lambda: APIModuleActions.fetch_file_preview_payload(
                file_uuid,
                max_bytes=self.IMAGE_PREVIEW_MAX_BYTES,
            )
        )
        if not isinstance(payload, dict):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        self._apply_image_preview_payload(payload)

    def _apply_image_preview_payload(self, payload: dict) -> None:
        if not isinstance(payload, dict):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
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
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
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
        payload = self._run_with_busy_cursor(
            lambda: APIModuleActions.fetch_file_preview_payload(
                file_uuid,
                max_bytes=self.TEXT_PREVIEW_MAX_BYTES,
            )
        )
        if not isinstance(payload, dict):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                    name=self._file_name()
                )
            )
            return

        self._last_url = str(payload.get("url") or "").strip()
        content = payload.get("content") or b""
        text = self._decode_text(content)

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

    @staticmethod
    def _decode_text(content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
            try:
                return content.decode(encoding)
            except Exception:
                continue
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _open_externally(self) -> None:
        if self.open_in_default_application(file_info=self._file_info, local_file_path=self._local_file_path):
            return

        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.TASK_FILES_OPEN_FAILED).format(
                name=self._file_name()
            ),
        )

    @staticmethod
    def _human_readable_size(size_bytes: Optional[int]) -> str:
        if size_bytes is None:
            return "–"
        try:
            value = float(size_bytes)
        except Exception:
            return "–"
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        while value >= 1024.0 and unit_index < len(units) - 1:
            value /= 1024.0
            unit_index += 1
        if unit_index == 0:
            return f"{int(value)} {units[unit_index]}"
        return f"{value:.1f} {units[unit_index]}"
