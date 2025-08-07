# Copilot Language and Module Management Rules

## Language Management
- All new modules must use `LanguageManager_NEW` from `language_manager.py` for translations.
- Translation files must be Python files (`.py`), not JSON or JS.
- Sidebar button names must be defined in `sidebar_button_names_<lang>.py` using string keys (e.g., "ProjectsModule").
- No JavaScript translation files are to be used for Python modules.
- All translation keys should be typo-proof and auto-completable by using string keys matching module class names.
- The `sidebar_button` method must be used for sidebar button translations in all new modules and UI components.
- If a translation is missing, the key itself is shown as a fallback.

## Module Implementation
- All new modules must use the `LanguageManager_NEW` class for all translation needs.
- Module registration and sidebar display must use the new language manager's `sidebar_button` method for human-readable names.
- No legacy translation systems (JSON, JS, or old LanguageManager) are to be used in new code.
- All translation files must be kept in the `languages/` directory and follow the naming convention: `<lang>.py` and `sidebar_button_names_<lang>.py`.

## Migration
- Existing modules should be migrated to use `LanguageManager_NEW` and Python-based translation files as time allows.
- Remove or ignore any `.js` translation files.

---

**Summary:**
- Use only Python translation files and `LanguageManager_NEW` for all new modules and UI.
- Sidebar button names must be managed via the new sidebar button translation system.
- No JavaScript or JSON translation files for new code.
