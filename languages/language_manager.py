
DEFAULT_LANGUAGE = "et"  # Set Estonian as the default language

import os
import json
import importlib.util

class LanguageManager:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language
        self.translations = {}
        self.sidebar_buttons = {}
        self.load_language()

    def load_language(self):
        self.translations = {}
        self.sidebar_buttons = {}
        lang_py = os.path.join(os.path.dirname(__file__), f"{self.language}.py")
        if os.path.exists(lang_py):
            spec = importlib.util.spec_from_file_location(f"lang_{self.language}", lang_py)
            lang_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lang_mod)
            self.translations.update(getattr(lang_mod, "TRANSLATIONS", {}))
        else:
            # Language file not found - use print instead of logger to avoid import issues
            print(f"Python language file {lang_py} not found. Defaulting to empty translations.")

        # Load and merge module translations from each module's lang/<lang>.py
        plugin_root = os.path.dirname(os.path.dirname(__file__))
        for root, dirs, files in os.walk(os.path.join(plugin_root, "modules")):
            if os.path.basename(root) == "lang":
                lang_file = os.path.join(root, f"{self.language}.py")
                if os.path.exists(lang_file):
                    try:
                        spec = importlib.util.spec_from_file_location(f"module_lang_{os.path.basename(os.path.dirname(root))}_{self.language}", lang_file)
                        lang_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(lang_mod)
                        self.translations.update(getattr(lang_mod, "TRANSLATIONS", {}))
                    except Exception as e:
                        # Failed to load module translation - use print instead of logger
                        print(f"Failed to load module translation {lang_file}: {e}")

        # Load sidebar button names from class-based file
        sidebar_py = os.path.join(os.path.dirname(__file__), f"sidebar_button_names_{self.language}.py")
        if os.path.exists(sidebar_py):
            spec = importlib.util.spec_from_file_location(f"sidebar_{self.language}", sidebar_py)
            sidebar_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sidebar_mod)
            self.sidebar_buttons = getattr(sidebar_mod.SideBarButtonNames, "BUTTONS", {})
        else:
            # Sidebar button names file not found - use print instead of logger
            print(f"Sidebar button names file {sidebar_py} not found. Defaulting to empty sidebar buttons.")

    def translate(self, key):
        return self.translations.get(key, key)

    def sidebar_button(self, key):
        return self.sidebar_buttons.get(key, key)

    def set_language(self, language):
        self.language = language
        self.load_language()

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
