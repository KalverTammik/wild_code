## Module UI Standard

**Rule:** All module `get_widget()` methods must return a `QWidget` instance, never a class. This ensures compatibility with `addWidget()` and prevents runtime errors. If a module needs to provide a new widget each time, it should instantiate and return it within `get_widget()`.

## Python edit safety (indentation & imports)
- Do not emit `self.*` or class member lines at top level. Keep member assignments inside methods with correct indentation.
- Preserve the current indentation level when editing inside a method. Avoid accidental dedent/outdent.
- Avoid inline imports inside functions/methods. Prefer top-of-file imports. If necessary, add a `# inline import: reason` comment.
- For Qt animations (e.g., `QPropertyAnimation`), always parent the animation and keep a reference on `self` to prevent garbage collection.
- After multi-line edits, re-check the file for syntax/indentation errors before finishing changes.
## Theme and QSS Requirements for All Modules

1. **Centralized Theme Management**
   - All theme logic (theme detection, toggling, QSS application) must use the shared `ThemeManager`.
   - All modules and widgets must use `ThemeManager.apply_module_style(widget, [QssPaths.VARIABLE])` for theming.
   - Never hardcode theme logic or QSS paths in individual modules/widgets. Never use direct `theme_dir` or `qss_files` logic.

2. **QSS File Structure**
   - All theme-specific QSS files must be placed in `styles/Light/` and `styles/Dark/` folders.
   - Each module/widget with custom styling must have its own QSS file (e.g., `NewModule.qss`).
   - Reusable chip/pill styling must live in `pills.qss` and be applied via `ThemeManager.apply_module_style(widget, [QssPaths.PILLS])`.

3. **Widget Styling**
   - Assign a unique `objectName` to any widget that needs custom QSS (e.g., `"NewModule"`).
   - Apply QSS using `ThemeManager.apply_module_style(widget, [QssPaths.VARIABLE])` for all such widgets. If the QSS variable does not exist, create a new QSS file and add it to `QssPaths`.

4. **Dynamic Restyling**
  - Any module that creates dynamic content (e.g., cards, list items) must implement a method to re-apply QSS to all such widgets (e.g., `rethem_[some logical name here]()`), and it should re-apply QSS via `ThemeManager.apply_module_style` to the module root and its cards.
  - After toggling the theme, the main dialog calls module retheme methods (e.g., `rethem_project()`, `retheme_settings()`, etc.).
  - Generic sweep: the dialog also calls `retheme()` on any child widget that exposes that method (found via `findChildren(QWidget)`), allowing widgets like `TagsWidget` to self-update without dialog-level imports. Widgets opt-in by implementing `retheme()`.

5. **Theme Toggle Integration**
   - The main dialog’s `toggle_theme` method must:
     - Call `ThemeManager.toggle_theme(...)` to update the global theme and header toggle icon.
     - Re-apply styles to top-level UI (header, sidebar, footer) via their dedicated `retheme_*` methods.
     - Call each active module’s retheme method (e.g., `rethem_project()`, `retheme_settings()`), which re-applies module/card QSS.
     - Finally, perform a generic sweep to invoke `retheme()` on any child widget that provides it (no class imports in dialog).

6. **No Direct QSS File Reading**
   - Do not read QSS files directly in modules. Always use `ThemeManager.apply_module_style`.

7. **Documentation**
   - All new modules/widgets must document how they support theme switching and QSS application. Add a docstring such as:
     - "This module supports dynamic theme switching via ThemeManager.apply_module_style."
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
- Required files: `__init__.py`, `[NewModuleName]Ui.py`, `[NewModuleName]logic.py`, `translations/`
- Example:
  ```
  modules/
      JokeGenerator/
          __init__.py
          ui.py
          logic.py
          translations/
              joke_generator_en.py
              joke_generator_et.py
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

**Always apply QSS themes using the following universal pattern in all modules and widgets:**

```python
from ..constants.file_paths import QssPaths
from ..widgets.theme_manager import ThemeManager
ThemeManager.apply_module_style(self, [QssPaths.SIDEBAR])  # Sidebar example
ThemeManager.apply_module_style(self, [QssPaths.MODULE_TOOLBAR])  # Toolbar example
ThemeManager.apply_module_style(self, [QssPaths.FOOTER])  # Footer example
ThemeManager.apply_module_style(self, [QssPaths.MAIN])    # Main/general example
ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.SIDEBAR])  # Composite example
```

**Always select the QSS file(s) that are appropriate for the specific widget or module you are developing—this pattern applies universally to both widgets and modules.**

**Never use direct theme_dir or qss_files logic. Always use ThemeManager.apply_module_style.**

This ensures correct and consistent theme application across the plugin.

### Initial Theme Load (REQUIRED)

- On dialog initialization, call `ThemeManager.set_initial_theme(dialog, switch_button, theme_base_dir, qss_files=[QssPaths.MAIN, QssPaths.SIDEBAR, QssPaths.HEADER, QssPaths.FOOTER])`.
- Each module should apply its own QSS to its root widget right after the UI is built, e.g. `theme_manager.apply_module_style(self.widget, [QssPaths.MAIN])` or a module-specific QSS.
- Widgets with custom QSS (like pills) must apply their QSS in `__init__` (e.g., `ThemeManager.apply_module_style(self, [QssPaths.PILLS])`) and implement `retheme()` to support live switching.

### New Module UI checklist

- Build the root widget and set layouts.
- Apply module QSS: `theme_manager.apply_module_style(self.widget, [QssPaths.MAIN] /* or module-specific */)`.
- Implement `rethem_[module]()` to re-apply module and card styles on theme toggle.
- If the module creates dynamic widgets (cards, lists), ensure those widgets implement `retheme()` when they have theme-dependent visuals (e.g., shadows) and/or call a helper to re-apply styles to children.
- The main dialog will call the module’s `rethem_*()` and also run a generic child `retheme()` sweep.

### Tags hover/popup handling (pills)

Purpose
- Show a small info icon in each card header; hovering reveals a lightweight popup with the item’s tags (styled as pills).

Key files
- `widgets/DataDisplayWidgets/ModuleFeedBuilder.py` — integrates the icon and popup in cards.
- `widgets/DataDisplayWidgets/TagsWidget.py` — renders tags as pills and exposes `retheme()`.
- `styles/Light/pills.qss`, `styles/Dark/pills.qss` — pill styling, referenced via `QssPaths.PILLS`.

Detection & integration
- Tags are extracted with `ModuleFeedBuilder._extract_tag_names(item)` from `item['tags']['edges'][i]['node']['name']`.
- `_item_has_tags(item)` guards whether to add the hover icon.
- In each card header: if the item has tags, add `TagsHoverButton(item)` next to the title.

Behavior
- Hover over the icon shows `TagPopup` directly below the icon; leaving the icon starts a short hide timer.
- The popup installs an event filter so it stays open while the cursor is over the popup or its children; leaving both areas hides it after a delay.
- `TagPopup` is a non-activating tool window: `Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint` and is reparented to the card’s top-level window for correct z-order in QGIS.
- The popup applies `ThemeManager.apply_module_style(self, [QssPaths.PILLS])` and calls `TagsWidget.retheme()` in `showEvent` to reflect theme changes.
- If an item has no tags, the popup closes immediately and no icon is added.

Tunables
- Hide delay when leaving the icon: `TagsHoverButton._hide_delay_ms` (default ~600 ms).
- Additional hide delay after leaving the popup (shorter, e.g. 350 ms) to tolerate small cursor gaps.
- Button size (20×20) and icon size (14×14) can be adjusted in `TagsHoverButton`.
- Popup anchoring offset (below the icon) can be tweaked in `TagPopup.show_near()` if visual alignment needs tuning.

Theming
- Do not inline styles; rely on `pills.qss` via `QssPaths.PILLS`.
- Ensure `TagsWidget` implements `retheme()` so pills update on theme toggle.

Edge cases
- Popup hidden behind the dialog: verify the popup is reparented to the top-level window and call `raise_()` after `show()`.
- Fast pointer movement causing flicker: increase the hide delays slightly.
- Items without tags: no hover icon is added.

Test checklist
- Hover over the icon → popup appears; move into popup → stays visible; leave both → hides after delay.
- Toggle theme while popup is open → pills restyle immediately.
- Scroll the feed with an open popup → behavior remains stable; reopen aligns to the icon.
- Same experience across Projects and Contracts cards.
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

---

## 12. Settings Architecture & Behavior

This plugin uses a structured, card-based Settings system with clear separation of concerns and centralized theming and translations.

Components
- `modules/Settings/SettingsUI.py` (orchestrator)
  - Owns the layout (scrollable list of SetupCards), theming reapplication, and dirty-state aggregation.
  - Creates one `UserCard` and 0..N `ModuleCard`s (one per visible module in sidebar).
  - Lifecycle:
    - `set_available_modules(module_names)` is called by the dialog to inform which module cards to build.
    - `activate()` loads the user via `SettingsLogic`, builds access pills, loads original settings, reflects preferred selection, and activates module cards.
    - `deactivate()` asks module cards to release memory.
  - Dirty-state and confirms:
    - User-card (preferred module change) shows a single confirm on that card.
    - Each ModuleCard manages its own confirm visibility via a `pendingChanged` signal.
    - `has_unsaved_changes()` returns true if either the user preferred has changed or any module card is dirty; used to guard navigation.
  - Theming: applies `QssPaths.MAIN` to itself and `QssPaths.SETUP_CARD` to each card; calls `card.retheme()` on theme toggle.

- `modules/Settings/SettingsLogic.py` (persistence, data mapping)
  - Loads user data through `GraphQLQueryLoader` and `APIClient`.
  - Parses roles and maps abilities to module access with `get_module_access_from_abilities()`.
  - Preferred module persistence via `QgsSettings` key `wild_code/preferred_module`.
  - Tracks original vs pending preferred and provides `apply_pending_changes()` / `revert_pending_changes()`.
  - Respects `set_available_modules()` when computing the access map so pills align with sidebar visibility.

- `modules/Settings/cards/UserCard.py` (user info, roles, access, preferred)
  - Shows ID, Name, Email, Roles (read-only pills) and Module access pills.
  - Preferred selector uses single-selection behavior implemented with `QCheckBox` (styled like radio via QSS). Allows unselecting all to prefer the Welcome page.
  - Emits `preferredChanged(str|None)` when selection changes.
  - API: `set_user()`, `set_roles()`, `set_access_map()`, `set_preferred()`, `revert()`, `retheme()`.

- `modules/Settings/cards/ModuleCard.py` (per-module settings)
  - Contains two layer selectors (Element/Archive) using the shared `LayerTreePicker` widget.
  - Signals `pendingChanged(bool)` to show/hide its own Confirm button.
  - API: `on_settings_activate(snapshot)`, `on_settings_deactivate()`, `apply()`, `revert()`, `has_pending_changes()`.

- `widgets/WelcomePage.py` (welcome when no preferred)
  - Displayed when there is no preferred module set.
  - Provides `openSettingsRequested` to jump into Settings.
  - Uses `LanguageManager` centrally; call `welcomePage.retranslate(lang_manager)` when language changes.

Flow
1. Dialog builds modules and sidebar, then passes visible modules to Settings via `set_available_modules`.
2. Entering Settings triggers `SettingsUI.activate()`:
   - Load user, set roles, compute access map, build access pills.
   - Load original preferred via logic, then call `UserCard.set_preferred(original)` to reflect it.
   - Build a shared layer-tree snapshot for all ModuleCards and call `on_settings_activate(snapshot)` on each.
3. Changing preferred or module settings marks dirty and shows per-card confirm(s).
4. Confirm applies and persists changes using logic and per-card apply handlers.
5. Leaving Settings or closing dialog prompts to save/discard when `has_unsaved_changes()` is true.

Notes
- Preferred key: `wild_code/preferred_module` (string module name). Removing the key means Welcome page on startup.
- Access mapping is extendable; ensure subjects map to module constants and are filtered by `available_modules`.
- When programmatically updating preferred, block signals on the checkboxes to avoid spurious dirty state.

---

## 13. Layer Selection Widget: LayerTreePicker (layer_dropdown.py)

Purpose
- Provide a memory-friendly, reusable, hierarchical layer picker with a familiar dropdown UX.

Files
- `widgets/layer_dropdown.py`
  - `build_snapshot_from_project(project=None)` produces a nested Python structure of the current QGIS layer tree.
  - `LayerTreePicker` is the widget that shows a button; clicking opens a Qt.Popup with a scrollable `QTreeWidget`.
  - `LayerDropdown` is a deprecated alias that inherits `LayerTreePicker` for backward compatibility.

Snapshot helpers
- `build_snapshot_from_project()` returns a nested list of dicts like:
  - Group: `{ "type": "group", "name": str, "children": [...] }`
  - Layer: `{ "type": "layer", "id": str, "name": str }`
- Internal `_snapshot_from_group(group_node)` recursively walks the QGIS layer tree.
- Pass the same snapshot to multiple pickers to avoid repeated tree traversal and reduce memory usage.

LayerTreePicker API
- ctor: `LayerTreePicker(parent=None, project=None, placeholder="Select layer")`
- Snapshot:
  - `setSnapshot(snapshot)` / `getSnapshot()`
- Project:
  - `project()` / `setProject(project)`
- Selection:
  - `selectedLayerId() -> str`
  - `selectedLayer() -> QgsMapLayer | None`
  - `setSelectedLayerId(layer_id: str)`
  - `clearSelection()`
- Lifecycle:
  - `on_settings_activate(snapshot=None)`
  - `on_settings_deactivate()`
- Signals:
  - `layerChanged(QgsMapLayer|None)`
  - `layerIdChanged(str)`

Behavior
- Initially shows a button with placeholder text.
- On click, opens a popup containing the hierarchical tree (groups and layers).
- Selecting a layer updates the button text, emits signals, and closes the popup.
- Supports lazy building: call `on_settings_activate(snapshot)` before display; call `on_settings_deactivate()` to release memory.

Integration pattern
- Build one snapshot per Settings activation and share:
```python
from ...widgets.layer_dropdown import build_snapshot_from_project
shared_snapshot = build_snapshot_from_project()
for card in module_cards:
    card.on_settings_activate(snapshot=shared_snapshot)
```
- In a card:
```python
self._element_picker = LayerTreePicker(self, placeholder=lang.translate("Select layer"))
self._archive_picker = LayerTreePicker(self, placeholder=lang.translate("Select layer"))
self._element_picker.layerIdChanged.connect(self._on_element_changed)
self._archive_picker.layerIdChanged.connect(self._on_archive_changed)
```

Styling
- The popup frame has objectName `LayerTreePopup`. Add QSS rules in your theme if you want to style it specially.

Deprecated
- `LayerDropdown` remains as an alias for compatibility but should not be used in new code. Prefer `LayerTreePicker`.

---

## 14. Icons & Themed Assets (REQUIRED)

- All UI icons must be theme-aware and resolved centrally. Do not hardcode absolute file paths in widgets or modules.
- Storage layout:
  - Base icons: `resources/icons/`
  - Theme variants (optional): `resources/icons/Light/` and `resources/icons/Dark/` with identical filenames
- Formats:
  - Prefer transparent PNG; SVG is supported as a fallback. Avoid any white/solid backgrounds.

### 14.1 Semantic basenames via ThemeManager
- Use semantic basenames exposed by `ThemeManager` (e.g., `ThemeManager.ICON_INFO`).
- Get a themed path or QIcon:
  - `ThemeManager.get_icon_path(ThemeManager.ICON_INFO)`
  - `ThemeManager.get_qicon(ThemeManager.ICON_INFO)`
- ThemeManager automatically picks a Light/Dark variant if present; otherwise falls back to the base in `resources/icons/`.

Example:
```python
from ..widgets.theme_manager import ThemeManager
button.setIcon(ThemeManager.get_qicon(ThemeManager.ICON_SAVE))
```

### 14.2 Module icons for the sidebar
- Module icons are centralized in `constants/module_icons.py` under `ModuleIconPaths.MODULE_ICONS`.
- Retrieve them with `ModuleIconPaths.get_module_icon(module_name)` (theme-aware).
- Do not reference module icon paths directly in UI code; let `ModuleManager`/`ModuleIconPaths` supply them.

Example:
```python
from ..constants.module_icons import ModuleIconPaths
icon_path = ModuleIconPaths.get_module_icon("ProjectsModule")
```

### 14.3 Themed path helper for generic icons
- For non-module assets when you need a path string, use `ModuleIconPaths.themed(<basename>)`.

Example:
```python
from ..constants.module_icons import ModuleIconPaths, ICON_SEARCH
path = ModuleIconPaths.themed(ICON_SEARCH)
```

### 14.4 Adding a new icon (checklist)
1) Download from Icons8 (Fluency Systems Regular) and keep the original filename or use lowercase kebab-case.
2) Place the file in `resources/icons/`.
3) (Optional) Add Light/Dark variants under `resources/icons/Light/` and `resources/icons/Dark/` using the same filename.
4) If it’s a generic UI icon, consider exposing a basename constant in `ThemeManager` for reuse; otherwise reference the basename directly where needed.
5) If it’s a module icon, add/update the mapping in `ModuleIconPaths.MODULE_ICONS`.
6) Never build absolute paths in UI code; always resolve via `ThemeManager` or `ModuleIconPaths`.

### 14.5 Rules and tips
- PNG preferred (transparent); SVG OK.
- Avoid background fills; ensure good contrast in both themes or provide variants.
- Do not duplicate file names between unrelated icons.
- Keep icons consistent with the Icons8 Fluency Systems Regular style.