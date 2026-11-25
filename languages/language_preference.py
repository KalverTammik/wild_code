"""The plugin language follows the Kavitro account (`me { language }`); the last one is remembered locally."""
from typing import Optional

from ..Logs.python_fail_logger import PythonFailLogger
from .language_manager import get_current_language, normalize_language, set_current_language


def restore_saved_language(settings_service=None) -> str:
    """At plugin start: the language of the last signed-in account, Estonian when none is stored."""
    try:
        if settings_service is None:
            from ..utils.settings_service import SettingsService
            settings_service = SettingsService()
        return set_current_language(settings_service.language())
    except Exception as exc:  # a broken settings store must not stop the plugin from starting
        PythonFailLogger.log_exception(exc, module="auth", event="language_restore_failed")
        return get_current_language()


def apply_account_language(language, settings_service=None) -> Optional[str]:
    """Make the account language the plugin language and remember it; None when the server gave no usable one."""
    code = normalize_language(language)
    if code is None:
        return None
    set_current_language(code)
    try:
        if settings_service is None:
            from ..utils.settings_service import SettingsService
            settings_service = SettingsService()
        settings_service.language(code)
    except Exception as exc:  # remembering is a convenience; the language itself is already applied
        PythonFailLogger.log_exception(exc, module="auth", event="language_remember_failed")
    return code


def fetch_account_language(query_loader=None, api_client=None) -> Optional[str]:
    """Read the signed-in account's language from the server; None when it cannot be read."""
    try:
        if query_loader is None:
            from ..python.GraphQLQueryLoader import GraphQLQueryLoader
            query_loader = GraphQLQueryLoader()
        if api_client is None:
            from ..python.api_client import APIClient
            api_client = APIClient()
        from ..constants.module_names import Module
        query = query_loader.load_query_by_module(Module.USER.value, "me_language.graphql")
        data = api_client.send_query(query) or {}
        me = data.get("me") if isinstance(data, dict) else None
        return me.get("language") if isinstance(me, dict) else None
    except Exception as exc:  # the language is optional; a failed read must never fail the sign-in
        PythonFailLogger.log_exception(exc, module="auth", event="account_language_fetch_failed")
        return None


def adopt_account_language(query_loader=None, api_client=None, settings_service=None) -> Optional[str]:
    """After sign-in: fetch the account language and apply it."""
    return apply_account_language(fetch_account_language(query_loader, api_client), settings_service)
