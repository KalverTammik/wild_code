# ...existing code...
DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

import os
import json
from .et import TRANSLATIONS as ET_TRANSLATIONS
from .en import TRANSLATIONS as EN_TRANSLATIONS
from .translation_keys import TranslationKeys
from ..utils.url_manager import Module

_MODULE_TRANSLATION_KEY_MAP = {
    Module.HOME.value: TranslationKeys.MODULE_HOME,
    Module.PROPERTY.value: TranslationKeys.MODULE_PROPERTY,
    Module.CONTRACT.value: TranslationKeys.MODULE_CONTRACT,
    Module.PROJECT.value: TranslationKeys.MODULE_PROJECT,
    Module.SETTINGS.value: TranslationKeys.MODULE_SETTINGS,
    Module.COORDINATION.value: TranslationKeys.MODULE_COORDINATION,
    Module.LETTER.value: TranslationKeys.MODULE_LETTER,
    Module.SPECIFICATION.value: TranslationKeys.MODULE_SPECIFICATION,
    Module.EASEMENT.value: TranslationKeys.MODULE_EASEMENT,
    Module.ORDINANCE.value: TranslationKeys.MODULE_ORDINANCE,
    Module.SUBMISSION.value: TranslationKeys.MODULE_SUBMISSION,
    Module.TASK.value: TranslationKeys.MODULE_TASK,
    Module.ASBUILT.value: TranslationKeys.MODULE_ASBUILT,
    Module.WORKS.value: TranslationKeys.MODULE_WORKS,
    Module.STATUSES.value: TranslationKeys.MODULE_STATUSES,
    Module.SIGNALTEST.value: TranslationKeys.SIGNALTEST,
    "properties": TranslationKeys.PROPERTIES,
    "projects": TranslationKeys.PROJECTS,
    "contracts": TranslationKeys.CONTRACTS,
    "coordinations": TranslationKeys.COORDINATIONS,
    "letters": TranslationKeys.LETTERS,
    "specifications": TranslationKeys.SPECIFICATIONS,
    "easements": TranslationKeys.EASEMENTS,
    "ordinances": TranslationKeys.ORDINANCES,
    "submissions": TranslationKeys.SUBMISSIONS,
    "tasks": TranslationKeys.TASKS,
}

class LanguageManager:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language

    def translate(self, key, fallback: str | None = None):
        """Lookup key in main language module first, then in module language modules.
           Uses the modules' own TRANSLATIONS dicts without copying them."""
        # main file
        if self.language == "et":
            translations = ET_TRANSLATIONS
        elif self.language == "en":
            translations = EN_TRANSLATIONS
        else:
            translations = ET_TRANSLATIONS
        value = translations.get(key)
        if value is not None:
            return value
        if fallback is not None:
            return fallback
        raise KeyError(f"Missing translation for key: {key}")

    def translate_module_name(self, module_name: str) -> str:
        key = (module_name or "").strip().lower()
        translation_key = _MODULE_TRANSLATION_KEY_MAP.get(key, key)
        return self.translate(translation_key)

    @staticmethod
    def translate_static(key, fallback: str | None = None):
        """Static method for global translation using default language."""
        manager = LanguageManager()
        return manager.translate(key, fallback)


    def set_language(self, language):
        self.language = language

    def save_language_preference(self):
        settings_file = os.path.join(os.path.dirname(__file__), "user_settings.json")
        with open(settings_file, "w", encoding="utf-8") as file:
            json.dump({"preferred_language": self.language}, file)

    @staticmethod
    def load_language_preference():
        settings_file = os.path.join(os.path.dirname(__file__), "user_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("preferred_language", DEFAULT_LANGUAGE)
        return DEFAULT_LANGUAGE