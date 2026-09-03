"""Pure helpers for validating untrusted values before OS-level actions."""

from __future__ import annotations

from dataclasses import dataclass
import ntpath
import os
import re
import unicodedata
from urllib.parse import unquote, urlsplit


ALLOWED_EXTERNAL_FILE_EXTENSIONS = frozenset(
    {
        "asice",
        "bdoc",
        "bmp",
        "cad",
        "csv",
        "ddoc",
        "dgn",
        "doc",
        "docx",
        "dwg",
        "dxf",
        "gif",
        "jpeg",
        "jpg",
        "mov",
        "mp4",
        "ods",
        "odt",
        "pdf",
        "png",
        "rtf",
        "txt",
        "webp",
        "xls",
        "xlsx",
        "zip",
    }
)

_EXTENSION_ALIASES = {
    "jpeg": "jpg",
}
_SIMPLE_EXTENSION_RE = re.compile(r"^[a-z0-9]{1,12}$")
_INVALID_WINDOWS_PATH_COMPONENT_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_REPEATED_UNDERSCORE_RE = re.compile(r"_+")
_WINDOWS_RESERVED_PATH_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
)
DEFAULT_PATH_COMPONENT_MAX_LENGTH = 120

DESCRIPTION_LINK_WEB = "web"
DESCRIPTION_LINK_LOCAL_PATH = "local_path"
DESCRIPTION_LINK_NETWORK_PATH = "network_path"
DESCRIPTION_LINK_BLOCKED = "blocked"

_WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_WINDOWS_DEVICE_PATH_PREFIXES = ("\\\\?\\", "\\\\.\\", "//?/", "//./")
_WINDOWS_DRIVE_REMOTE = 4


@dataclass(frozen=True)
class DescriptionLinkTarget:
    """A description link classified without touching its filesystem target."""

    kind: str
    target: str = ""
    display: str = ""
    scheme: str = ""
    host: str = ""
    reason: str = ""


def windows_drive_type(path: object) -> int:
    """Return the Win32 drive type for an absolute drive path without probing a file."""

    text = str(path or "").strip()
    if os.name != "nt" or not _WINDOWS_ABSOLUTE_PATH_RE.match(text):
        return 0

    try:
        import ctypes

        root = f"{text[0].upper()}:\\"
        return int(ctypes.windll.kernel32.GetDriveTypeW(root))  # type: ignore[attr-defined]
    except Exception:
        return 0


def windows_mapped_drive_remote_name(path: object) -> str:
    """Return a mapped drive's UNC root without accessing the remote filesystem."""

    text = str(path or "").strip()
    if os.name != "nt" or not _WINDOWS_ABSOLUTE_PATH_RE.match(text):
        return ""

    try:
        import ctypes
        from ctypes import wintypes

        drive = f"{text[0].upper()}:"
        size = wintypes.DWORD(2048)
        buffer = ctypes.create_unicode_buffer(size.value)
        result = ctypes.windll.mpr.WNetGetConnectionW(  # type: ignore[attr-defined]
            drive,
            buffer,
            ctypes.byref(size),
        )
        return str(buffer.value or "").strip() if int(result) == 0 else ""
    except Exception:
        return ""


def classify_description_link(value: object) -> DescriptionLinkTarget:
    """Classify an untrusted description href without filesystem access.

    Raw UNC paths, hosted ``file://`` URLs and mapped Windows drives are marked
    as network targets before callers perform ``exists``/``isfile`` checks.
    Relative paths, device paths and schemes other than http/https/file are
    rejected.
    """

    text = str(value or "").strip()
    if not text:
        return _blocked_description_link(text, "empty")
    if _contains_control_characters(text):
        return _blocked_description_link(text, "control_characters")

    lowered = text.casefold()
    if lowered.startswith(tuple(prefix.casefold() for prefix in _WINDOWS_DEVICE_PATH_PREFIXES)):
        return _blocked_description_link(text, "device_path")

    if text.startswith(("\\\\", "//")):
        return _classify_unc_path(text)

    if _WINDOWS_ABSOLUTE_PATH_RE.match(text):
        normalized = ntpath.normpath(text.replace("/", "\\"))
        if windows_drive_type(normalized) == _WINDOWS_DRIVE_REMOTE:
            remote_root = windows_mapped_drive_remote_name(normalized)
            return DescriptionLinkTarget(
                kind=DESCRIPTION_LINK_NETWORK_PATH,
                target=normalized,
                display=normalized,
                scheme="file",
                host=_unc_server_name(remote_root) or normalized[:2].upper(),
            )
        return DescriptionLinkTarget(
            kind=DESCRIPTION_LINK_LOCAL_PATH,
            target=normalized,
            display=normalized,
            scheme="file",
        )

    try:
        parsed = urlsplit(text)
    except ValueError:
        return _blocked_description_link(text, "invalid_url")

    scheme = str(parsed.scheme or "").casefold()
    if scheme in {"http", "https"}:
        try:
            host = str(parsed.hostname or "").strip()
            parsed.port
        except ValueError:
            return _blocked_description_link(text, "invalid_url")
        if not host or not parsed.netloc:
            return _blocked_description_link(text, "missing_host")
        return DescriptionLinkTarget(
            kind=DESCRIPTION_LINK_WEB,
            target=text,
            display=text,
            scheme=scheme,
            host=host,
        )

    if scheme == "file":
        return _classify_file_url(text, parsed)

    if scheme:
        return _blocked_description_link(text, "unsupported_scheme", scheme=scheme)

    if os.name != "nt" and os.path.isabs(text):
        normalized = os.path.normpath(text)
        return DescriptionLinkTarget(
            kind=DESCRIPTION_LINK_LOCAL_PATH,
            target=normalized,
            display=normalized,
            scheme="file",
        )

    return _blocked_description_link(text, "relative_path")


def _classify_file_url(text: str, parsed) -> DescriptionLinkTarget:
    if parsed.query or parsed.fragment:
        return _blocked_description_link(text, "file_url_components", scheme="file")

    authority = unquote(str(parsed.netloc or "")).strip()
    path = unquote(str(parsed.path or ""))
    if _contains_control_characters(authority) or _contains_control_characters(path):
        return _blocked_description_link(text, "control_characters", scheme="file")

    if authority and authority.casefold() != "localhost":
        if any(marker in authority for marker in ("@", ":", "\\", "/")):
            return _blocked_description_link(text, "invalid_network_host", scheme="file")
        network_path = path.replace("/", "\\")
        return _classify_unc_path(
            f"\\\\{authority}{network_path}",
            original=text,
        )

    local_path = path
    if os.name == "nt":
        local_path = local_path.replace("/", "\\")
        if re.match(r"^\\[a-zA-Z]:\\", local_path):
            local_path = local_path[1:]
        if not _WINDOWS_ABSOLUTE_PATH_RE.match(local_path):
            return _blocked_description_link(text, "relative_path", scheme="file")
        normalized = ntpath.normpath(local_path)
        if windows_drive_type(normalized) == _WINDOWS_DRIVE_REMOTE:
            remote_root = windows_mapped_drive_remote_name(normalized)
            return DescriptionLinkTarget(
                kind=DESCRIPTION_LINK_NETWORK_PATH,
                target=normalized,
                display=normalized,
                scheme="file",
                host=_unc_server_name(remote_root) or normalized[:2].upper(),
            )
    else:
        if not os.path.isabs(local_path):
            return _blocked_description_link(text, "relative_path", scheme="file")
        normalized = os.path.normpath(local_path)

    return DescriptionLinkTarget(
        kind=DESCRIPTION_LINK_LOCAL_PATH,
        target=normalized,
        display=normalized,
        scheme="file",
    )


def _classify_unc_path(path: str, *, original: str = "") -> DescriptionLinkTarget:
    text = str(path or "").strip()
    lowered = text.casefold()
    if lowered.startswith(tuple(prefix.casefold() for prefix in _WINDOWS_DEVICE_PATH_PREFIXES)):
        return _blocked_description_link(original or text, "device_path", scheme="file")

    normalized = ntpath.normpath(text.replace("/", "\\"))
    components = [part for part in normalized.lstrip("\\").split("\\") if part]
    if len(components) < 2 or components[0] in {".", "?"}:
        return _blocked_description_link(original or text, "invalid_network_path", scheme="file")
    return DescriptionLinkTarget(
        kind=DESCRIPTION_LINK_NETWORK_PATH,
        target=normalized,
        display=normalized,
        scheme="file",
        host=components[0],
    )


def _unc_server_name(path: object) -> str:
    text = str(path or "").strip().replace("/", "\\")
    if not text.startswith("\\\\"):
        return ""
    components = [part for part in text.lstrip("\\").split("\\") if part]
    return components[0] if components else ""


def _contains_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _blocked_description_link(
    value: object,
    reason: str,
    *,
    scheme: str = "",
) -> DescriptionLinkTarget:
    text = str(value or "").strip()
    return DescriptionLinkTarget(
        kind=DESCRIPTION_LINK_BLOCKED,
        display=text,
        scheme=str(scheme or "").casefold(),
        reason=reason,
    )


def normalize_file_extension(value: object) -> str:
    """Return a simple lowercase extension or an empty string when malformed."""

    text = str(value or "").strip().lower()
    if text.startswith("."):
        text = text[1:]
    if not text or not _SIMPLE_EXTENSION_RE.fullmatch(text):
        return ""
    return text


def file_name_extension(file_name: object) -> str:
    """Extract a simple extension after discarding any supplied path components."""

    leaf = re.split(r"[\\/]", str(file_name or "").strip())[-1]
    if not leaf or leaf in {".", ".."} or "." not in leaf:
        return ""
    return normalize_file_extension(leaf.rsplit(".", 1)[-1])


def resolve_allowed_external_extension(
    *,
    api_extension: object = "",
    file_name: object = "",
    local_file_path: object = "",
) -> str:
    """Resolve an allowlisted suffix for handing a file to the OS.

    API metadata is treated as untrusted. When both ``ext`` and ``fileName``
    provide an extension, they must agree (common aliases such as jpg/jpeg are
    considered equivalent). Local files are decided solely by their real path.
    """

    local_path = str(local_file_path or "").strip()
    if local_path:
        local_extension = file_name_extension(local_path)
        return local_extension if local_extension in ALLOWED_EXTERNAL_FILE_EXTENSIONS else ""

    raw_api_extension = str(api_extension or "").strip()
    normalized_api_extension = normalize_file_extension(raw_api_extension)
    if raw_api_extension and not normalized_api_extension:
        return ""

    normalized_name_extension = file_name_extension(file_name)
    if normalized_api_extension and normalized_name_extension:
        api_canonical = _EXTENSION_ALIASES.get(normalized_api_extension, normalized_api_extension)
        name_canonical = _EXTENSION_ALIASES.get(normalized_name_extension, normalized_name_extension)
        if api_canonical != name_canonical:
            return ""

    selected = normalized_api_extension or normalized_name_extension
    return selected if selected in ALLOWED_EXTERNAL_FILE_EXTENSIONS else ""


def sanitize_path_component(
    value: object,
    *,
    fallback: object = "",
    max_length: int = DEFAULT_PATH_COMPONENT_MAX_LENGTH,
) -> str:
    """Return one Windows-safe path component without directory semantics."""

    try:
        length_limit = max(1, min(int(max_length), 240))
    except (TypeError, ValueError):
        length_limit = DEFAULT_PATH_COMPONENT_MAX_LENGTH

    def _clean(candidate: object) -> str:
        text = unicodedata.normalize("NFC", str(candidate or ""))
        text = re.sub(r"\s+", " ", text).strip(" .")
        text = _INVALID_WINDOWS_PATH_COMPONENT_RE.sub("_", text)
        text = _REPEATED_UNDERSCORE_RE.sub("_", text).strip(" .")
        if not text:
            return ""

        base_name = text.split(".", 1)[0].casefold()
        if base_name in _WINDOWS_RESERVED_PATH_NAMES:
            text = f"_{text}"

        return text[:length_limit].rstrip(" .")

    return _clean(value) or _clean(fallback)


def resolve_direct_child_path(target_root: object, folder_component: object) -> str:
    """Resolve an already-sanitized component directly below ``target_root``.

    Returns an empty string if the component changes during sanitization or the
    resolved candidate is not the root's immediate child.
    """

    root_text = str(target_root or "").strip()
    component = str(folder_component or "").strip()
    if not root_text or not component:
        return ""
    if sanitize_path_component(component) != component:
        return ""

    root_path = os.path.realpath(os.path.abspath(root_text))
    candidate = os.path.realpath(os.path.join(root_path, component))
    if os.path.normcase(os.path.dirname(candidate)) != os.path.normcase(root_path):
        return ""
    return candidate


def is_same_or_descendant_path(path: object, parent: object) -> bool:
    """Return whether ``path`` resolves to ``parent`` or below it."""

    path_text = str(path or "").strip()
    parent_text = str(parent or "").strip()
    if not path_text or not parent_text:
        return False

    resolved_path = os.path.normcase(os.path.realpath(os.path.abspath(path_text)))
    resolved_parent = os.path.normcase(os.path.realpath(os.path.abspath(parent_text)))
    try:
        return os.path.commonpath((resolved_path, resolved_parent)) == resolved_parent
    except ValueError:
        return False
