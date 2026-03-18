from __future__ import annotations

import os
import tempfile
import time
from typing import Optional

from qgis.PyQt.QtCore import Qt, QSize, QUrl
from qgis.PyQt.QtGui import QPixmap
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
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import loadWebpage
from ..theme_manager import ThemeManager

try:
    from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView  # type: ignore
except Exception:
    QWebEngineSettings = None  # type: ignore[assignment]
    QWebEngineView = None  # type: ignore[assignment]

try:
    from qgis.PyQt.QtPdf import QPdfDocument  # type: ignore
except Exception:
    QPdfDocument = None  # type: ignore[assignment]


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

    def __init__(self, *, file_info: dict, lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._file_info = dict(file_info or {})
        self._last_url: str = ""
        self._pdf_temp_path: str = ""
        self._pdf_document = None
        self._web_view = None

        self.setModal(True)
        self.setObjectName("TaskFilePreviewDialog")
        self.setMinimumSize(760, 520)
        self.setWindowTitle(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TITLE).format(
                name=self._file_name()
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
        self._load_preview()

    def _run_with_busy_cursor(self, callback):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            return callback()
        finally:
            QApplication.restoreOverrideCursor()

    def _file_name(self) -> str:
        return str(self._file_info.get("fileName") or self._file_info.get("uuid") or "-")

    def _file_uuid(self) -> str:
        return str(self._file_info.get("uuid") or "").strip()

    def _file_mime(self) -> str:
        return str(self._file_info.get("mimeType") or "").strip().lower()

    def _file_ext(self) -> str:
        return str(self._file_info.get("ext") or "").strip().lower().lstrip(".")

    def _set_meta_text(self) -> None:
        name = self._file_name()
        size = str(self._file_info.get("humanReadableSize") or "").strip() or "–"
        mime_type = self._file_mime() or self._file_ext() or "–"
        uploader = APIModuleActions.user_display_name(self._file_info.get("uploader")) or "–"
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

    def _load_preview(self) -> None:
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

        if QWebEngineView is None and QPdfDocument is None:
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

        if self._load_pdf_webengine_preview(temp_path):
            return

        if self._load_pdf_document_preview(temp_path):
            return

        self._cleanup_pdf_temp_file()
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _load_pdf_webengine_preview(self, temp_path: str) -> bool:
        if QWebEngineView is None:
            return False

        self._release_web_view()
        self._set_notice("")
        self._clear_content()

        try:
            web_view = QWebEngineView(self._content_frame)
        except Exception:
            return False

        if QWebEngineSettings is not None:
            try:
                settings = web_view.settings()
            except Exception:
                settings = None

            if settings is not None:
                if hasattr(QWebEngineSettings, "PdfViewerEnabled"):
                    try:
                        settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
                    except Exception:
                        pass

                if hasattr(QWebEngineSettings, "PluginsEnabled"):
                    try:
                        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
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

        temp_path = str(self._pdf_temp_path or "").strip()
        self._release_web_view()

        if temp_path and self._load_pdf_document_preview(temp_path):
            return

        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_FAILED).format(
                name=self._file_name()
            )
        )

    def _load_pdf_document_preview(self, temp_path: str) -> bool:
        if QPdfDocument is None:
            return False

        pdf_document = QPdfDocument(self)
        try:
            pdf_document.load(temp_path)
        except Exception:
            try:
                pdf_document.close()
            except Exception:
                pass
            return False

        if not self._wait_for_pdf_document(pdf_document):
            try:
                pdf_document.close()
            except Exception:
                pass
            return False

        self._release_web_view()
        self._pdf_document = pdf_document
        self._set_notice("")
        self._clear_content()

        scroll = QScrollArea(self._content_frame)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget(scroll)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(12)

        page_count = max(0, int(pdf_document.pageCount()))
        pages_to_render = min(page_count, self.PDF_PREVIEW_MAX_PAGES)

        rendered_any = False
        for page_index in range(pages_to_render):
            try:
                image = pdf_document.render(page_index, self.PDF_RENDER_SIZE)
            except Exception:
                image = None
            if image is None or image.isNull():
                continue

            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                continue

            page_label = QLabel(container)
            page_label.setAlignment(Qt.AlignCenter)
            page_label.setPixmap(pixmap)
            container_layout.addWidget(page_label, 0, Qt.AlignHCenter)
            rendered_any = True

        container_layout.addStretch(1)
        scroll.setWidget(container)
        self._content_layout.addWidget(scroll, 1)

        if not rendered_any:
            self._clear_content()
            try:
                pdf_document.close()
            except Exception:
                pass
            self._pdf_document = None
            return False

        if page_count > pages_to_render:
            self._set_notice(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_PAGE_LIMIT).format(
                    count=pages_to_render
                )
            )
        else:
            self._set_notice("")

        return True

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

        if self._pdf_document is not None:
            try:
                self._pdf_document.close()
            except Exception:
                pass
        self._pdf_document = None

        path = str(self._pdf_temp_path or "").strip()
        self._pdf_temp_path = ""
        if not path:
            return

        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    @staticmethod
    def _wait_for_pdf_document(pdf_document) -> bool:
        ready_value = getattr(QPdfDocument, "Ready", 2)
        error_value = getattr(QPdfDocument, "Error", 4)
        loading_value = getattr(QPdfDocument, "Loading", 1)

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                status = pdf_document.status()
            except Exception:
                status = None

            if status == ready_value:
                return True
            if status == error_value:
                return False
            if status != loading_value and pdf_document.pageCount() > 0:
                return True

            QApplication.processEvents()
            time.sleep(0.02)

        try:
            return pdf_document.pageCount() > 0
        except Exception:
            return False

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
        scaled = pixmap.scaled(1280, 960, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        url = self._last_url
        if not url:
            url = APIModuleActions.create_file_download_link(self._file_uuid()) or ""
        if url and loadWebpage.open_webpage(url):
            return

        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.TASK_FILES_OPEN_FAILED).format(
                name=self._file_name()
            ),
        )
