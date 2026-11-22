"""Opening a task file in the operating system's default application, after the user
confirmed it; a remote file is first downloaded to a temp file."""
from __future__ import annotations

import os
import tempfile
from typing import Optional

import requests
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...utils.security_boundaries import resolve_allowed_external_extension

# Downloaded files handed to other applications; they may still be open there, so they
# are not deleted, only forgotten once gone.
EXTERNAL_TEMP_FILES: set[str] = set()


def embedded_pdf_runtime_support() -> tuple[bool, dict[str, str]]:
    qt_version = "unknown"
    pyqt_version = "unknown"

    try:
        from qgis.PyQt.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

        qt_version = str(QT_VERSION_STR or "unknown")
        pyqt_version = str(PYQT_VERSION_STR or "unknown")
    except ImportError:
        pass

    try:
        from qgis.PyQt.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView  # noqa: F401

        return bool(hasattr(QWebEngineSettings, "PdfViewerEnabled")), {
            "qt": qt_version,
            "pyqt": pyqt_version,
        }
    except ImportError:  # no QtWebEngine in this QGIS build
        return False, {
            "qt": qt_version,
            "pyqt": pyqt_version,
        }


def open_in_default_application(
    *,
    file_info: Optional[dict] = None,
    local_file_path: str = "",
    user_confirmed: bool = False,
) -> bool:
    if not user_confirmed:
        return False

    normalized_local_path = str(local_file_path or "").strip()
    data = file_info if isinstance(file_info, dict) else {}
    allowed_extension = resolve_allowed_external_extension(
        api_extension=data.get("ext"),
        file_name=data.get("fileName"),
        local_file_path=normalized_local_path,
    )
    if not allowed_extension:
        return False

    if normalized_local_path:
        return open_local_path(normalized_local_path)

    temp_path = materialize_remote_file_to_temp(data, allowed_extension=allowed_extension)
    if not temp_path:
        return False
    return open_local_path(temp_path)


def open_local_path(path: str) -> bool:
    normalized_path = str(path or "").strip()
    if not normalized_path or not os.path.exists(normalized_path):
        return False

    try:
        if hasattr(os, "startfile"):
            os.startfile(normalized_path)  # type: ignore[attr-defined]
            return True
    except OSError:  # no associated application: fall back to the desktop services
        pass

    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path)))


def materialize_remote_file_to_temp(file_info: Optional[dict], *, allowed_extension: str = "") -> str:
    data = file_info if isinstance(file_info, dict) else {}
    file_uuid = str(data.get("uuid") or "").strip()
    if not file_uuid:
        return ""

    resolved_extension = resolve_allowed_external_extension(
        api_extension=data.get("ext"),
        file_name=data.get("fileName"),
    )
    if not resolved_extension or resolved_extension != allowed_extension:
        return ""

    url = APIModuleActions.create_file_download_link(file_uuid) or ""
    if not url:
        return ""

    suffix = f".{resolved_extension}"

    cleanup_missing_temp_paths()

    temp_path = ""
    try:
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = str(handle.name or "")
        with handle:
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        handle.write(chunk)
    except OSError as exc:  # includes requests.RequestException
        # The download link may carry a signature and the request error names the URL,
        # so only the error type is logged.
        PythonFailLogger.log(
            "task_file_preview_download_failed",
            module="ui",
            extra={"error_type": type(exc).__name__, "uuid": file_uuid},
        )
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:  # best-effort removal of a half-written temp file
            pass
        return ""

    if not temp_path or not os.path.exists(temp_path):
        return ""

    EXTERNAL_TEMP_FILES.add(temp_path)
    return temp_path


def cleanup_missing_temp_paths() -> None:
    for path in list(EXTERNAL_TEMP_FILES):
        if not str(path or "").strip() or not os.path.exists(path):
            EXTERNAL_TEMP_FILES.discard(path)
