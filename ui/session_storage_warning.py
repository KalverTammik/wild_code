"""Tells the user when a login could not be stored safely."""
from __future__ import annotations

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.SessionManager import (
    SESSION_STORAGE_CLEANUP_FAILED,
    SESSION_STORAGE_MEMORY_ONLY,
    SESSION_STORAGE_MIGRATION_PENDING,
    SessionManager,
)
from ..utils.messagesHelper import ModernMessageDialog

_MESSAGE_KEYS = {
    SESSION_STORAGE_MEMORY_ONLY: TranslationKeys.SESSION_STORAGE_MEMORY_ONLY,
    SESSION_STORAGE_MIGRATION_PENDING: TranslationKeys.SESSION_STORAGE_MIGRATION_PENDING,
    SESSION_STORAGE_CLEANUP_FAILED: TranslationKeys.SESSION_STORAGE_CLEANUP_FAILED,
}


def show_storage_warning(status: str, parent=None, lang_manager=None) -> None:
    message_key = _MESSAGE_KEYS.get(status)
    if message_key is None:
        return
    manager = lang_manager if lang_manager is not None else LanguageManager()
    ModernMessageDialog.show_warning(
        manager.translate(TranslationKeys.SESSION_STORAGE_WARNING_TITLE),
        manager.translate(message_key),
        parent=parent,
    )


def show_pending_storage_warning(parent=None, lang_manager=None) -> None:
    status = SessionManager.take_pending_storage_warning()
    if status:
        show_storage_warning(status, parent=parent, lang_manager=lang_manager)
