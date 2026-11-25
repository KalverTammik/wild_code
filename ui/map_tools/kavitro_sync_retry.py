"""Offer to send a layer change to Kavitro again when the first send failed.

The layer is saved before Kavitro is updated, so Kavitro never gets a shape the layer did not keep.
When the Kavitro update then fails, the two differ; the user can try again at once instead of
learning of it from a warning only.
"""
from __future__ import annotations

from typing import Callable, Optional

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..messages_helper import ModernMessageDialog

KavitroSync = Callable[[], tuple[bool, str]]


def run_kavitro_sync(sync: KavitroSync, *, log_module: str, extra: Optional[dict] = None) -> tuple[bool, str]:
    """Run one Kavitro update; an error is logged and reported as a failed update."""
    try:
        synced, detail = sync()
    except Exception as exc:  # called from Qt callbacks: nothing may escape; the layer save stands
        PythonFailLogger.log_exception(
            exc, module=log_module, event="kavitro_sync_failed", extra=dict(extra or {}),
        )
        return False, str(exc)
    return bool(synced), str(detail or "")


def offer_kavitro_sync_retry(
    sync: KavitroSync,
    *,
    failure_message: Callable[[str], str],
    title: str,
    log_module: str,
    first_detail: str = "",
    parent=None,
    extra: Optional[dict] = None,
    dialog_class=None,
) -> bool:
    """Ask after a failed Kavitro update whether to try again; True once an attempt succeeds.

    `failure_message(detail)` words the failure (first with `first_detail`, the detail of the update
    that already failed); the note that map and Kavitro differ is added here.
    Returns False when the user leaves it as it is. `dialog_class` is the caller's message dialog class.
    """
    dialogs = dialog_class or ModernMessageDialog
    lang = LanguageManager()
    retry = lang.translate(TranslationKeys.KAVITRO_SYNC_RETRY)
    keep = lang.translate(TranslationKeys.KAVITRO_SYNC_KEEP)
    note = lang.translate(TranslationKeys.KAVITRO_SYNC_DIFFERS_NOTE)
    detail = str(first_detail or "")
    attempt = 0
    while True:
        message = failure_message(detail)
        choice = dialogs.ask_choice_modern(
            title,
            f"{message}\n\n{note}" if message else note,
            buttons=[retry, keep],
            parent=parent,
            default=retry,
            cancel=keep,
        )
        if choice != retry:
            PythonFailLogger.log(
                "kavitro_sync_left_different", module=log_module, extra={**(extra or {}), "attempts": attempt},
            )
            return False
        attempt += 1
        synced, detail = run_kavitro_sync(sync, log_module=log_module, extra=extra)
        if synced:
            PythonFailLogger.log(
                "kavitro_sync_retry_succeeded", module=log_module, extra={**(extra or {}), "attempts": attempt},
            )
            return True
