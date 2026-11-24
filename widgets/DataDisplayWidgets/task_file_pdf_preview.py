"""PDF preview of TaskFilePreviewDialog: the file is written to a temp file in the plugin's
temp folder and shown in a QtWebEngine view, which is optional in QGIS builds and imported
only when needed. A temp file the view still holds is left for the age-based cleanup."""
from __future__ import annotations

import os

from qgis.PyQt.QtCore import QUrl

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.translation_keys import TranslationKeys
from .task_file_external_open import create_external_temp_file, remove_temp_file_quietly
from .task_file_identity import safe_int


class TaskFilePdfPreviewMixin:
    """Mixed into TaskFilePreviewDialog, which provides the content frame, the placeholders
    and the _pdf_temp_path / _web_view / _pdf_runtime_unsupported state."""

    def _release_web_view(self) -> None:
        if self._web_view is None:
            return

        web_view = self._web_view

        try:
            web_view.stop()
        except RuntimeError:  # web view already deleted
            pass

        try:
            web_view.setUrl(QUrl("about:blank"))
        except RuntimeError:  # web view already deleted
            pass

        try:
            web_view.deleteLater()
        except RuntimeError:  # web view already deleted
            pass

        self._web_view = None

    def _load_local_preview(self) -> None:
        if not self._local_file_path or not os.path.exists(self._local_file_path):
            self._show_failed()
            return

        preview_kind = self._resolve_preview_kind()
        if preview_kind != "pdf":
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
            )
            return

        if self._show_pdf_runtime_unavailable():
            return

        try:
            size_bytes = os.path.getsize(self._local_file_path)
        except OSError:
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

        self._show_failed()

    def _show_pdf_runtime_unavailable(self) -> bool:
        """Without PDF support in QtWebEngine the dialog stays open without a preview, so the
        user can still use **Open externally**; nothing is downloaded for the preview."""
        runtime_info = self._pdf_runtime_unsupported
        if runtime_info is None:
            return False
        self._show_placeholder(
            self._lang.translate(TranslationKeys.TASK_FILES_PDF_PREVIEW_UNAVAILABLE).format(
                qt_version=runtime_info.get("qt") or "unknown",
            )
        )
        return True

    def _load_pdf_preview(self, file_uuid: str) -> None:
        if self._show_pdf_runtime_unavailable():
            return

        size_bytes = safe_int(self._file_info.get("size"))
        if size_bytes is not None and size_bytes > self.PDF_PREVIEW_MAX_BYTES:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        try:
            # inline import: QtWebEngine is optional in some QGIS Qt5 builds; import lazily to avoid breaking plugin startup.
            from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView  # noqa: F401 - availability check
        except ImportError:
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_UNSUPPORTED)
            )
            return

        # Loads on a worker (2026-11-24); the view is built when the payload arrives.
        self._fetch_preview_in_background(file_uuid, self.PDF_PREVIEW_MAX_BYTES, self._apply_pdf_preview_payload)

    def _apply_pdf_preview_payload(self, payload: dict) -> None:
        # inline import: checked in _load_pdf_preview before the fetch started.
        from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView

        self._last_url = str(payload.get("url") or "").strip()
        if payload.get("truncated"):
            self._show_placeholder(
                self._lang.translate(TranslationKeys.TASK_FILES_PREVIEW_TOO_LARGE)
            )
            return

        content = payload.get("content") or b""
        if not content:
            self._show_failed()
            return

        temp_path = self._write_pdf_temp_file(content)
        if not temp_path:
            self._show_failed()
            return

        if self._load_pdf_webengine_preview(
            temp_path,
            webengine_settings_cls=QWebEngineSettings,
            webengine_view_cls=QWebEngineView,
        ):
            return

        self._cleanup_pdf_temp_file()
        self._show_failed()

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
        except Exception as exc:  # the view class is supplied by the caller
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="task_file_preview_webview_create_failed",
            )
            return False

        try:
            settings = web_view.settings()
        except (AttributeError, RuntimeError):
            settings = None

        if settings is not None:
            if hasattr(webengine_settings_cls, "PdfViewerEnabled"):
                try:
                    settings.setAttribute(webengine_settings_cls.PdfViewerEnabled, True)
                except (TypeError, RuntimeError):
                    pass

            if hasattr(webengine_settings_cls, "PluginsEnabled"):
                try:
                    settings.setAttribute(webengine_settings_cls.PluginsEnabled, True)
                except (TypeError, RuntimeError):
                    pass

        try:
            web_view.loadFinished.connect(self._handle_pdf_web_view_loaded)
        except Exception as exc:  # without it the preview never reports a failed load
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="task_file_preview_loadfinished_connect_failed",
            )

        self._web_view = web_view
        self._content_layout.addWidget(web_view, 1)

        try:
            web_view.setUrl(QUrl.fromLocalFile(temp_path))
        except (AttributeError, RuntimeError):
            try:
                web_view.load(QUrl.fromLocalFile(temp_path))
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="task_file_preview_pdf_load_failed",
                )
                self._release_web_view()
                self._clear_content()
                return False

        return True

    def _handle_pdf_web_view_loaded(self, ok: bool) -> None:
        if ok or not self.isVisible():
            return

        self._cleanup_pdf_temp_file()
        self._show_failed()

    def _write_pdf_temp_file(self, content: bytes) -> str:
        self._cleanup_pdf_temp_file()
        try:
            handle, path = create_external_temp_file(".pdf")
            self._pdf_temp_path = str(path or "")
            with handle:
                handle.write(content)
            return self._pdf_temp_path
        except OSError as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="task_file_preview_pdf_temp_write_failed",
            )
            remove_temp_file_quietly(self._pdf_temp_path)
            self._pdf_temp_path = ""
            return ""

    def _cleanup_pdf_temp_file(self) -> None:
        self._release_web_view()

        path = str(self._pdf_temp_path or "").strip()
        self._pdf_temp_path = ""
        if not path:
            return

        remove_temp_file_quietly(path)
