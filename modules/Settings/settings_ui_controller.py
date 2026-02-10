from __future__ import annotations


class SettingsUIController:
    @staticmethod
    def can_close(dialog) -> bool:
        from ...Logs.python_fail_logger import PythonFailLogger
        from ...utils.url_manager import Module

        try:
            settings = getattr(dialog, "settingsModule", None)
            if settings is None and getattr(dialog, "moduleManager", None) is not None:
                try:
                    settings = dialog.moduleManager.getActiveModuleInstance(Module.SETTINGS.name)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=Module.SETTINGS.value,
                        event="settings_close_guard_resolve_failed",
                    )
                    settings = None

            if settings and settings.has_unsaved_changes():
                return bool(settings.confirm_navigation_away(parent=dialog))
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_close_guard_failed",
            )
            return False
