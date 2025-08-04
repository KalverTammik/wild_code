import json
import os

DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

class LanguageManager:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language
        self.translations = {}
        self.load_language()

    def load_language(self):
        lang_file = os.path.join(os.path.dirname(__file__), f"{self.language}.json")  # Adjusted path
        if os.path.exists(lang_file):
            with open(lang_file, "r", encoding="utf-8") as file:
                self.translations = json.load(file)
        else:
            print(f"Language file {lang_file} not found. Defaulting to empty translations.")

    def translate(self, key):
        return self.translations.get(key, key)  # Return the key itself if no translation is found

    def set_language(self, language):
        self.language = language
        self.load_language()

    def save_language_preference(self):
        """Save the user's preferred language to a settings file."""
        settings_file = os.path.join(os.path.dirname(__file__), "user_settings.json")
        with open(settings_file, "w", encoding="utf-8") as file:
            json.dump({"preferred_language": self.language}, file)

    @staticmethod
    def load_language_preference():
        """Load the user's preferred language from the settings file."""
        settings_file = os.path.join(os.path.dirname(__file__), "user_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("preferred_language", DEFAULT_LANGUAGE)
        return DEFAULT_LANGUAGE
