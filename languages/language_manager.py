from .et import TRANSLATIONS as ET_TRANSLATIONS
from .en import TRANSLATIONS as EN_TRANSLATIONS
from .translation_keys import TranslationKeys
from ..constants.module_names import Module

DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

# One table per language. A language is added by registering its complete table here; nothing else
# changes, and tests/test_translation_completeness.py then holds the new table to the whole key catalogue.
_TABLES = {
    "et": ET_TRANSLATIONS,
    "en": EN_TRANSLATIONS,
}
SUPPORTED_LANGUAGES = tuple(_TABLES)

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

    def translate(self, key):
        """The text of `key` in this manager's language. A missing key raises: there is no fallback text and no
        fallback language, so a gap in a table is found by the tests instead of showing as another language."""
        try:
            return _TABLES[self.language][key]
        except KeyError:
            raise KeyError(f"Missing translation for key {key!r} in language {self.language!r}") from None

    def translate_module_name(self, module_name: str) -> str:
        key = (module_name or "").strip().lower()
        translation_key = _MODULE_TRANSLATION_KEY_MAP.get(key, key)
        return self.translate(translation_key)

    @staticmethod
    def translate_static(key):
        """Translate with the plugin-wide language, without a manager instance."""
        return LanguageManager().translate(key)
