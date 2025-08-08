## Theme and QSS Requirements for All Modules

1. **Centralized Theme Management**
   - All theme logic (theme detection, toggling, QSS application) must use the shared `ThemeManager`.
   - Never hardcode theme logic or QSS paths in individual modules/widgets.

2. **QSS File Structure**
   - All theme-specific QSS files must be placed in `styles/Light/` and `styles/Dark/` folders.
   - Each module/widget with custom styling must have its own QSS file (e.g., `project_card.qss`).

3. **Widget Styling**
   - Assign a unique `objectName` to any widget that needs custom QSS (e.g., `"ProjectCard"`).
   - Apply QSS using `ThemeManager.apply_theme(widget, theme_dir, [qss_file])` for all such widgets.

4. **Dynamic Restyling**
   - Any module that creates dynamic content (e.g., cards, list items) must implement a method to re-apply QSS to all such widgets (e.g., `restyle_project_cards()`).
   - After toggling the theme, the main dialog must call these restyle methods for all active modules.

5. **Theme Toggle Integration**
   - The main dialog’s `toggle_theme` method must:
     - Call `ThemeManager.toggle_theme(...)` to update the global theme.
     - Call each module’s restyle method (e.g., `projectsModule.on_theme_toggled()`) to update all content.

6. **No Direct QSS File Reading**
   - Do not read QSS files directly in modules. Always use `ThemeManager.apply_theme`.

7. **Documentation**
   - All new modules/widgets must document how they support theme switching and QSS application.
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

**All new modules must inherit from `BaseModule`.**
**Do not use class-level attributes for `name`, `display_name`, or `icon`. Always set these as instance attributes in the constructor.**
**The constructor for every module must accept `name`, `display_name`, `icon`, `lang_manager`, and `theme_manager` as arguments, and assign them to `self.name`, `self.display_name`, and `self.icon`.**
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


### Project Rule: Building New API Requests

**When to use `APIClient`:**
- Always use the central `APIClient` class for any API or GraphQL request in modules, widgets, or helpers.
- Never use `requests` or `open()` directly in any module, widget, or helper—these are only allowed inside `APIClient`.
- All authentication/session handling must go through `SessionManager` (used by `APIClient`).


**What to create when building a new API request:**
1. **GraphQL Query File:**
   - Place your query in a `.graphql` file in the appropriate `queries/` subdirectory.
   - Use modular GraphQL fragments for any field set used in more than one query (e.g., `ProjectFields`, `PropertyFields`).
   - Store all reusable fragments in `queries/graphql/fragments/` for global use across modules (e.g., projects, contracts, properties).
   - Import fragments into your main queries using the loader's convention (e.g., `# import ProjectFields from '../fragments/ProjectFields.graphql'`).
   - Load queries using `GraphQLQueryLoader`.
2. **API Call:**
   - Use `APIClient.send_query(query, variables, require_auth=True)` to send the request.
   - Do not build or send HTTP requests manually.
   - Do not trigger API requests in the module constructor. Always defer data loading until the user activates or interacts with the module (e.g., in the `activate()` method).
3. **Error Handling:**
   - Always handle errors using the language manager for user-facing messages.
   - Use the error structure and translation patterns in `APIClient`.
4. **Path Management:**
   - Reference all file paths (queries, configs, etc.) via `constants/file_paths.py`.
5. **Session/Token:**
   - If authentication is required, ensure `require_auth=True` and that the session is valid.

**Fragment Guidelines:**
- Always check for and use global fragments before creating new ones.
- Place all reusable fragments in the global `fragments/` directory.
- Name fragments clearly and keep them focused on a single entity (e.g., `ProjectFields`, `PropertyFields`).
- Document new fragments for discoverability and maintainability.

**Summary:**
- All API requests must be routed through `APIClient`.
- All queries must be loaded via `GraphQLQueryLoader`.
- Never hardcode URLs, tokens, or file paths—use constants and managers.
- Follow the error and translation patterns established in `APIClient`.

This ensures all API interactions are secure, maintainable, and consistent across the project.

---

## 5. Centralized Path and Resource Management

- All file and directory paths (styles, QSS, translations, resources, etc.) must be referenced via `constants/file_paths.py`.
- Never hardcode or construct paths with `os.path` in modules or widgets.
- QSS filenames, theme directories, icons, and config/manuals must be referenced via constants.
- When adding paths for a module, always define the module name as a constant in `constants/module_names.py`.
- For web links and URLs, use `UrlManager.py` and `WebLinks`.

---

## 6. UI/UX & Theming Guidelines
### Theme Application Pattern (REQUIRED)

**Always apply QSS themes using the following pattern in all modules and widgets:**


1. Determine the current theme:
    ```python
    theme = ThemeManager.load_theme_setting()
    ```
2. Set the theme directory:
    ```python
    from ..constants.file_paths import StylePaths
    theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT
    ```

3. Apply the theme using the correct directory and a list of QSS files that match the context of your widget or module:
    ```python
    from ..constants.file_paths import QssPaths
    # For any widget or module, select the QSS file(s) that best match its purpose:
    #   - For a toolbar widget or module: [QssPaths.MODULE_TOOLBAR]
    #   - For a sidebar widget or module: [QssPaths.SIDEBAR]
    #   - For a footer widget or module:  [QssPaths.FOOTER]
    #   - For a main window or general UI: [QssPaths.MAIN]
    #   - For custom or composite UIs, combine as needed:
    ThemeManager.apply_theme(self, theme_dir, [QssPaths.SIDEBAR])  # Sidebar example
    ThemeManager.apply_theme(self, theme_dir, [QssPaths.MODULE_TOOLBAR])  # Toolbar example
    ThemeManager.apply_theme(self, theme_dir, [QssPaths.FOOTER])  # Footer example
    ThemeManager.apply_theme(self, theme_dir, [QssPaths.MAIN])    # Main/general example
    ThemeManager.apply_theme(self, theme_dir, [QssPaths.MAIN, QssPaths.SIDEBAR])  # Composite example
    ```

**Always select the QSS file(s) that are appropriate for the specific widget or module you are developing—this pattern applies universally to both widgets and modules.**

**Never pass a QSS file name as the theme_dir argument. Always use the theme directory and a list of QSS file names.**

**Example for a custom widget:**
```python
theme = ThemeManager.load_theme_setting()
theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT
ThemeManager.apply_theme(self, theme_dir, [QssPaths.SIDEBAR])
```

This ensures correct and consistent theme application across the plugin.
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

- All modules must use `LanguageManager` from `language_manager.py` for translations.
- Translation files must be Python files (`.py`), not JSON or JS.
- Each module must keep its translations in `modules/ModuleName/lang/en.py`, `et.py`, etc. (one file per language per module).
- Sidebar button names must be defined in `languages/sidebar_button_names_<lang>.py` using string keys matching module class names (e.g., "ProjectsModule").
- No JavaScript or JSON translation files are to be used for Python modules.
- All translation keys should be typo-proof and auto-completable by using string keys matching module class names.
- The `sidebar_button` method must be used for sidebar button translations in all new modules and UI components.
- If a translation is missing, the key itself is shown as a fallback.
- No legacy translation systems (JSON, JS) are to be used in new code.
- All translation files for sidebar/global keys must be kept in the `languages/` directory and follow the naming convention: `<lang>.py` and `sidebar_button_names_<lang>.py`.


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

---

## Example: Setting Up Translations in a Module

When setting up translations for a new module, follow these steps:

1. Import the `LanguageManager`:
    ```python
    from languages.language_manager import LanguageManager
    ```

2. Initialize the language manager with the desired language (e.g., Estonian):
    ```python
    lang = LanguageManager(language="et")
    ```

3. Set the text of your labels or other translatable strings using the `translate` or `sidebar_button` method:
    ```python
    label.setText(lang.translate("project_description_placeholder"))
    label.setText(lang.sidebar_button("ProjectsModule"))
    ```

4. Ensure that your translation files are named correctly and placed in the module's lang directory:
    - `modules/ProjectCard/lang/en.py` for English translations for ProjectCard module.
    - `modules/ProjectCard/lang/et.py` for Estonian translations for ProjectCard module.
    - `languages/sidebar_button_names_et.py` for the Estonian sidebar button names.

5. In your module's UI code, make sure to use the `LanguageManager` for any translatable text or labels.

By following these steps, your module will support translations seamlessly, and the sidebar buttons will be correctly labeled in the selected language.

## Module Creation & Registration Guidelines


When adding a new module, follow these unified steps to ensure consistency and avoid registration errors:

1. **Module Structure**
    - Each module must be in its own subdirectory under `modules/` with the required files: `__init__.py`, `ui.py`, `logic.py`, and a `lang/` directory for translations.
    - Do not place new modules as single files in `modules/`.


2. **Class Definition**
    - Inherit from `BaseModule`.
    - The module must define a unique `name` as a class attribute (e.g., `name = "MyModuleName"`).
    - The constructor should accept any needed managers (e.g., `lang_manager`, `theme_manager`) and other dependencies.
    - Implement all required methods: `activate`, `deactivate`, `run`, `reset`, `get_widget`.
    - Use `lang_manager.translate()` for all user-facing strings, including `display_name` if needed.

3. **Translations**
    - Use `LanguageManager` for all translations.
    - Translation files must be Python files (`.py`) and placed in the module's `lang/` directory (e.g., `modules/ProjectCard/lang/en.py`).
    - Sidebar button names must be defined in `languages/sidebar_button_names_<lang>.py` using string keys matching module class names.


4. **Registration & Integration**
    - **You must import, instantiate, and register the new module in the `loadModules` method of your main dialog (e.g., `dialog.py`).**
    - Register the module using only the module instance: `registerModule(moduleInstance)`.
    - Do **not** pass keyword arguments like `name`, `display_name`, or `icon` to `registerModule()` unless the method signature in `module_manager.py` explicitly supports them.
    - Each module must provide a `get_widget()` method that returns the QWidget to display.
    - The `registerModule` method will automatically handle the icon and display name for the sidebar using the module's `name` class attribute and the language manager. You do not need to set `display_name` or `icon` in your module unless you want to override the defaults.
    - Before registering a module, always check the current signature of `registerModule()` in `module_manager.py`.
    - If you need to support extra metadata, update the method and all usages accordingly.
    - If you see `TypeError: registerModule() got an unexpected keyword argument`, remove all extra arguments and follow these rules.

**Important:** If you do not add your new module to the `loadModules` method, it will not be registered, will not appear in the sidebar, and will not be usable in the plugin. Always update `loadModules` when adding a new module.

**Example module skeleton:**
```python
from .BaseModule import BaseModule

class ExampleModule(BaseModule):
    def __init__(self, name, display_name, icon, lang_manager, theme_manager):
        super().__init__(name, display_name, icon, lang_manager, theme_manager)
        # ... module-specific initialization ...
    def activate(self):
        pass
    def deactivate(self):
        pass
    def run(self):
        pass
    def reset(self):
        pass
    def get_widget(self):
        return self.widget
```

These rules ensure all modules are created, structured, and registered consistently in the wild_code plugin.