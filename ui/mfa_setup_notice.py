"""Tells the user that the organisation requires two-factor authentication."""
from __future__ import annotations

from ..constants.module_icons import IconNames
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from .messages_helper import ModernMessageDialog
from ..utils.url_manager import OpenLink, loadWebpage


def show_mfa_setup_notice() -> None:
    """Warn that MFA must be turned on in the web app; the web app opens only when the user asks for it."""
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
