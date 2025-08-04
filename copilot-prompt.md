# Copilot Prompt: QGIS Plugin Coding Guidelines

> 🧠 Tip: To help Copilot follow these rules more accurately, keep key files open while working. Copilot prioritizes context from open and recently edited files.

# Context: This plugin is for QGIS from fersion 3.49 and runs in PyQt5 with access to iface and QgsProject.

"""
You're helping me build a modular plugin system for a Qt-based (e.g., PyQt5 or QGIS) application.

Design Requirements:
1. Use `BaseModule` as the base class for all new modules. if importin use from .base_module import BaseModuel to aviod import mistakes.
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

## Layout Design Guidelines

### General Principles
- All UI layouts must follow a **structured, modular, and visually aligned** format.
- Do **not** use absolute positioning (`move()`, `setGeometry()`) — always use layouts.
- Layouts should reflect logical groupings of fields, actions, and labels.
- All dialogs must follow **top-down visual flow** using `QVBoxLayout`.

---

### Section Composition
- Use `QVBoxLayout` to structure the overall vertical flow of the dialog.
- Use `QHBoxLayout` for inline controls, action rows, or label+input pairs.
- Nest layouts as needed for granular control.

---

### Component Grouping
- Use `QGroupBox` to **group related controls** (e.g., "Location Info", "Work Details").
  - Each `QGroupBox` must have a clear, descriptive title.
  - Internally use `QVBoxLayout` or `QFormLayout` for aligned inputs.
- Use `QFrame` with `QFrame.HLine` or `QFrame.VLine` as **visual dividers** between sections.
- Use consistent internal spacing (`setSpacing(8)`) and margin padding (`setContentsMargins(8, 8, 8, 8)`).

---

### Button Rows
- Always place dialog decision buttons at the **bottom-right** using `QHBoxLayout`:



### Typography & Colors
- Avoid using inline styling; use `theme_manager.py` to handle styling dynamically.
- Ensure all text and background colors adapt to the active theme (dark or light).
- **Standardize object names for widgets** (e.g., `#PrimaryButton`, `#DialogTitle`, `#FormGroup`) and reflect these in QSS. This enables general, scalable, and maintainable styling across the plugin.
- For specific object-based styling, use these standardized object names in the QSS files.

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
- `styles/Dark/...`: Contains styles for the dark theme.
- `styles/Light/...`: Contains styles for the light theme.
- Ensure both QSS files define consistent styles for all widgets, dialogs, and frames.

## QSS Styling Guidelines

### General Rules
- All style rules must be defined in `.qss` files, not inline.
- Base styles belong in `styles/main.qss`.
- Component-specific styles are split by layout section:
  - `header.qss`, `sidebar.qss`, `login.qss`, `footer.qss`, etc.
  - if more component-specific styles are neccesery add file pointing to layout component

### Naming & Reuse
- Use `objectName` selectors (e.g., `#saveButton`, `#headerLabel`) for component overrides.
- Common styles (e.g., for `QPushButton`, `QLineEdit`, `QFrame`) must be declared globally in `main.qss`.

### Theme Switching
- Every theme must have both `DarkTheme.qss` and `LightTheme.qss` versions.
- File naming: `main.qss`, `main_light.qss`, `header.qss`, `header_light.qss`, etc.
- Apply themes dynamically via `theme_manager.py`.

### Limitations
- Qt QSS **does not support variables, nesting, or animations**.
- Do not use unsupported pseudo-elements (`::after`, `:not()`).

## Theme Color Usage Rules

### General Principles
- Maintain a consistent **color palette** for both dark and light themes.
- All colors must be declared in centralized QSS files (`main.qss`, `main_light.qss`).
- Accent color: `rgb(9,144,143)` — shared across themes as primary brand highlight.
- Avoid hardcoded inline `setStyleSheet()` calls with color values.

### Color Roles (informal naming)
| Role              | Dark Theme        | Light Theme       |
|-------------------|-------------------|-------------------|
| Main BG           | `#1d252b`         | `#ffffff`         |
| Input BG          | `#303a42`         | `#f5f5f5`         |
| Text              | `#c5c5d2`         | `#333333`         |
| Disabled BG       | `#24252e`         | `#e0e0e0`         |
| Button (normal)   | `rgb(9,144,143)`  | `rgb(9,144,143)`  |
| Button Hover      | `#004d40`         | `#00796b`         |
| Button Pressed    | `#2d2e3a`         | `#cccccc` |
| Focus Border      | `#0b4544`         | `#0078d4`         |

### Contrast & Accessibility
- Button hover/pressed states must have at least **4.5:1 contrast** against base background.
- Use hover styles that include color *and* shadow/border feedback.

### Reference
- [Qt Style Sheet Reference](https://doc.qt.io/qt-5/stylesheet-reference.html)
- [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/quickref/#contrast-minimum)


### Component Rules
- Buttons (`QPushButton`) must use consistent padding, font, and hover styles.
- Inputs (`QLineEdit`, `QTextEdit`) must have defined focus, hover, and disabled states.
- Section layouts should use rounded borders, dividers (`QFrame.HLine`), and consistent spacing.

### Example
```css
/* main.qss */
QLineEdit {
    background-color: #303a42;
    color: #ececf1;
    border: 1px solid #0b4544;
    border-radius: 5px;
    padding: 6px;
}


### Web Link and Module URL Management
- All static and module-related URLs are managed centrally in UrlManager.py.
- Static links (home, privacy, terms, etc.) are loaded from config.json and accessed via the WebLinks class.
- Module-specific URLs are defined in the Module enum and WebModules class, and full URLs are built using the OpenLink class.
- To add a new module or link, update the enum/class and/or config.json—no need to hardcode URLs throughout the codebase.
- To open any link in the browser, use the loadWebpage.open_webpage(url) utility.

## Resource and Theme Integration Checklist

**Always use the centralized resource management classes from `constants/file_paths.py`:**

- **Icons/Images:** Use `ResourcePaths` (e.g., `ResourcePaths.ICON`, `ResourcePaths.EYE_ICON`)
- **QSS/Theme Files:** Use `QssPaths` (e.g., `QssPaths.LIGHT_THEME`, `QssPaths.DARK_THEME`, `QssPaths.LOGIN`)
- **Config/Manuals:** Use `ConfigPaths` (e.g., `ConfigPaths.CONFIG`, `ConfigPaths.METADATA`, `ConfigPaths.USER_MANUAL`)
- **Module Icons:** Use `ModuleIconPaths.get_module_icon(module_name)` or `ModuleIconPaths.MODULE_ICONS[...]`

**Never hardcode file paths or QSS filenames in modules. Always reference them via the appropriate class.**

**To apply a theme or QSS:**

- Use `ThemeManager.apply_theme(self, QssPaths.LIGHT_THEME)` or the relevant QSS path.
- For modular QSS, pass a list of QSS files from `QssPaths` as needed.

**When adding a new module:**

- If your module needs a unique icon, add it to `ModuleIconPaths.MODULE_ICONS` in `file_paths.py`.
- If your module needs a user manual or config, add the path to `ConfigPaths`.

**For web links and URLs:** Use `UrlManager.py` and `WebLinks` for all static/module URLs.