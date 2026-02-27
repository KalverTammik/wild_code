from __future__ import annotations

from ...ui.window_state.dialog_helpers import DialogHelpers


class SettingsUIController:
    @staticmethod
    def can_close(dialog) -> bool:
        from ...Logs.python_fail_logger import PythonFailLogger

        try:
            module_name = ""
            module_manager = getattr(dialog, "moduleManager", None)
            if module_manager is not None:
                module_name = module_manager.getActiveModuleName() or ""
            return bool(DialogHelpers.confirm_settings_navigation(module_name, dialog))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_close_guard_failed",
            )
            return False
