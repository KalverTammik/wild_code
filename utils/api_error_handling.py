from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from time import monotonic
from typing import Optional, Tuple, Union
from qgis.PyQt.QtCore import QCoreApplication, QObject, pyqtSignal, pyqtSlot
from ..Logs.python_fail_logger import PythonFailLogger


class ApiErrorKind(str, Enum):
    AUTH = "auth"
    MFA_SETUP_REQUIRED = "mfa_setup_required"
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
    _lock = RLock()

    @classmethod
    def should_show(cls, key: str, *, interval_s: float = 30.0) -> bool:
        now = monotonic()
        with cls._lock:
            last = cls._last_shown_at.get(key)
            if last is not None and (now - last) < float(interval_s):
                return False
            cls._last_shown_at[key] = now
            return True


class _MfaSetupNotificationBridge(QObject):
    showRequested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.showRequested.connect(self._show_notification)

    @pyqtSlot()
    def _show_notification(self) -> None:
        try:
            from ..constants.module_icons import IconNames
            from ..languages.language_manager import LanguageManager
            from ..languages.translation_keys import TranslationKeys
            from .messagesHelper import ModernMessageDialog
            from .url_manager import OpenLink, loadWebpage

            lang = LanguageManager()
            open_label = lang.translate(TranslationKeys.MFA_OPEN_WEB_APP)
            close_label = lang.translate(TranslationKeys.OK)
            choice = ModernMessageDialog.ask_choice_modern(
                lang.translate(TranslationKeys.WARNING),
                lang.translate(TranslationKeys.MFA_SETUP_REQUIRED),
                buttons=[open_label, close_label],
                default=open_label,
                cancel=close_label,
                icon_name=IconNames.WARNING,
            )
            if choice == open_label:
                loadWebpage.open_webpage(OpenLink().main)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=PythonFailLogger.LOG_MODULE_UI,
                event=PythonFailLogger.EVENT_MFA_NOTIFICATION_FAILED,
            )


class MfaSetupNotifier:
    """Show the MFA setup notice at most once per dedupe window."""

    _bridge: Optional[_MfaSetupNotificationBridge] = None
    _lock = RLock()
    _dedupe_key = "mfa_setup_required"

    @classmethod
    def _get_bridge(cls) -> Optional[_MfaSetupNotificationBridge]:
        app = QCoreApplication.instance()
        if app is None:
            return None
        with cls._lock:
            if cls._bridge is None:
                bridge = _MfaSetupNotificationBridge()
                if bridge.thread() != app.thread():
                    bridge.moveToThread(app.thread())
                cls._bridge = bridge
            return cls._bridge

    @classmethod
    def notify(cls) -> bool:
        try:
            bridge = cls._get_bridge()
            if bridge is None or not DedupeNotifier.should_show(cls._dedupe_key):
                return False
            bridge.showRequested.emit()
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=PythonFailLogger.LOG_MODULE_UI,
                event=PythonFailLogger.EVENT_MFA_NOTIFICATION_FAILED,
            )
            return False


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
