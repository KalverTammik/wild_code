from __future__ import annotations
from typing import Any, TypeVar

from PyQt5.QtCore import QTimer

from ...Logs.switch_logger import SwitchLogger
from ...modules.Settings.scroll_helper import SettingsScrollHelper
from ...utils.url_manager import Module

T = TypeVar("T")


class DialogHelpers:
    @staticmethod
    def open_folder_rule_dialog(lang_manager: Any, dialog: Any, dialog_class: Any, accepted_value: Any, current_value: T) -> T:
        dlg = dialog_class(lang_manager, dialog, initial_rule=current_value)
        result = dlg.exec_()
        if result == accepted_value:
            return dlg.get_rule()
        return current_value

    @staticmethod
    def confirm_settings_navigation(previous_module_name: str, dialog: Any) -> bool:
        previous_key = (previous_module_name or "").strip().lower()
        if previous_key != Module.SETTINGS.value:
            return True
        try:
            instance = dialog.moduleManager.getActiveModuleInstance(Module.SETTINGS.value)
            if instance is None:
                raise ValueError("Settings module instance not found.")
            return bool(instance.confirm_navigation_away(parent=dialog))
        except Exception as exc:
            SwitchLogger.log(
                "settings_confirm_navigation_failed",
                module=Module.SETTINGS.value,
                extra={"error": str(exc)},
            )
            raise

    @staticmethod
    def focus_settings_section(instance: Any, focus_module: str | None, dialog: Any = None) -> None:
        if not focus_module or instance is None:
            return
        try:
            QTimer.singleShot(
                0,
                lambda sm=instance, fm=focus_module: SettingsScrollHelper.scroll_to_module(
                    sm,
                    fm,
                ),
            )
        except Exception as exc:
            SwitchLogger.log(
                "settings_focus_failed",
                module=Module.SETTINGS.value,
                extra={"error": str(exc), "focus": focus_module},
            )
