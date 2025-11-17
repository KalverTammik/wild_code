# ...existing code...
DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

import os
import json
from .et import TRANSLATIONS as ET_TRANSLATIONS
from .en import TRANSLATIONS as EN_TRANSLATIONS

class LanguageManager:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language

    def translate(self, key):
        """Lookup key in main language module first, then in module language modules.
           Uses the modules' own TRANSLATIONS dicts without copying them."""
        # main file
        if self.language == "et":
            translations = ET_TRANSLATIONS
        elif self.language == "en":
            translations = EN_TRANSLATIONS
        else:
            translations = ET_TRANSLATIONS
        return translations.get(key)

    @staticmethod
    def translate_static(key):
        """Static method for global translation using default language."""
        manager = LanguageManager()
        return manager.translate(key)


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