"""What a task file is (MIME type, extension, name) and which preview it gets; plus the
small formatting helpers of the preview dialog."""
from __future__ import annotations

import mimetypes
import os
from typing import Optional

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


def preview_identity(*, file_info: Optional[dict] = None, local_file_path: str = "") -> tuple[str, str]:
    """(mime type, extension) in lower case; a local path wins over the API metadata."""
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


def preview_kind(mime_type: str, ext: str) -> str:
    """"pdf", "image", "text" or "unsupported"."""
    if mime_type in PDF_MIME_TYPES or ext in PDF_EXTENSIONS:
        return "pdf"
    if mime_type.startswith("image/") or ext in IMAGE_EXTENSIONS:
        return "image"
    if mime_type.startswith("text/") or mime_type in TEXT_MIME_TYPES or ext in TEXT_EXTENSIONS:
        return "text"
    return "unsupported"


def is_image(mime_type: str, ext: str) -> bool:
    return mime_type.startswith("image/") or ext in IMAGE_EXTENSIONS


def file_name(*, file_info: Optional[dict] = None, local_file_path: str = "") -> str:
    normalized_local_path = str(local_file_path or "").strip()
    if normalized_local_path:
        return os.path.basename(normalized_local_path) or normalized_local_path or "-"
    data = file_info if isinstance(file_info, dict) else {}
    return str(data.get("fileName") or data.get("uuid") or "-")


def decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def human_readable_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "–"
    try:
        value = float(size_bytes)
    except (TypeError, ValueError):
        return "–"
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"
