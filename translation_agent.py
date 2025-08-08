import os
import json
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Paths to monitor
FILES_TO_MONITOR = [
    "login_dialog.py",
    "dialog.py",
    "main.py"
]

# Import centralized path constants
from .constants.file_paths import LanguagePaths

# Path to the master translation file
MASTER_TRANSLATION_FILE = LanguagePaths.BASE_JSON

# Path to the languages directory
LANGUAGES_DIR = LanguagePaths.LANGUAGES_DIR

class TranslationAgent(FileSystemEventHandler):
    def on_modified(self, event):
        if any(file in event.src_path for file in FILES_TO_MONITOR):
            self.update_translations()

    def extract_keys(self):
        """Extract translation keys from monitored files."""
        keys = set()
        for file in FILES_TO_MONITOR:
            if os.path.exists(file):
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    keys.update(re.findall(r'lang\.translate\("(.*?)"\)', content))
        return keys

    def update_translations(self):
        """Update the master translation file and propagate changes to language modules."""
        # Extract keys from monitored files
        extracted_keys = self.extract_keys()

        # Load the master translation file
        if os.path.exists(MASTER_TRANSLATION_FILE):
            with open(MASTER_TRANSLATION_FILE, "r", encoding="utf-8") as f:
                master_translations = json.load(f)
        else:
            master_translations = {}

        # Add missing keys to the master file
        for key in extracted_keys:
            if key not in master_translations:
                master_translations[key] = "TODO"

        # Remove unused keys
        for key in list(master_translations.keys()):
            if key not in extracted_keys:
                del master_translations[key]

        # Save the updated master file
        with open(MASTER_TRANSLATION_FILE, "w", encoding="utf-8") as f:
            json.dump(master_translations, f, indent=4, ensure_ascii=False)

        # Propagate changes to language modules
        self.propagate_to_languages(master_translations)

    def propagate_to_languages(self, master_translations):
        """Propagate changes from the master file to all language modules."""
        for file in os.listdir(LANGUAGES_DIR):
            if file.endswith(".json") and file != "base.json":
                lang_file_path = os.path.join(LANGUAGES_DIR, file)
                with open(lang_file_path, "r", encoding="utf-8") as f:
                    lang_translations = json.load(f)

                # Add missing keys
                for key, value in master_translations.items():
                    if key not in lang_translations:
                        lang_translations[key] = "TODO"

                # Remove unused keys
                for key in list(lang_translations.keys()):
                    if key not in master_translations:
                        del lang_translations[key]

                # Save the updated language file
                with open(lang_file_path, "w", encoding="utf-8") as f:
                    json.dump(lang_translations, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    event_handler = TranslationAgent()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
