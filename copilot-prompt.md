# QGIS Plugin Coding Guidelines

## Table of Contents
1. Introduction & Scope
2. Architecture & Module System
3. Directory & File Structure
4. API, Data, and Query Standards
5. Centralized Path and Resource Management
6. UI/UX & Theming Guidelines
7. Translation & Localization
8. Coding Conventions & Best Practices
9. QGIS-Specific Rules
10. Documentation, Comments, and Safety
11. Appendix: Examples & Troubleshooting

---

## 1. Introduction & Scope
_Short summary of the plugin, its modular approach, and the purpose of these guidelines._

---

## 2. Architecture & Module System

- Use `BaseModule` as the base class for all new modules.
- Only one module is active at a time; modules are activated/deactivated via sidebar or menu.
- Each module must implement:  
  - `activate()`, `deactivate()`, `run()`, `reset()`, `get_widget()`
- UI and logic must be separated (ui.py, logic.py).
- Modules are lazy-loaded and registered via `ModuleManager`.
- Each module must have a unique name constant in `constants/module_names.py`.
- The plugin remembers last-used module and user settings using QSettings.
- Before creating new modules, check for reusability or extension of existing modules.

---

## 3. Directory & File Structure

- Each module must be in its own subdirectory under `modules/`.
- Required files: `__init__.py`, `ui.py`, `logic.py`, `translations/`
- Example:
  ```
  modules/
      JokeGenerator/
          __init__.py
          ui.py
          logic.py
          translations/
              joke_generator_en.json
              joke_generator_et.json
  ```
- Do not place new modules as single files in `modules/`.

---

## 4. API, Data, and Query Standards

- All API connections must use the central `APIClient` class.
- All data transfer must use session/token management via `SessionManager`.
- Use `PaginatedDataLoader` for large/unbounded lists; batch size must be configurable.
- All modules must use `GraphQLQueryLoader` for loading GraphQL queries.
- All file and directory paths for API queries, configs, and resources must be referenced via the central file path manager.
- Never use `requests` or `open()` directly in modules.

---

## 5. Centralized Path and Resource Management

- All file and directory paths (styles, QSS, translations, resources, etc.) must be referenced via `constants/file_paths.py`.
- Never hardcode or construct paths with `os.path` in modules or widgets.
- QSS filenames, theme directories, icons, and config/manuals must be referenced via constants.
- When adding paths for a module, always define the module name as a constant in `constants/module_names.py`.
- For web links and URLs, use `UrlManager.py` and `WebLinks`.

---

## 6. UI/UX & Theming Guidelines

### General Design
- Use dark theme as default; support seamless switching to light theme.
- All dialogs/widgets must have rounded corners and soft shadow borders.
- Always apply the shared stylesheet from `widgets/theme_manager.py`.
- Use centralized QSS files for theme-specific styling.

### Layout & Components
- Use `QVBoxLayout` for vertical flow, `QHBoxLayout` for inline controls.
- Use `QGroupBox` for grouping, `QFrame` for dividers.
- No absolute positioning; always use layouts.
- Place dialog decision buttons at the bottom-right.

### Typography & Colors
- Avoid inline styling; use `theme_manager.py` for dynamic styling.
- Standardize object names for widgets for QSS.
- Accent color: `rgb(9,144,143)`.

### QSS & Theme Files
- All style rules in `.qss` files, not inline.
- Each theme must have both `DarkTheme.qss` and `LightTheme.qss`.
- Use objectName selectors for component overrides.

---

## 7. Translation & Localization

- All user-facing text must be translatable using `LanguageManager`.
- Default language is Estonian (`et`); support dynamic language switching.
- Never hardcode UI strings; always use translation keys.
- Global translations in `languages/{lang}.json`.
- Module translations in `{module_name}_{lang}.json` in the module directory.
- `LanguageManager` merges global and module translations.

---

## 8. Coding Conventions & Best Practices

- Use Python 3.9+ syntax and PEP8 style.
- Use camelCase for variables/functions, PascalCase for classes.
- Avoid wildcard imports.
- Use relative imports (`.` and `..`) as appropriate.
- Group standard, PyQt5, and QGIS imports separately.
- All logic in helper classes; avoid business logic in UI classes.
- Use `@staticmethod` or `@classmethod` when instance state is not required.
- File names follow CamelCase.py convention.

---

## 9. QGIS-Specific Rules

- Supported QGIS version from 3.4.
- Use `iface` safely; check for layer/context availability.
- Always validate layers before accessing.
- Use `QgsFeatureRequest` for filtering; avoid full layer iteration.

---

## 10. Documentation, Comments, and Safety

- Every public method must have a docstring.
- Use `# TODO:` for future improvements.
- Keep comments concise and useful.
- Prefer explicit type checks and early returns.
- Never block the UI thread with long-running operations.

---

## 11. Appendix: Examples & Troubleshooting

- Place code snippets, file structure examples, and troubleshooting tips here.