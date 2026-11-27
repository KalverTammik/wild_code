from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..module_manager import ModuleManager
    from ..languages.language_manager import LanguageManager
    from ..widgets.sidebar import Sidebar


class DialogProtocol(Protocol):
    lang_manager: "LanguageManager"
    sidebar: "Sidebar"


def _adapt_value_editor(value_editor):
    """Adapt a single-value editor to the module-label callback contract."""

    def handler(_module_key: str, _key: str, current_value: str):
        return value_editor(current_value)

    return handler


class ModulesRegistry:
    @staticmethod
    def register_all(module_manager: "ModuleManager", dialog: "DialogProtocol") -> None:
        """Wire module registrations onto the provided ModuleManager instance."""
        from functools import partial
        from qgis.PyQt.QtWidgets import QDialog

        from ..languages.translation_keys import DialogLabels
        from ..constants.setting_placeholders import SettingDialogPlaceholders
        from ..modules.Settings.SettingsUI import SettingsModule
        from ..modules.easements.easement_status_mapping_dialog import EasementStatusMappingDialog
        from ..modules.Property.widgets.property_ui import PropertyModule
        from ..modules.projects.ProjectsUi import ProjectsModule
        from ..modules.projects.projects_card_actions import ProjectCardActions
        from ..modules.projects.FolderNamingRuleDialog import FolderNamingRuleDialog
        from ..modules.contract.ContractUi import ContractsModule
        from ..modules.coordination.CoordinationModule import CoordinationModule
        from ..modules.easements.EasementsUi import EasementsModule
        from ..modules.easements.easement_card_actions import EasementCardActions
        from ..modules.easements.easement_layer_service import EasementLayerService
        from ..modules.works.WorksUi import WorksModule
        from ..modules.works.works_card_actions import WorksCardActions
        from ..modules.asbuilt.AsBuiltUi import AsBuiltModule
        from ..modules.asbuilt.asbuilt_card_actions import AsBuiltCardActions
        from ..constants.module_names import Module
        from .window_state.dialog_helpers import DialogHelpers
        from ..utils.Folders.foldersHelpers import FolderHelpers
        from ..widgets.WelcomePage import WelcomePage
        from .theme_manager import ThemeManager

        qss_modular = list(ThemeManager.module_bundle())

        # Module pieces that shared widgets show; the widgets never import modules/ themselves.
        from ..widgets.DataDisplayWidgets.ModuleConfig import ModuleConfigFactory
        from ..widgets.DataDisplayWidgets.status_change_controller import StatusChangeController
        from ..modules.projects.project_detail_config import create_project_config
        from ..modules.works.works_sync_service import WorksSyncService
        from ..modules.projects.projects_layer_service import ProjectsLayerService

        ModuleConfigFactory.register(Module.PROJECT.value, create_project_config)

        def sync_works_layer(item_id: str, task_payload) -> None:
            WorksSyncService().sync_task_from_backend(item_id, task=task_payload)

        StatusChangeController.register_status_change_hook(
            (Module.WORKS.value, Module.TASK.value),
            "works_layer_sync",
            sync_works_layer,
        )

        def sync_asbuilt_layer(item_id: str, task_payload) -> None:
            from ..modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService

            AsBuiltLayerService.sync_status_from_task(item_id, task_payload)

        # An as-built is a task too, but its status belongs on the as-built layer, not the Works layer.
        StatusChangeController.register_status_change_hook((Module.ASBUILT.value,), "asbuilt_layer_sync", sync_asbuilt_layer)

        def sync_project_layer(item_id: str, project_payload) -> None:
            ProjectsLayerService.sync_status_from_project(item_id, project_payload)

        StatusChangeController.register_status_change_hook((Module.PROJECT.value,), "project_layer_sync", sync_project_layer)

        def sync_easement_layer(item_id: str, easement_payload) -> None:
            EasementLayerService.sync_status_from_easement(item_id, easement_payload)

        StatusChangeController.register_status_change_hook((Module.EASEMENT.value,), "easement_layer_sync", sync_easement_layer)

        def pick_folder(_module_key: str, _key: str, current_value: str):
            return FolderHelpers.select_folder_path(dialog, start_path=current_value)

        def open_easement_status_mapping(_module_key: str, _key: str, current_value: str):
            return EasementStatusMappingDialog.edit_mapping(
                lang_manager=dialog.lang_manager,
                stored_value=current_value,
                parent=dialog,
            )

        open_folder_rule = _adapt_value_editor(
            partial(
                DialogHelpers.open_folder_rule_dialog,
                dialog,
                FolderNamingRuleDialog,
                QDialog.DialogCode.Accepted,
            )
        )

        module_manager.registerModule(
            WelcomePage,
            Module.HOME.name,
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
            supports_archive_layer=True,
        )
        module_manager.registerModule(
            ProjectsModule,
            Module.PROJECT.name,
            card_actions=ProjectCardActions,
            qss_files=qss_modular,
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
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
        )
        module_manager.registerModule(
            CoordinationModule,
            Module.COORDINATION.name,
            qss_files=qss_modular,
            supports_types=True,
            supports_statuses=True,
            supports_tags=True,
            supports_archive_layer=True,
        )
        module_manager.registerModule(
            EasementsModule,
            Module.EASEMENT.name,
            card_actions=EasementCardActions,
            qss_files=qss_modular,
            supports_types=True,
            supports_statuses=True,
            supports_tags=False,
            module_labels=[
                {
                    "key": SettingDialogPlaceholders.EASEMENT_LAYER_STATUS_MAPPING,
                    "title_value": dialog.lang_manager.translate(DialogLabels.EASEMENT_LAYER_STATUS_MAPPING),
                    "tool": "button",
                    "on_click": open_easement_status_mapping,
                    "display_formatter": EasementLayerService.format_status_mapping_summary,
                },
            ],
        )
        module_manager.registerModule(
            WorksModule,
            Module.WORKS.name,
            card_actions=WorksCardActions,
            qss_files=qss_modular,
            supports_types=True,
            supports_statuses=True,
            supports_tags=False,
        )
        module_manager.registerModule(
            AsBuiltModule,
            Module.ASBUILT.name,
            card_actions=AsBuiltCardActions,
            qss_files=qss_modular,
            supports_types=True,
            supports_statuses=True,
            supports_tags=False,
        )

        dialog.sidebar.populate_from_modules(module_manager)
