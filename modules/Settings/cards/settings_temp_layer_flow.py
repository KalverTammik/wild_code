"""The "create/load temp GPKG layer" button on the works and projects settings cards.

Both modules run the same flow; only the helper, the texts and the log event differ.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import QFileDialog, QPushButton, QWidget

from ...projects.projects_entry import ProjectsTempLayerHelper
from ...works.works_entry import WorksTempLayerHelper
from ....Logs.python_fail_logger import PythonFailLogger
from ....constants.button_props import ButtonSize, ButtonVariant
from ....constants.module_names import Module
from ....languages.translation_keys import TranslationKeys
from ....utils.property.ArchiveLayerHandler import GPKGHelpers
from ....ui.messages_helper import ModernMessageDialog
from ....utils.MapTools.MapHelpers import MapHelpers


@dataclass(frozen=True)
class TempLayerFlow:
    helper: type
    failure_event: str
    button_name: str
    button_variant: str
    create_button: str
    reference_required: str
    prompt_title: str
    prompt_label: str
    name_required: str
    storage_existing: str
    storage_standalone: str
    storage_title: str
    storage_message: str
    gpkg_required: str
    save_dialog_title: str
    overwrite_title: str
    overwrite_message: str
    create_failed: str
    ready: str


WORKS_TEMP_LAYER_FLOW = TempLayerFlow(
    helper=WorksTempLayerHelper,
    failure_event="works_temp_layer_button_failed",
    button_name="WorksTempLayerCreateButton",
    button_variant=ButtonVariant.WARNING,
    create_button=TranslationKeys.WORKS_TEMP_LAYER_CREATE_BUTTON,
    reference_required=TranslationKeys.WORKS_TEMP_LAYER_REFERENCE_REQUIRED,
    prompt_title=TranslationKeys.WORKS_TEMP_LAYER_PROMPT_TITLE,
    prompt_label=TranslationKeys.WORKS_TEMP_LAYER_PROMPT_LABEL,
    name_required=TranslationKeys.WORKS_TEMP_LAYER_NAME_REQUIRED,
    storage_existing=TranslationKeys.WORKS_TEMP_LAYER_STORAGE_EXISTING,
    storage_standalone=TranslationKeys.WORKS_TEMP_LAYER_STORAGE_STANDALONE,
    storage_title=TranslationKeys.WORKS_TEMP_LAYER_STORAGE_TITLE,
    storage_message=TranslationKeys.WORKS_TEMP_LAYER_STORAGE_MESSAGE,
    gpkg_required=TranslationKeys.WORKS_TEMP_LAYER_GPKG_REQUIRED,
    save_dialog_title=TranslationKeys.WORKS_TEMP_LAYER_SAVE_DIALOG_TITLE,
    overwrite_title=TranslationKeys.WORKS_TEMP_LAYER_OVERWRITE_TITLE,
    overwrite_message=TranslationKeys.WORKS_TEMP_LAYER_OVERWRITE_MESSAGE,
    create_failed=TranslationKeys.WORKS_TEMP_LAYER_CREATE_FAILED,
    ready=TranslationKeys.WORKS_TEMP_LAYER_READY,
)

PROJECTS_TEMP_LAYER_FLOW = TempLayerFlow(
    helper=ProjectsTempLayerHelper,
    failure_event="projects_temp_layer_button_failed",
    button_name="ProjectsTempLayerCreateButton",
    button_variant=ButtonVariant.SUCCESS,
    create_button=TranslationKeys.PROJECTS_TEMP_LAYER_CREATE_BUTTON,
    reference_required=TranslationKeys.PROJECTS_TEMP_LAYER_REFERENCE_REQUIRED,
    prompt_title=TranslationKeys.PROJECTS_TEMP_LAYER_PROMPT_TITLE,
    prompt_label=TranslationKeys.PROJECTS_TEMP_LAYER_PROMPT_LABEL,
    name_required=TranslationKeys.PROJECTS_TEMP_LAYER_NAME_REQUIRED,
    storage_existing=TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_EXISTING,
    storage_standalone=TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_STANDALONE,
    storage_title=TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_TITLE,
    storage_message=TranslationKeys.PROJECTS_TEMP_LAYER_STORAGE_MESSAGE,
    gpkg_required=TranslationKeys.PROJECTS_TEMP_LAYER_GPKG_REQUIRED,
    save_dialog_title=TranslationKeys.PROJECTS_TEMP_LAYER_SAVE_DIALOG_TITLE,
    overwrite_title=TranslationKeys.PROJECTS_TEMP_LAYER_OVERWRITE_TITLE,
    overwrite_message=TranslationKeys.PROJECTS_TEMP_LAYER_OVERWRITE_MESSAGE,
    create_failed=TranslationKeys.PROJECTS_TEMP_LAYER_CREATE_FAILED,
    ready=TranslationKeys.PROJECTS_TEMP_LAYER_READY,
)


class SettingsTempLayerMixin:
    """Mixed into SettingsModuleCard, which provides the layer picker, the pending main
    layer name, _write_saved_layer_value and sync_main_layer_selection."""

    def _create_temp_layer_button(self, parent: QWidget, flow: TempLayerFlow) -> QPushButton:
        button = QPushButton(self.lang_manager.translate(flow.create_button), parent)
        button.setObjectName(flow.button_name)
        button.setProperty("variant", flow.button_variant)
        button.setProperty("btnSize", ButtonSize.SMALL)
        button.setAutoDefault(False)
        button.setDefault(False)
        button.clicked.connect(lambda _checked=False: self._run_temp_layer_flow(flow))
        return button

    def _run_temp_layer_flow(self, flow: TempLayerFlow) -> None:
        translate = self.lang_manager.translate
        helper = flow.helper
        try:
            preferred_layer = self._layer_selector.currentLayer() if self._layer_selector else None
            reference_layer = helper.resolve_reference_layer(preferred_layer)
            if reference_layer is None:
                ModernMessageDialog.show_warning(translate(TranslationKeys.ERROR), translate(flow.reference_required))
                return

            default_name = self._pend_element_name or self._orig_element_name or helper.DEFAULT_LAYER_NAME
            layer_name, ok = ModernMessageDialog.get_text_modern(
                translate(flow.prompt_title),
                translate(flow.prompt_label),
                text=default_name,
            )
            if not ok:
                return

            normalized_name = (layer_name or "").strip()
            if not normalized_name:
                ModernMessageDialog.show_warning(translate(TranslationKeys.ERROR), translate(flow.name_required))
                return

            use_existing_label = translate(flow.storage_existing)
            standalone_label = translate(flow.storage_standalone)
            cancel_label = translate(TranslationKeys.CANCEL_BUTTON)
            storage_choice = ModernMessageDialog.ask_choice_modern(
                translate(flow.storage_title),
                translate(flow.storage_message),
                buttons=[use_existing_label, standalone_label, cancel_label],
                default=standalone_label,
                cancel=cancel_label,
                button_variants=[ButtonVariant.PRIMARY, ButtonVariant.SUCCESS, ButtonVariant.GHOST],
            )
            if storage_choice in (None, cancel_label):
                return

            target_gpkg_path: str | None = None
            overwrite_file = False
            backup_path = ""
            if storage_choice == use_existing_label:
                if not helper.gpkg_path_for_layer(reference_layer):
                    ModernMessageDialog.show_warning(translate(TranslationKeys.ERROR), translate(flow.gpkg_required))
                    return
            else:
                default_path = helper.default_standalone_gpkg_path(reference_layer, normalized_name)
                selected_path, _selected_filter = QFileDialog.getSaveFileName(
                    self,
                    translate(flow.save_dialog_title),
                    default_path,
                    "GeoPackage (*.gpkg)",
                )
                if not selected_path:
                    return

                target_gpkg_path = selected_path if selected_path.lower().endswith(".gpkg") else f"{selected_path}.gpkg"
                if os.path.exists(target_gpkg_path):
                    # The whole file goes: name its layers, default to Cancel and keep the old file as a backup.
                    backup_path = helper.backup_path_for(target_gpkg_path)
                    file_layers = GPKGHelpers.gpkg_layer_names(target_gpkg_path)
                    loaded = helper.loaded_layer_names_for_gpkg(target_gpkg_path)
                    dash = translate(TranslationKeys.NONE_DASH)
                    overwrite_label = translate(TranslationKeys.TEMP_LAYER_OVERWRITE_BUTTON)
                    choice = ModernMessageDialog.ask_choice_modern(
                        translate(flow.overwrite_title),
                        translate(TranslationKeys.TEMP_LAYER_OVERWRITE_CONFIRM).format(
                            path=target_gpkg_path,
                            layers=", ".join(file_layers) if file_layers else dash,
                            loaded=", ".join(loaded) if loaded else dash,
                            backup=backup_path,
                        ),
                        buttons=[overwrite_label, cancel_label],
                        default=cancel_label,
                        cancel=cancel_label,
                        button_variants=[ButtonVariant.WARNING, ButtonVariant.GHOST],
                    )
                    if choice != overwrite_label:
                        return
                    moved, move_error = helper.move_gpkg_to_backup(target_gpkg_path, backup_path)
                    if not moved:
                        ModernMessageDialog.show_warning(
                            translate(TranslationKeys.ERROR),
                            translate(TranslationKeys.TEMP_LAYER_BACKUP_FAILED).format(error=move_error),
                        )
                        return

            created_layer, error_text = helper.create_or_load_layer(
                reference_layer,
                normalized_name,
                gpkg_path=target_gpkg_path,
                overwrite_file=overwrite_file,
            )
            if created_layer is None or not created_layer.isValid():
                ModernMessageDialog.show_warning(
                    translate(TranslationKeys.ERROR),
                    translate(flow.create_failed).format(
                        name=normalized_name,
                        error=error_text or translate(TranslationKeys.ERROR),
                    ),
                )
                return

            actual_name = created_layer.name() or normalized_name
            self._write_saved_layer_value("element", actual_name)
            self.sync_main_layer_selection(actual_name, force=True)

            ready_text = translate(flow.ready).format(name=actual_name)
            if backup_path:
                ready_text += "\n\n" + translate(TranslationKeys.TEMP_LAYER_BACKUP_NOTE).format(backup=backup_path)
            ModernMessageDialog.show_info(translate(TranslationKeys.SUCCESS), ready_text)
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=Module.SETTINGS.value, event=flow.failure_event)
            ModernMessageDialog.show_warning(
                translate(TranslationKeys.ERROR),
                translate(flow.create_failed).format(
                    name=(
                        MapHelpers.layer_name_from_id(self._pend_element_name or self._orig_element_name)
                        or self._pend_element_name
                        or self._orig_element_name
                        or helper.DEFAULT_LAYER_NAME
                    ),
                    error=str(exc),
                ),
            )
