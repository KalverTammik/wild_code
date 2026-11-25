from .et import TRANSLATIONS as ET_TRANSLATIONS
from .en import TRANSLATIONS as EN_TRANSLATIONS
from .translation_keys import TranslationKeys
from ..constants.module_names import Module

DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

# Languages that actually carry a translation table. Offering more would only
# fall back to Estonian silently.
SUPPORTED_LANGUAGES = ("et", "en")

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
    Module.SUBMISSION.value: TranslationKeys.MODULE_SUBMISSION,
    Module.TASK.value: TranslationKeys.MODULE_TASK,
    Module.ASBUILT.value: TranslationKeys.MODULE_ASBUILT,
    Module.WORKS.value: TranslationKeys.MODULE_WORKS,
    Module.STATUSES.value: TranslationKeys.MODULE_STATUSES,
    "properties": TranslationKeys.PROPERTIES,
    "projects": TranslationKeys.PROJECTS,
    "contracts": TranslationKeys.CONTRACTS,
    "coordinations": TranslationKeys.COORDINATIONS,
    "letters": TranslationKeys.LETTERS,
    "specifications": TranslationKeys.SPECIFICATIONS,
    "easements": TranslationKeys.EASEMENTS,
    "submissions": TranslationKeys.SUBMISSIONS,
    "tasks": TranslationKeys.TASKS,
}

def normalize_language(value) -> str | None:
    """Reduce a language code such as "et", "ET", "en-GB" or "et_EE" to a supported code, or None."""
    code = str(value or "").strip().lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED_LANGUAGES else None


# The language of the signed-in account. Managers built without an explicit
# language follow it, so one choice reaches every widget and message.
_current_language = DEFAULT_LANGUAGE


def get_current_language() -> str:
    return _current_language


def set_current_language(language) -> str:
    """Make a supported language the plugin-wide one; an unknown value keeps the Estonian default."""
    global _current_language
    _current_language = normalize_language(language) or DEFAULT_LANGUAGE
    return _current_language


class LanguageManager:
    def __init__(self, language=None):
        # None follows the plugin-wide language; a value pins this manager (tests, fixed-language texts).
        self._language = normalize_language(language) if language is not None else None

    @property
    def language(self) -> str:
        return self._language or _current_language

    def translate(self, key, fallback: str | None = None):
        """Lookup key in the language's translation table (Estonian when the language has none)."""
        translations = EN_TRANSLATIONS if self.language == "en" else ET_TRANSLATIONS
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
        """Translate with the plugin-wide language, without a manager instance."""
        return LanguageManager().translate(key, fallback)
