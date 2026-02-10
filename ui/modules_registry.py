from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..module_manager import ModuleManager
    from ..languages.language_manager import LanguageManager
    from ..widgets.sidebar import Sidebar


class DialogProtocol(Protocol):
    lang_manager: "LanguageManager"
    sidebar: "Sidebar"


class ModulesRegistry:
    @staticmethod
    def register_all(module_manager: "ModuleManager", dialog: "DialogProtocol") -> None:
        """Wire module registrations onto the provided ModuleManager instance."""
        from functools import partial
        from PyQt5.QtWidgets import QDialog

        from ..constants.file_paths import QssPaths
        from ..languages.translation_keys import DialogLabels
        from ..modules.Settings.setting_keys import SettingDialogPlaceholders
        from ..modules.Settings.SettingsUI import SettingsModule
        from ..modules.Property.PropertyUI import PropertyModule
        from ..modules.projects.ProjectsUi import ProjectsModule
        from ..modules.projects.FolderNamingRuleDialog import FolderNamingRuleDialog
        from ..modules.contract.ContractUi import ContractsModule
        from ..modules.coordination.CoordinationModule import CoordinationModule
        from ..modules.signaltest.SignalTestModule import SignalTestModule
        from ..utils.url_manager import Module
        from .window_state.dialog_helpers import DialogHelpers
        from ..utils.Folders.foldersHelpers import FolderHelpers
        from ..widgets.WelcomePage import WelcomePage
        from ..widgets.theme_manager import ThemeManager

        qss_modular = list(ThemeManager.module_bundle())
        qss_signaltest = list(ThemeManager.module_bundle([QssPaths.SETUP_CARD]))

        def pick_folder(_module_key: str, _key: str, current_value: str):
            return FolderHelpers.select_folder_path(dialog, start_path=current_value)
        open_folder_rule = partial(
            DialogHelpers.open_folder_rule_dialog,
            dialog.lang_manager,
            dialog,
            FolderNamingRuleDialog,
            QDialog.Accepted,
        )

        module_manager.registerModule(
            WelcomePage,
            Module.HOME.name,
            lang_manager=dialog.lang_manager,
        )
        module_manager.registerModule(
            SettingsModule,
            Module.SETTINGS.name,
            sidebar_main_item=False,
        )
        module_manager.registerModule(
            PropertyModule,
            Module.PROPERTY.name,
            qss_files=qss_modular,
            lang_manager=dialog.lang_manager,
            supports_archive_layer=True,
        )
        module_manager.registerModule(
            ProjectsModule,
            Module.PROJECT.name,
            qss_files=qss_modular,
            language=dialog.lang_manager,
            supports_statuses=True,
            supports_tags=True,
            module_labels=[
                {
                    "key": SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER,
                    "title_value": dialog.lang_manager.translate(DialogLabels.PROJECTS_SOURCE_FOLDER),
                    "tool": "button",
                    "on_click": pick_folder,
                },
                {
                    "key": SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER,
                    "title_value": dialog.lang_manager.translate(DialogLabels.PROJECTS_TARGET_FOLDER),
                    "tool": "button",
                    "on_click": pick_folder,
                },
                {
                    "key": SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
                    "tool": "button",
                    "title_value": dialog.lang_manager.translate(
                        DialogLabels.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE
                    ),
                    "on_click": open_folder_rule,
                },
            ],
        )
        module_manager.registerModule(
            ContractsModule,
            Module.CONTRACT.name,
            qss_files=qss_modular,
            lang_manager=dialog.lang_manager,
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
        )
        module_manager.registerModule(
            CoordinationModule,
            Module.COORDINATION.name,
            qss_files=qss_modular,
            language=dialog.lang_manager,
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
            supports_archive_layer=True,
        )
        module_manager.registerModule(
            SignalTestModule,
            Module.SIGNALTEST.name,
            qss_files=qss_signaltest,
            lang_manager=dialog.lang_manager,
        )

        dialog.sidebar.populate_from_modules(module_manager)
