import json
import os

class TranslationAgent:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_FILE = os.path.join(BASE_DIR, "base.json")
    LANG_FILES = ["et.json", "en.json", "fr.json"]

    @staticmethod
    def extract_missing_keys():
        """
        Extract missing keys from all language files and update base.json.
        """
        try:
            # Load base.json
            with open(TranslationAgent.BASE_FILE, "r") as base_file:
                base_data = json.load(base_file)

            # Iterate through language files
            for lang_file in TranslationAgent.LANG_FILES:
                lang_path = os.path.join(TranslationAgent.BASE_DIR, lang_file)
                with open(lang_path, "r") as file:
                    lang_data = json.load(file)

                # Find missing keys
                missing_keys = {key: value for key, value in base_data.items() if key not in lang_data}

                # Update language file with missing keys
                if missing_keys:
                    lang_data.update(missing_keys)
                    with open(lang_path, "w") as file:
                        json.dump(lang_data, file, indent=4)
                    print(f"Updated {lang_file} with missing keys.")

        except Exception as e:
            print(f"Error extracting missing keys: {e}")

    @staticmethod
    def update_base_file(new_keys):
        """
        Update base.json with new keys.
        :param new_keys: Dictionary of new keys to add.
        """
        try:
            with open(TranslationAgent.BASE_FILE, "r") as base_file:
                base_data = json.load(base_file)

            # Add new keys to base.json
            base_data.update(new_keys)
            with open(TranslationAgent.BASE_FILE, "w") as base_file:
                json.dump(base_data, base_file, indent=4)
            print("base.json updated with new keys.")

        except Exception as e:
            print(f"Error updating base.json: {e}")
