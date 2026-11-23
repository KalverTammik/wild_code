
from typing import Callable, Optional
import shutil
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFileDialog
from ...python.module_files_path_updater import ModuleFilesPathUpdater
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.api_error_handling import user_message

from ...constants.module_names import Module
from ...constants.setting_placeholders import SettingDialogPlaceholders
from ..settings_service import SettingsService
from ..user_dialogs import UserDialogs
from ..security_boundaries import (
    DESCRIPTION_LINK_LOCAL_PATH,
    DESCRIPTION_LINK_NETWORK_PATH,
    DESCRIPTION_LINK_WEB,
    classify_description_link,
    is_same_or_descendant_path,
    resolve_allowed_external_extension,
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
    def _update_project_folder_link(project_id, dest_dir, warning_title, dialogs: UserDialogs) -> Optional[str]:
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
                error=user_message(exc),
            )
            dialogs.show_warning(warning_title, text)
            return None

    @staticmethod
    def generate_project_folder_from_template( project_id,
                                               project_name,
                                               project_number,
                                               source_folder,
                                               target_folder,
                                               on_files_path_updated: Optional[Callable[[str], None]] = None,
                                               *,
                                               dialogs: UserDialogs,
                                               ) -> None:
        confirm_title = LanguageManager.translate_static(TranslationKeys.CONFIRM)
        yes_label = LanguageManager.translate_static(TranslationKeys.YES)
        no_label = LanguageManager.translate_static(TranslationKeys.NO)
        warning_title = LanguageManager.translate_static(TranslationKeys.WARNING)

        source_value = str(source_folder or "").strip()
        target_value = str(target_folder or "").strip()
        source_dir = os.path.realpath(os.path.abspath(source_value)) if source_value else ""
        target_dir = os.path.realpath(os.path.abspath(target_value)) if target_value else ""

        if not source_dir or not os.path.isdir(source_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_SOURCE_INVALID).format(
                path=source_value or "-"
            )
            dialogs.show_warning(warning_title, text)
            return

        if not target_dir or not os.path.isdir(target_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_TARGET_INVALID).format(
                path=target_value or "-"
            )
            dialogs.show_warning(warning_title, text)
            return

        if is_same_or_descendant_path(target_dir, source_dir):
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_TARGET_INSIDE_SOURCE).format(
                source=source_dir,
                target=target_dir,
            )
            dialogs.show_warning(warning_title, text)
            return

        try:
            raw_folder_name = FolderNameGenerator().folder_structure_name_order(project_name, project_number)
            fallback_name = f"project-{project_id}" if str(project_id or "").strip() else "project"
            folder_name = sanitize_path_component(raw_folder_name, fallback=fallback_name)
            dest_dir = resolve_direct_child_path(target_dir, folder_name)
        except MissingProjectNumberError:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_NUMBER_MISSING)
            dialogs.show_warning(warning_title, text)
            return
        except Exception as exc:
            text = (
                LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID)
                + f"\n{exc}"
            )
            dialogs.show_warning(warning_title, text)
            return

        if not folder_name or not dest_dir:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID)
            dialogs.show_warning(warning_title, text)
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
                link_existing = dialogs.ask_yes_no(
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
                    dialogs,
                )
                if not updated_path:
                    return
                if callable(on_files_path_updated):
                    on_files_path_updated(updated_path)

                heading = LanguageManager.translate_static(TranslationKeys.SUCCESS)
                text = LanguageManager.translate_static(
                    TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_SUCCESS
                ).format(
                    path=dest_dir
                )
                dialogs.show_info(heading, text)
                return

            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS).format(
                path=dest_dir
            )
            dialogs.show_warning(warning_title, text)
            return

        confirmation_text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_CREATE_CONFIRM).format(
            source=source_dir,
            destination=dest_dir,
        )
        overall_confirmation = dialogs.ask_yes_no(
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
                dialogs.show_warning(warning_title, text)
                return
            shutil.copytree(source_dir, dest_dir)
        except Exception as exc:
            text = LanguageManager.translate_static(TranslationKeys.PROJECT_FOLDER_COPY_FAILED).format(
                error=exc
            )
            dialogs.show_warning(warning_title, text)
            return

        confirmation = dialogs.ask_yes_no(
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
                dialogs,
            )
            if not updated_path:
                return
            if callable(on_files_path_updated):
                on_files_path_updated(updated_path)

        # The folder is copied either way; only linking it to the project can be declined.
        heading = LanguageManager.translate_static(TranslationKeys.SUCCESS)
        text = LanguageManager.translate_static(TranslationKeys.FOLDER_COPY_SUCCESS).format(source=source_dir, folder=folder_name)
        dialogs.show_info(heading, text)

class FolderNameGenerator:
    def folder_structure_name_order(self, project_name, project_number):
        service = SettingsService()

        rule_raw = service.module_label_value(
            Module.PROJECT.value,
            SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
        ) or ""

        rule = str(rule_raw).strip()

        if not rule:
            rule = DEFAULT_PROJECT_FOLDER_RULE

        folder_name = build_project_folder_name(
            rule,
            project_name=project_name,
            project_number=project_number,
        )
        return folder_name

class FolderHelpers:
    @staticmethod
    def select_folder_path(parent=None, start_path: str = "") -> Optional[str]:
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        caption: str = "Select folder"
        directory = QFileDialog.getExistingDirectory(parent, caption, start_path or os.path.expanduser("~"), options)
        return directory or None

    # Results of open_item_folder; the caller words them for the user.
    FOLDER_OPENED = "opened"
    FOLDER_BLOCKED = "blocked"
    FOLDER_NOT_FOUND = "not_found"
    FOLDER_OPEN_FAILED = "failed"

    @staticmethod
    def open_item_folder(file_path: Optional[str]) -> str:
        """Open the item's folder or web address, never through a shell.

        The path comes from Kavitro. A shell (``start``/``explorer`` with ``shell=True``) would read
        characters such as ``&`` or ``|`` in it as commands; the desktop services open it as one path.
        The description link rules decide what may open: http/https, an absolute local or network
        folder, or a file whose extension is on the document allowlist (pdf, docx, dwg, ...), which
        opens in its own program. Programs and scripts (exe, bat, ps1, ...) are refused, as are
        control characters, device paths and other schemes.
        """
        destination = classify_description_link(file_path)
        try:
            if destination.kind == DESCRIPTION_LINK_WEB:
                opened = QDesktopServices.openUrl(QUrl(destination.target, QUrl.TolerantMode))
            elif destination.kind in (DESCRIPTION_LINK_LOCAL_PATH, DESCRIPTION_LINK_NETWORK_PATH):
                target = destination.target
                if os.path.isfile(target):
                    if not resolve_allowed_external_extension(local_file_path=target):
                        PythonFailLogger.log("open_item_folder_blocked", module="ui",
                                             extra={"reason": "file_extension"})
                        return FolderHelpers.FOLDER_BLOCKED
                elif not os.path.isdir(target):
                    return FolderHelpers.FOLDER_NOT_FOUND
                opened = QDesktopServices.openUrl(QUrl.fromLocalFile(target))
            else:
                PythonFailLogger.log(
                    "open_item_folder_blocked",
                    module="ui",
                    extra={"reason": destination.reason or destination.kind},
                )
                return FolderHelpers.FOLDER_BLOCKED
        except (OSError, RuntimeError) as exc:
            PythonFailLogger.log_exception(exc, module="ui", event="open_item_folder_failed")
            return FolderHelpers.FOLDER_OPEN_FAILED
        return FolderHelpers.FOLDER_OPENED if opened else FolderHelpers.FOLDER_OPEN_FAILED
