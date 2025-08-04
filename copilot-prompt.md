# Copilot Prompt: QGIS Plugin Coding Guidelines

> 🧠 Tip: To help Copilot follow these rules more accurately, keep key files open while working. Copilot prioritizes context from open and recently edited files.

# Context: This plugin is for QGIS from fersion 3.49 and runs in PyQt5 with access to iface and QgsProject.

"""
You're helping me build a modular plugin system for a Qt-based (e.g., PyQt5 or QGIS) application.

Design Requirements:
1. Use `BaseModule` as the base class for all new modules.
2. The plugin has multiple **modules**, but only one is active at a time.
3. Each module has:
   - A toolbar/header area with buttons and dropdowns (inputs)
   - A result/output display area (tables, logs, previews, etc.)
   - A consistent layout
4. The plugin has a central UI that switches between modules (use QStackedWidget or QTabWidget).
5. Modules should be activatable/deactivatable via a sidebar or menu system.
6. Each module must:
   - Implement `activate()`, `deactivate()`, `run()`, and `reset()` methods as needed.
   - Set up its UI within the `__init__` method using `self.widget`.
   - Provide `get_widget()` to return the module’s main QWidget.
   - have  a unique name for the module in `module_manager.py` ( and use it like. `self.name = JOKE_GENERATOR_MODULE`)
7. All module UIs follow a uniform dark theme and layout conventions.
8. Module logic and UI are separated (logic.py and ui.py per module).
9. The plugin remembers the last-used module and user settings using QSettings.
10. Modules are lazy-loaded and registered via a `ModuleManager`.


## Additional Requirements
- Before creating new modules or components, check if existing modules can be reused or extended.
- Always consult this prompt to ensure compliance with design and coding guidelines.
- Avoid duplicating functionality; prefer refactoring or reusing existing modules.
- Avoid using frameless windows. Ensure all dialogs and modules use standard window decorations for better compatibility and usability.
- For user authentication:
  - Use `login_dialog.py` to handle the login process.
  - Upon successful login, initialize and activate the required modules using `BaseModule`.
- For translations, use `LanguageManager` to dynamically update UI text.
- Maintain simplicity and modularity to ensure easy integration and testing.
- Discard `dialog.py` and migrate any reusable features (e.g., menu systems) to `BaseModule` or utility classes.

## General Rules
- Always use **Python 3.9+** syntax.
- Follow **PEP8** style guide (4-space indent, max line length ~100).
- Use **camelCase** for variable and function names.
- Use **PascalCase** for class names.
- Avoid wildcard imports (`from x import *`).
- Use `.` for first-level directories and `..` for second-level directories when importing modules (e.g., `from .module import ClassName` or `from ..subpackage.module import FunctionName`).
- Group standard, PyQt5, and QGIS imports separately.

## PyQt5 UI Guidelines
- Prefer `QVBoxLayout` and `QHBoxLayout` over absolute positioning.
- All UI components must use consistent **dark theme** styles.
- Use `QPushButton`, `QLabel`, `QGroupBox`, `QFrame`, and `QDialog` with custom-styled frames.
- Always subclass `QDialog` or `QWidget` when creating custom dialogs.

## QGIS-Specific
- Supported QGis version from 3.4
- Use `iface` safely: check for layer/context availability before use.
- Always validate layers (`if not layer or not layer.isValid():`) before accessing.
- Use `QgsFeatureRequest` for efficient feature filtering.
- Avoid full layer iteration unless necessary; use `getFeatures()` with filters.

## Architecture and Design
- All logic goes in helper classes (e.g., `LayerHelper`, `DialogHelper`, etc.).
- Avoid business logic inside UI classes.
- Use `@staticmethod` or `@classmethod` when instance state is not required.
- File names follow `CamelCase.py` convention (e.g., `LayerGroupHelper.py`).
- Organize by feature: UI, logic, data, helpers.

## Documentation and Comments
- Every public method must have a docstring.
- Use `# TODO:` for future improvements.
- Keep comments concise and useful.

## Safety and Performance
- Prefer explicit type checks and early returns.
- Never block the UI thread with long-running operations.

---

## UI Design Rules

### General Design
- Use **dark theme** as default, but ensure seamless switching between **dark** and **light** themes.
- All dialogs and widgets must have **rounded corners** and **soft shadow borders**.
- Avoid mixing native widget styles with custom-styled elements.
- Always apply the shared stylesheet from `widgets/theme_manager.py`.
- Use centralized QSS files (`styles/DarkTheme.qss` and `styles/LightTheme.qss`) for theme-specific styling.
- No inline styling unless absolutely necessary; prefer centralized QSS.

### Layouts
- Use `QVBoxLayout` for vertical stacking of sections and `QHBoxLayout` for horizontal controls.
- Never use absolute positioning.
- Group related fields in `QGroupBox` with consistent spacing and titles.
- Use `QFrame` for visual separation of content sections (e.g., headers/footers).

### Typography & Colors
- Avoid using inline styling; use `theme_manager.py` to handle styling dynamically.
- Ensure all text and background colors adapt to the active theme (dark or light).
- For specific object-based styling, use object names (e.g., `#myobject`) in the QSS files.

### Buttons and Interaction
- Use a primary action button with teal glow (e.g., **Save**, **Apply**) that adapts to the active theme.
- Secondary buttons (e.g., **Cancel**) are flat with muted colors, consistent with the active theme.
- Add a hover state with subtle glow or border highlight, ensuring it matches the theme.
- Dialogs must have consistent button placement (e.g., **OK/Cancel** right-aligned at bottom).

### Dialog Frames
- Subclass `QDialog` or `QWidget` for all custom dialogs.
- Ensure dialogs dynamically apply the active theme using `theme_manager.py`.

---


### Theme Manager
- Use `widgets/theme_manager.py` to handle theme switching and apply styles dynamically on new module UIs.
- Ensure that each new module responds to theme changes as described in theme_manager


### QSS Files

Base themes are:
- `styles/DarkTheme.qss`: Contains styles for the dark theme.
- `styles/LightTheme.qss`: Contains styles for the light theme.
- Ensure both QSS files define consistent styles for all widgets, dialogs, and frames.

### Web Link and Module URL Management
- All static and module-related URLs are managed centrally in UrlManager.py.
- Static links (home, privacy, terms, etc.) are loaded from config.json and accessed via the WebLinks class.
- Module-specific URLs are defined in the Module enum and WebModules class, and full URLs are built using the OpenLink class.
- To add a new module or link, update the enum/class and/or config.json—no need to hardcode URLs throughout the codebase.
- To open any link in the browser, use the loadWebpage.open_webpage(url) utility.
