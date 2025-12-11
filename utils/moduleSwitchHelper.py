from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt5.QtCore import QTimer

from .url_manager import Module
from ..modules.Settings.scroll_helper import SettingsScrollHelper
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsHelpers
from ..module_manager import ModuleManager

if TYPE_CHECKING:
    from ..dialog import PluginDialog


class ModuleSwitchHelper:
    @staticmethod
    def switch_module(
        module_name: str,
        *,
        dialog: "PluginDialog | None" = None,
        focus_module: str | None = None,
    ) -> None:
        """Switch the active module using an explicit module name and dialog."""
        import sys

        if not module_name:
            raise TypeError("ModuleSwitchHelper.switch_module requires a module_name.")

        dlg = dialog
        if dlg is None:
            try:
                from ..dialog import PluginDialog  # Local import to avoid circular dependency at module load

                dlg = PluginDialog.get_instance()
            except Exception:
                dlg = None

        if dlg is None:
            raise RuntimeError("ModuleSwitchHelper.switch_module requires a dialog instance (pass one or ensure PluginDialog.get_instance() returns one).")

        module_manager = ModuleManager()
        previous_module_name = module_manager.getActiveModuleName()
        normalized_name = module_name.lower()

        if not SettingsHelpers._confirm_unsaved_settings(previous_module_name):
            return

        try:
            module_manager.activateModule(module_name)
            instance = module_manager.getActiveModuleInstance(module_name)
            if instance is None:
                module_manager.activateModule(Module.HOME.name)
                raise ValueError(f"Failed to get instance of module '{module_name}' after activation.")

            if normalized_name == Module.PROPERTY.value:
                try:
                    instance.property_selected_from_map.disconnect(dlg.window_manager._minimize_window)
                except Exception:
                    pass
                try:
                    instance.property_selection_completed.disconnect(dlg.window_manager._restore_window)
                except Exception:
                    pass
                instance.property_selected_from_map.connect(dlg.window_manager._minimize_window)
                instance.property_selection_completed.connect(dlg.window_manager._restore_window)

            widget = instance.get_widget()
            if dlg.moduleStack.indexOf(widget) == -1:
                dlg.moduleStack.addWidget(widget)
            dlg.moduleStack.setCurrentWidget(widget)

            display_title = module_name.lower()
            dlg.header_widget.set_title(dlg.lang_manager.translate(display_title))

            dlg.sidebar.setActiveModuleOnSidebarButton(module_name)
            dlg.moduleStack.update()
            dlg.moduleStack.repaint()

            if module_name == Module.SETTINGS.name:
                dlg.settingsModule = instance
                if focus_module:
                    QTimer.singleShot(
                        0,
                        lambda sm=dlg.settingsModule: SettingsScrollHelper.scroll_to_module(
                            sm,
                            focus_module,
                        ),
                    )


        except Exception:
            if previous_module_name:
                dlg.sidebar.setActiveModuleOnSidebarButton(previous_module_name)
            import traceback
            traceback.print_exc(file=sys.stderr)
