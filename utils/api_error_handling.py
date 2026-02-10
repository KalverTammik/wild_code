from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Optional, Tuple, Union
from ..Logs.python_fail_logger import PythonFailLogger


class ApiErrorKind(str, Enum):
    AUTH = "auth"
    NETWORK = "network"
    SERVER = "server"
    GRAPHQL = "graphql"
    UNKNOWN = "unknown"


_TAG_PREFIX = "[WC-API]"


def tag_message(kind: ApiErrorKind, message: str) -> str:
    cleaned = (message or "").strip()
    return f"{_TAG_PREFIX}[{kind.value}] {cleaned}".strip()


def parse_tagged_message(message: Union[str, Exception]) -> Tuple[ApiErrorKind, str]:
    text = str(message or "").strip()
    if not text:
        return ApiErrorKind.UNKNOWN, ""

    if not text.startswith(_TAG_PREFIX):
        # Best-effort inference from common requests/urllib3 phrasing
        lowered = text.lower()
        if "unauthenticated" in lowered or "session expired" in lowered:
            return ApiErrorKind.AUTH, text
        if any(
            token in lowered
            for token in (
                "nameresolutionerror",
                "max retries exceeded",
                "failed to establish a new connection",
                "temporary failure in name resolution",
                "connection refused",
                "connection aborted",
                "read timed out",
                "connect timeout",
                "timeout",
                "network is unreachable",
            )
        ):
            return ApiErrorKind.NETWORK, text
        if "http 5" in lowered or "bad gateway" in lowered or "service unavailable" in lowered:
            return ApiErrorKind.SERVER, text
        return ApiErrorKind.UNKNOWN, text

    # Tagged format: "[WC-API][kind] message"
    try:
        after_prefix = text[len(_TAG_PREFIX) :].lstrip()
        if after_prefix.startswith("[") and "]" in after_prefix:
            kind_token = after_prefix[1 : after_prefix.index("]")].strip().lower()
            rest = after_prefix[after_prefix.index("]") + 1 :].lstrip()
            kind = ApiErrorKind(kind_token) if kind_token in ApiErrorKind._value2member_map_ else ApiErrorKind.UNKNOWN
            return kind, rest
    except Exception as exc:
        PythonFailLogger.log_exception(
            exc,
            module="api",
            event="parse_tagged_message_failed",
        )

    return ApiErrorKind.UNKNOWN, text


def summarize_connection_error(raw: str) -> str:
    """Turn long requests/urllib3 messages into a short, user-facing hint."""
    text = (raw or "").strip()
    lowered = text.lower()

    if "nameresolutionerror" in lowered or "temporary failure in name resolution" in lowered:
        return "Cannot resolve server name (DNS)"
    if "connection refused" in lowered:
        return "Connection refused"
    if "read timed out" in lowered:
        return "Request timed out"
    if "connect timeout" in lowered or "connection timed out" in lowered:
        return "Connection timed out"
    if "network is unreachable" in lowered:
        return "Network is unreachable"
    if "max retries exceeded" in lowered:
        return "Connection failed (max retries exceeded)"

    # Fallback: keep it short
    return text[:160] if len(text) > 160 else text


class DedupeNotifier:
    """Process-wide deduping for UI warnings/errors."""

    _last_shown_at: dict[str, float] = {}

    @classmethod
    def should_show(cls, key: str, *, interval_s: float = 30.0) -> bool:
        now = monotonic()
        last = cls._last_shown_at.get(key, 0.0)
        if (now - last) < float(interval_s):
            return False
        cls._last_shown_at[key] = now
        return True


@dataclass(frozen=True)
class ApiErrorDisplay:
    kind: ApiErrorKind
    message: str
    notify_title: Optional[str] = None
    notify_message: Optional[str] = None
    notify_key: Optional[str] = None


def to_display(kind: ApiErrorKind, message: str) -> ApiErrorDisplay:
    msg = (message or "").strip()
    if kind == ApiErrorKind.NETWORK:
        title = "Server unreachable"
        return ApiErrorDisplay(
            kind=kind,
            message=msg,
            notify_title=title,
            notify_message=msg or "Network error",
            notify_key=f"network:{msg[:60]}",
        )
    if kind == ApiErrorKind.SERVER:
        title = "Server error"
        return ApiErrorDisplay(
            kind=kind,
            message=msg,
            notify_title=title,
            notify_message=msg or "Server error",
            notify_key=f"server:{msg[:60]}",
        )
    return ApiErrorDisplay(kind=kind, message=msg)
