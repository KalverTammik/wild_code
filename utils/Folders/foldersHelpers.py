
import subprocess
from typing import Callable, Optional
import shutil
import os
from PyQt5.QtWidgets import QFileDialog
from ...python.module_files_path_updater import ModuleFilesPathUpdater
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys

from ...utils.url_manager import Module
from ...modules.Settings.setting_keys import SettingDialogPlaceholders
from ...constants.settings_keys import SettingsService
from ..messagesHelper import ModernMessageDialog
from ..security_boundaries import (
    is_same_or_descendant_path,
    resolve_direct_child_path,
    sanitize_path_component,
)
from ..project_folder_rules import (
    DEFAULT_PROJECT_FOLDER_RULE,
    MissingProjectNumberError,
    build_project_folder_name,
)
from ...Logs.python_fail_logger import PythonFailLogger

class FolderEngines:
    @staticmethod
    def _update_project_folder_link(project_id, dest_dir, warning_title) -> Optional[str]:
        try:
            updated = ModuleFilesPathUpdater().update(
                Module.PROJECT,
                project_id,
                dest_dir,
            )
            updated_path = str(updated.get("filesPath") or "").strip()
            if not updated_path:
                raise RuntimeError("filesPath update returned an empty path")
            return updated_path
        except Exception as exc:
            text = LanguageManager.translate_static(
                TranslationKeys.PROJECT_FOLDER_LINK_UPDATE_FAILED
            ).format(
                path=dest_dir,
                error=exc,
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return None

    @staticmethod
    def generate_project_folder_from_template( project_id, 
                                               project_name, 
                                               project_number,
                                               source_folder,
                                               target_folder,
                                               on_files_path_updated: Optional[Callable[[str], None]] = None,
                                               ) -> None:
        confirm_title = LanguageManager.translate_static(TranslationKeys.CONFIRM) or "Confirmation"
        yes_label = LanguageManager.translate_static(TranslationKeys.YES) or "Yes"
        no_label = LanguageManager.translate_static(TranslationKeys.NO) or "No"
        warning_title = LanguageManager.translate_static(TranslationKeys.WARNING) or "Warning"

        source_value = str(source_folder or "").strip()
        target_value = str(target_folder or "").strip()
        source_dir = os.path.realpath(os.path.abspath(source_value)) if source_value else ""
        target_dir = os.path.realpath(os.path.abspath(target_value)) if target_value else ""

        if not source_dir or not os.path.isdir(source_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_SOURCE_INVALID).format(
                path=source_value or "-"
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        if not target_dir or not os.path.isdir(target_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_TARGET_INVALID).format(
                path=target_value or "-"
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        if is_same_or_descendant_path(target_dir, source_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_TARGET_INSIDE_SOURCE).format(
                source=source_dir,
                target=target_dir,
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        try:
            raw_folder_name = FolderNameGenerator().folder_structure_name_order(project_name, project_number)
            fallback_name = f"project-{project_id}" if str(project_id or "").strip() else "project"
            folder_name = sanitize_path_component(raw_folder_name, fallback=fallback_name)
            dest_dir = resolve_direct_child_path(target_dir, folder_name)
        except MissingProjectNumberError:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_NUMBER_MISSING)
            ModernMessageDialog.show_warning(warning_title, text)
            return
        except Exception as exc:
            text = (
                LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID)
                + f"\n{exc}"
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        if not folder_name or not dest_dir:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID)
            ModernMessageDialog.show_warning(warning_title, text)
            return

        if os.path.exists(dest_dir):
            if os.path.isdir(dest_dir):
                link_action_label = LanguageManager.translate_static(
                    TranslationKeys.PROJECT_FOLDER_LINK_ACTION
                )
                confirmation_text = LanguageManager.translate_static(
                    TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_CONFIRM
                ).format(
                    path=dest_dir
                )
                link_existing = ModernMessageDialog.ask_yes_no(
                    confirm_title,
                    confirmation_text,
                    yes_label=link_action_label,
                    no_label=no_label,
                    default=no_label,
                )
                if not link_existing:
                    return
                updated_path = FolderEngines._update_project_folder_link(
                    project_id,
                    dest_dir,
                    warning_title,
                )
                if not updated_path:
                    return
                if callable(on_files_path_updated):
                    on_files_path_updated(updated_path)

                heading = LanguageManager.translate_static(TranslationKeys.SUCCESS) or "Success"
                text = LanguageManager.translate_static(
                    TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_SUCCESS
                ).format(
                    path=dest_dir
                )
                ModernMessageDialog.show_info(heading, text)
                return

            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS).format(
                path=dest_dir
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        confirmation_text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_CREATE_CONFIRM).format(
            source=source_dir,
            destination=dest_dir,
        )
        overall_confirmation = ModernMessageDialog.ask_yes_no(
            confirm_title,
            confirmation_text,
            yes_label=yes_label,
            no_label=no_label,
            default=no_label,
        )
        if not overall_confirmation:
            return

        try:
            if os.path.exists(dest_dir):
                text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS).format(
                    path=dest_dir
                )
                ModernMessageDialog.show_warning(warning_title, text)
                return
            shutil.copytree(source_dir, dest_dir)
        except Exception as exc:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_COPY_FAILED).format(
                error=exc
            )
            ModernMessageDialog.show_warning(warning_title, text)
            return

        confirmation = ModernMessageDialog.ask_yes_no(
            confirm_title,
            LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_LINK_CONFIRM).format(
                path=dest_dir
            ),
            yes_label=yes_label,
            no_label=no_label,
            default=yes_label,
        )

        if confirmation:
            updated_path = FolderEngines._update_project_folder_link(
                project_id,
                dest_dir,
                warning_title,
            )
            if not updated_path:
                return
            if callable(on_files_path_updated):
                on_files_path_updated(updated_path)
        else:
            print("Operation canceled by the user.")

        heading = LanguageManager.translate_static(TranslationKeys.SUCCESS) or "Success"
        text = (f"Kausta '{source_dir}'\n(k.a kaustas sisalduvad alamkaustad ja failid) dubleerimine õnnestus.")
        text_2 = f"Sihtkohta on genereeritud kaust nimetusega \n'{folder_name}'."
        ModernMessageDialog.show_info(heading, f"{text}\n\n{text_2}")

class FolderNameGenerator:
    def folder_structure_name_order(self, project_name, project_number):
        service = SettingsService()

        print("[folder_name] start", {"project_name": project_name, "project_number": project_number})

        rule_raw = service.module_label_value(
            Module.PROJECT.value,
            SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
        ) or ""
        print("[folder_name] rule_raw", rule_raw)

        rule = str(rule_raw).strip()
        print("[folder_name] normalized", {"rule": rule})

        if not rule:
            rule = DEFAULT_PROJECT_FOLDER_RULE
            print("[folder_name] fallback rule", rule)

        folder_name = build_project_folder_name(
            rule,
            project_name=project_name,
            project_number=project_number,
        )
        print("[folder_name] result", folder_name)
        return folder_name

class FolderHelpers:
    @staticmethod
    def select_folder_path(parent=None, start_path: str = "") -> Optional[str]:
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        caption: str = "Select folder"
        directory = QFileDialog.getExistingDirectory(parent, caption, start_path or os.path.expanduser("~"), options)
        return directory or None

    @staticmethod
    def open_item_folder(file_path: Optional[str]) -> None:
        if not file_path:
            return
        target = file_path.replace("/", "\\")
        try:
            if target.lower().startswith("http"):
                subprocess.Popen(["start", "", target], shell=True)
            else:
                subprocess.Popen(["explorer", target], shell=True)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="open_item_folder_failed",
            )
