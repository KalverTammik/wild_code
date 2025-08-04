# Languages Directory

This directory contains JSON files for supported languages. Each file should follow the format:

```json
{
    "key": "translation"
}
```

For example:

```json
{
    "login_title": "Login",
    "username_label": "Username:",
    "password_label": "Password:",
    "login_button": "Login"
}
```

## Path to this directory

The full path to this directory is:
`c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code\languages`

Add new languages by creating a new JSON file with the appropriate translations.

Supported languages: Estonian (et), English (en), French (fr).

## Using the Translation Agent

1. **Start the Agent**:
   Run the following command in your terminal to start the translation agent:
   ```
   C:/Users/Kalver/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/wild_code/.venv/Scripts/python.exe translation_agent.py
   ```

2. **Monitor Changes**:
   The agent will monitor changes in the following files:
   - `login_dialog.py`
   - `dialog.py`
   - `main.py`

3. **Add New Keys**:
   - Add a new `lang.translate("key")` call in one of the monitored files.
   - Save the file.

4. **Check Updates**:
   - The agent will automatically update `base.json` with the new key and propagate it to all language files with a placeholder value (`"TODO"`).

5. **Remove Unused Keys**:
   - If a key is removed from the monitored files, the agent will delete it from `base.json` and all language files.

6. **Verify Translations**:
   - Open the language files (e.g., `et.json`, `fr.json`) and replace `"TODO"` with the correct translations.

7. **Stop the Agent**:
   - Press `Ctrl+C` in the terminal to stop the agent.
