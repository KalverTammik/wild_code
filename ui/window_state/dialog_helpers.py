from __future__ import annotations
from typing import Any, Iterable, TypeVar

from PyQt5.QtCore import QTimer

from .DialogCoordinator import get_dialog_coordinator
from ...Logs.python_fail_logger import PythonFailLogger
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

    @staticmethod
    def resolve_safe_parent_window(
        window: Any,
        *,
        iface_obj: Any,
        module: str,
        qgis_main_error_event: str,
    ) -> Any:
        if window is None:
            return None

        try:
            qgis_main = iface_obj.mainWindow() if iface_obj is not None else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=module,
                event=qgis_main_error_event,
            )
            qgis_main = None

        if qgis_main is not None and window is qgis_main:
            return None

        return window

    @staticmethod
    def enter_map_selection_mode(
        *,
        iface_obj: Any,
        parent_window: Any = None,
        dialogs: Iterable[Any] | None = None,
    ) -> None:
        coordinator = get_dialog_coordinator(iface_obj)
        coordinator.enter_map_selection_mode(parent=parent_window, dialogs=dialogs)

    @staticmethod
    def exit_map_selection_mode(
        *,
        iface_obj: Any,
        parent_window: Any = None,
        dialogs: Iterable[Any] | None = None,
        bring_front: bool = True,
    ) -> None:
        coordinator = get_dialog_coordinator(iface_obj)
        coordinator.exit_map_selection_mode(
            parent=parent_window,
            dialogs=dialogs,
            bring_front=bring_front,
        )
