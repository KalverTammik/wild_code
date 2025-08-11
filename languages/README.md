# Languages Directory

This directory contains JSON files for supported languages. Each file should follow the format:

# Keelefailide ja tõlkesüsteemi README
{
    "key": "translation"
}
```

    "password_label": "Password:",
    "login_button": "Login"
}

Add new languages by creating a new JSON file with the appropriate translations.

Supported languages: Estonian (et), English (en), French (fr).

## Using the Translation Agent

1. **Start the Agent**:
   Run the following command in your terminal to start the translation agent:
   ```
   ```

2. **Monitor Changes**:
   The agent will monitor changes in the following files:
   - `dialog.py`
   - `main.py`

   - Add a new `lang.translate("key")` call in one of the monitored files.
   - Save the file.

4. **Check Updates**:
   - The agent will automatically update `base.json` with the new key and propagate it to all language files with a placeholder value (`"TODO"`).

6. **Verify Translations**:
   - Open the language files (e.g., `et.json`, `fr.json`) and replace `"TODO"` with the correct translations.

Kui kõik on läbi käidud, siis tuleta mulle meelde commitida