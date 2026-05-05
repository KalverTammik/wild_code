from __future__ import annotations

from typing import Any

from ...languages.translation_keys import TranslationKeys
from ...module_manager import ModuleManager
from ...utils.url_manager import Module, ModuleSupports
from .setting_keys import SettingDialogPlaceholders
from .SettinsUtils.SettingsLogic import SettingsLogic
from ..projects.project_board_status_rules import ProjectBoardStatusRules


class SettingsSetupGuard:
    _PROJECT_FOLDER_LABEL_KEYS = {
        SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER,
        SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER,
        SettingDialogPlaceholders.PROJECTS_PREFERED_FOLDER_NAME_STRUCTURE_RULE,
    }

    @staticmethod
    def _module_registration(module_key: str) -> dict[str, Any] | None:
        key = str(module_key or "").strip().lower()
        if not key:
            return None
        return ModuleManager().modules.get(key)

    @staticmethod
    def missing_requirements(module_key: str, *, include_project_folder_labels: bool = True) -> list[str]:
        key = str(module_key or "").strip().lower()
        if key in {"", Module.HOME.value, Module.SETTINGS.value}:
            return []

        registration = SettingsSetupGuard._module_registration(key)
        if not registration:
            return []

        logic = SettingsLogic()
        missing: list[str] = []

        supports_archive = bool(registration.get("supports_archive_layer"))
        layer_ids = logic.get_module_layer_ids(key, include_archive=supports_archive)
        if not str(layer_ids.get("element") or "").strip():
            missing.append("main-layer")
        if supports_archive and not str(layer_ids.get("archive") or "").strip():
            missing.append("archive-layer")

        if bool(registration.get("supports_statuses")):
            if not list(logic.load_module_preference_ids(key, support_key=ModuleSupports.STATUSES.value)):
                missing.append("preferred-statuses")
            if not list(ProjectBoardStatusRules.load_not_started_status_ids(key)):
                missing.append("not-started-statuses")

        if bool(registration.get("supports_types")):
            if not list(logic.load_module_preference_ids(key, support_key=ModuleSupports.TYPES.value)):
                missing.append("preferred-types")

        if bool(registration.get("supports_tags")):
            if not list(logic.load_module_preference_ids(key, support_key=ModuleSupports.TAGS.value)):
                missing.append("preferred-tags")

        for label_def in registration.get("module_labels") or []:
            if not isinstance(label_def, dict):
                continue
            label_key = label_def.get("key")
            if not label_key:
                continue
            if not include_project_folder_labels and label_key in SettingsSetupGuard._PROJECT_FOLDER_LABEL_KEYS:
                continue
            label_value = logic.load_module_label_value(key, label_key)
            if not str(label_value or "").strip():
                missing.append(f"label:{label_key}")

        return missing

    @staticmethod
    def is_ready(module_key: str, *, include_project_folder_labels: bool = True) -> bool:
        return not SettingsSetupGuard.missing_requirements(
            module_key,
            include_project_folder_labels=include_project_folder_labels,
        )

    @staticmethod
    def redirect_warning_text(lang_manager, module_key: str) -> tuple[str, str]:
        module_name = str(module_key or "").strip().lower()
        translated_module = (
            lang_manager.translate_module_name(module_name)
            if lang_manager is not None and hasattr(lang_manager, "translate_module_name")
            else module_name.capitalize()
        )
        title = lang_manager.translate(TranslationKeys.SETTINGS_SETUP_MISSING_TITLE) if lang_manager else "Module setup missing"
        body = lang_manager.translate(TranslationKeys.SETTINGS_SETUP_MISSING_MESSAGE).format(module=translated_module) if lang_manager else f"Settings for module {translated_module} are not configured yet. Next, you will be redirected to that module's settings."
        note = lang_manager.translate(TranslationKeys.SETTINGS_SETUP_MISSING_NOTE) if lang_manager else "Nota bene:\nPlease also review the other module settings while you are in Settings."
        return title, f"{body}\n\n{note}"
