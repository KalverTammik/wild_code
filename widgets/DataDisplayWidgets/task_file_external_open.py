"""Opening a task file in the operating system's default application, after the user
confirmed it. A remote file is first downloaded into the plugin's own temp folder.

The download is meant to run on a background worker (see TaskFilePreviewDialog): it
reports progress through a callback and stops between chunks when its cancel event is set.

Files in the temp folder are handed to other applications, which may still have them open,
so they are never deleted right away. ``cleanup_external_temp_files`` removes the ones
older than ``EXTERNAL_TEMP_MAX_AGE_SECONDS``; it runs before every new download, when a
preview dialog closes and when the plugin is unloaded. A file another program still keeps
locked is skipped and logged, and removed on a later run.
"""
from __future__ import annotations

import os
import tempfile
import threading
import time
from typing import Callable, Optional

import requests
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...utils.security_boundaries import resolve_allowed_external_extension

EXTERNAL_TEMP_FOLDER_NAME = "Kavitro_files"
# Only files with this prefix are ever removed from the folder.
EXTERNAL_TEMP_PREFIX = "kavitro_"
# How long an external application gets to read a downloaded file before it may be removed.
EXTERNAL_TEMP_MAX_AGE_SECONDS = 15 * 60
DOWNLOAD_CHUNK_BYTES = 65536
# (connect, read) timeouts; the read timeout is per chunk, the whole download has none,
# because it runs in the background and the user can cancel it.
DOWNLOAD_TIMEOUT = (15, 60)

ProgressCallback = Callable[[int, Optional[int]], None]


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
    """Synchronous variant. A remote file is downloaded in the calling thread, so GUI code
    opens remote files through a background worker instead (TaskFilePreviewDialog)."""
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


def external_temp_folder() -> str:
    return os.path.join(tempfile.gettempdir(), EXTERNAL_TEMP_FOLDER_NAME)


def create_external_temp_file(suffix: str):
    """Return ``(binary handle, path)`` of a new empty file in the plugin's temp folder."""
    folder = external_temp_folder()
    os.makedirs(folder, exist_ok=True)
    descriptor, path = tempfile.mkstemp(prefix=EXTERNAL_TEMP_PREFIX, suffix=suffix, dir=folder)
    return os.fdopen(descriptor, "wb"), path


def remove_temp_file_quietly(path: str) -> bool:
    """Remove one file now; a file still in use is left for the age-based cleanup."""
    normalized_path = str(path or "").strip()
    if not normalized_path:
        return True
    try:
        if os.path.exists(normalized_path):
            os.remove(normalized_path)
        return True
    except OSError as exc:  # still open in another program
        PythonFailLogger.log(
            "task_file_temp_file_locked",
            module="ui",
            extra={"error_type": type(exc).__name__, "name": os.path.basename(normalized_path)},
        )
        return False


def cleanup_external_temp_files(
    *,
    max_age_seconds: float = EXTERNAL_TEMP_MAX_AGE_SECONDS,
    now: Optional[float] = None,
) -> int:
    """Remove the plugin's temp files older than ``max_age_seconds``; return how many went.

    Never raises: it also runs from the plugin unload hook.
    """
    removed = 0
    try:
        folder = external_temp_folder()
        if not os.path.isdir(folder):
            return 0
        current_time = time.time() if now is None else float(now)
        with os.scandir(folder) as entries:
            candidates = [
                entry for entry in entries
                if entry.name.startswith(EXTERNAL_TEMP_PREFIX) and entry.is_file(follow_symlinks=False)
            ]
        for entry in candidates:
            try:
                modified = entry.stat(follow_symlinks=False).st_mtime
            except OSError:  # removed meanwhile
                continue
            if current_time - modified < max_age_seconds:
                continue
            if remove_temp_file_quietly(entry.path):
                removed += 1
    except Exception as exc:  # noqa: BLE001 - cleanup must never break the caller
        PythonFailLogger.log_exception(exc, module="ui", event="task_file_temp_cleanup_failed")
    return removed


class DownloadCancelled(Exception):
    """The user cancelled the download; the partial file is already removed."""


def materialize_remote_file_to_temp(
    file_info: Optional[dict],
    *,
    allowed_extension: str = "",
    cancel_event: Optional[threading.Event] = None,
    progress: Optional[ProgressCallback] = None,
) -> str:
    """Download the file into the plugin's temp folder and return its path ("" on failure).

    ``progress(done_bytes, total_bytes_or_None)`` is called from the downloading thread
    and must not touch widgets. When ``cancel_event`` is set, the download stops at the
    next chunk, the partial file is removed and "" is returned.
    """
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

    def cancelled() -> bool:
        return bool(cancel_event is not None and cancel_event.is_set())

    if cancelled():
        return ""

    url = APIModuleActions.create_file_download_link(file_uuid) or ""
    if not url or cancelled():
        return ""

    cleanup_external_temp_files()

    temp_path = ""
    try:
        handle, temp_path = create_external_temp_file(f".{resolved_extension}")
        with handle:
            with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as response:
                response.raise_for_status()
                total = _content_length(response, data)
                done = 0
                if progress is not None:
                    progress(done, total)
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_BYTES):
                    if cancelled():
                        raise DownloadCancelled()
                    if chunk:
                        handle.write(chunk)
                        done += len(chunk)
                        if progress is not None:
                            progress(done, total)
    except DownloadCancelled:
        remove_temp_file_quietly(temp_path)
        return ""
    except OSError as exc:  # includes requests.RequestException
        # The download link may carry a signature and the request error names the URL,
        # so only the error type is logged.
        PythonFailLogger.log(
            "task_file_preview_download_failed",
            module="ui",
            extra={"error_type": type(exc).__name__, "uuid": file_uuid},
        )
        remove_temp_file_quietly(temp_path)
        return ""

    if cancelled():
        remove_temp_file_quietly(temp_path)
        return ""
    if not temp_path or not os.path.exists(temp_path):
        return ""
    return temp_path


def _content_length(response, file_info: dict) -> Optional[int]:
    headers = getattr(response, "headers", None)
    raw = None
    try:
        raw = headers.get("Content-Length") if headers is not None else None
    except AttributeError:
        raw = None
    for value in (raw, file_info.get("size")):
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            return number
    return None
