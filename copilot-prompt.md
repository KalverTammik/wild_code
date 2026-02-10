# === DEV NOTES: PYTHON PATCHING & INDENTATION RULES ===
**CODEBASE STATUS: PRODUCTION-READY** - All development artifacts removed, lazy loading working, consolidated architecture.
- Always use 4 spaces for indentation (never tabs)
- All method bodies must be fully indented inside their class
- Never leave stray code outside class or function scope
- If editing, always read the full method and class structure first!
- Always check for stray lines after patching, especially at file end
- [Add your environment-specific rules here]
# ================================================
## Module UI Standard

**Rule:** All module `get_widget()` methods must return a `QWidget` instance, never a class. This ensures compatibility with `addWidget()` and prevents runtime errors. If a module needs to provide a new widget each time, it should instantiate and return it within `get_widget()`.

## Python edit safety (indentation & imports)
- Do not emit `self.*` or class member lines at top level. Keep member assignments inside methods with correct indentation.
- Preserve the current indentation level when editing inside a method. Avoid accidental dedent/outdent.
- Avoid inline imports inside functions/methods. Prefer top-of-file imports. If necessary, add a `# inline import: reason` comment.
- For Qt animations (e.g., `QPropertyAnimation`), always parent the animation and keep a reference on `self` to prevent garbage collection.
- After multi-line edits, re-check the file for syntax/indentation errors before finishing changes.


# QGIS Plugin Coding Guidelines

## Table of Contents
1. Introduction & Scope
2. Architecture & Module System
3. Directory & File Structure
4. API, Data, and Query Standards
5. Centralized Path and Resource Management
6. UI/UX & Theming Guidelines
7. Help System
8. Translation & Localization
9. Coding Conventions & Best Practices
10. QGIS-Specific Rules
11. Documentation, Comments, and Safety
12. Appendix: Examples & Troubleshooting
13. Settings Architecture & Behavior
14. Centralized Settings Management
15. Layer Selection in SettingsModuleCard
16. Icons & Themed Assets (REQUIRED)

---

## 1. Introduction & Scope
_Short summary of the plugin, its modular approach, and the purpose of these guidelines._

---

## 2. Architecture & Module System

**Module contract:** A module is any QWidget-backed class that implements `activate()`, `deactivate()`, (optional) `run()`/`reset()`, and `get_widget()`; it does not need to inherit from `BaseModule` (that stub is legacy and currently unused). Always set `self.name`/`self.module_key` inside `__init__` so ModuleManager and analytics agree on identifiers.

### 2.1 Registration & lifecycle
- Register modules through `ModuleManager.registerModule(cls, Module.ENUM.name, **init_params)` as done in `dialog.py`. The manager stores metadata (`supports_statuses`, `supports_types`, `supports_tags`, icon paths) and lazily instantiates the class the first time it is activated.
- The sidebar reads this metadata to build buttons. Provide accurate support flags so `ModuleBaseUI` can decide which filters to show and which saved preferences to load.
- Only one module is active at a time. `activate()` is called when the sidebar selects a module; `deactivate()` runs on the previously active instance. Always call `super().activate()` / `super().deactivate()` if you subclass a shared base.
- Return the live widget instance from `get_widget()` so `moduleStack.addWidget()` can embed it. Do not return classes or create a new widget per call.

### 2.2 Feed modules built on `ModuleBaseUI`
Most sidebar feeds (`ProjectsModule`, `ContractsModule`, `SignalTestModule`) subclass `ui/ModuleBaseUI.py`, which already mixes in:
- Progressive feed loading (`FeedLoadEngine`), dedupe tracking, and viewport-aware auto-dripping
- Toolbar scaffolding via `ModuleToolbarArea`, refresh button wiring through `FilterRefreshHelper`, and stored preferences through `SettingsLogic`
- Helper hooks like `_build_has_tags_condition`, `_get_saved_*_ids()`, `_safe_extract_item_id()`

Implementation checklist:
1. Define `module_key = Module.<NAME>.name.lower()` and `self.name = self.module_key` inside `__init__`.
2. Declare `FEED_LOGIC_CLS` (usually `UnifiedFeedLogic`) and a `QUERY_FILE`. Lazily instantiate `self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)` inside `activate()` or filter refresh paths, and call `configure_single_item_query(...)` if the module supports opening a single card from search.
3. Build the toolbar in `__init__`: add whichever filter widgets the module supports, keep them in `self._filter_widgets`, and connect each `selectionChanged` signal to a `_refresh_filters()` helper.
4. Implement `load_next_batch()` as `return self.process_next_batch(retheme_func=...)`. `ModuleBaseUI.activate()` ensures the shared `FeedLoadEngine` is initialized with `self.load_next_batch` and wires scroll handling.
5. Inside `_refresh_filters`, read the widget selections (or fall back to `_get_saved_*_ids()`), translate them into a GraphQL `where` dict plus optional `hasTags` payload via `_build_has_tags_condition`, and pass both into `self.feed_logic.set_where(...)` / `set_extra_arguments(...)`. Always reset the feed UI via `self.clear_feed(...)` and schedule a load through `self.feed_load_engine.schedule_load()`.
6. Store pills or secondary controls (overdue/due soon) on the toolbar’s right side, and reuse `_apply_where()` helpers to combine them with the current base filters.

### 2.3 Non-feed / bespoke modules
Some modules (e.g., `PropertyModule`) present a single detail view instead of a scrollable feed. These classes can inherit `QWidget` directly as long as they honor the same activation contract and return themselves from `get_widget()`. They may still use shared helpers (theme manager, settings logic), but they own their own layouts and data loading patterns.

### 2.4 Feed logic responsibilities
- `feed/FeedLogic.py` provides `UnifiedFeedLogic`, the standard GraphQL paginator. Modules should never send raw requests; instead configure `query_name`, `batch_size`, `set_where(...)`, and `set_extra_arguments(...)`. Toggle single-item mode via `set_single_item_mode(True, id=...)` when responding to search deep-links.
- `feed/feed_load_engine.py` buffers items, debounces calls to `load_next_batch`, and coordinates with `ModuleBaseUI` to drip cards until the viewport is “filled + 1”. Let `ModuleBaseUI` create and own the engine—only call `self.feed_load_engine.schedule_load()` / `reset()` from modules.

Before creating a new module, decide whether it should piggyback on `ModuleBaseUI` (for feeds) or be a bespoke QWidget (detail dashboards, settings-like UIs), and reuse existing helper patterns whenever possible.

---

## 3. Directory & File Structure

- Each module must be in its own subdirectory under `modules/`.
- Required files: `__init__.py`, `[NewModuleName]Ui.py`, `[NewModuleName]logic.py`
- Example:
  ```
  modules/
      JokeGenerator/
          __init__.py
          ui.py
          logic.py
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
- When filtering feed data by tags, always define/extend the query to accept a `hasTags` variable (type `QueryProjectsHasTagsWhereHasConditions`), build its payload via `ModuleBaseUI._build_has_tags_condition()` (supports `ANY`/`ALL`), and pass it through `FeedLogic.set_extra_arguments(hasTags=payload)` so pagination honors the same filter.

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

### Help System

**All help functionality must use the centralized ShowHelp utility class.**

```python
from ..utils.help.ShowHelp import ShowHelp
ShowHelp.show_help_for_module(active_module)
```

**Key Guidelines:**
- Never implement help logic directly in UI components
- Always delegate to `ShowHelp.show_help_for_module(active_module)`
- The active module is obtained via `ModuleManager().getActiveModule()`
- Help URLs are determined based on the current module and opened in the system browser
- Dialog connects header help button: `self.header_widget.helpRequested.connect(self._on_help_requested)`

**ShowHelp Class:**
- Located in `utils/help/ShowHelp.py`
- Provides `show_help_for_module(module_info)` static method
- Handles URL determination and browser opening
- Uses `ModuleManager` to get current module context

---

## 8. Translation & Localization

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

## 9. Coding Conventions & Best Practices

- Use Python 3.9+ syntax and PEP8 style.
- Use camelCase for variables/functions, PascalCase for classes.
- Avoid wildcard imports.
- Use relative imports (`.` and `..`) as appropriate.
- Group standard, PyQt5, and QGIS imports separately.
- All logic in helper classes; avoid business logic in UI classes.
- Use `@staticmethod` or `@classmethod` when instance state is not required.
- File names follow CamelCase.py convention.
- Regularly review and remove unnecessary method abstractions; inline simple operations to reduce method call overhead.
- Use ModernMessageDialog methods for user notifications instead of QMessageBox directly:
  - `ModernMessageDialog.Info_messages_modern(title, message)` - Information messages with ℹ️ icon
  - `ModernMessageDialog.Warning_messages_modern(title, message)` - Warning messages with ⚠️ icon  
  - `ModernMessageDialog.Error_messages_modern(title, message)` - Error messages with ❌ icon
  - `ModernMessageDialog.Message_messages_modern(title, message)` - General messages with 💬 icon
- Remove unused parameters and empty callback methods that are leftover from development iterations.

---

## 10. QGIS-Specific Rules

- Supported QGIS version from 3.4.
- Use `iface` safely; check for layer/context availability.
- Always validate layers before accessing.
- Use `QgsFeatureRequest` for filtering; avoid full layer iteration.

---

## 11. Documentation, Comments, and Safety

- Every public method must have a docstring.
- Use `# TODO:` for future improvements.
- Keep comments concise and useful.
- Prefer explicit type checks and early returns.
- Never block the UI thread with long-running operations.
- Document code cleanup decisions in commit messages when removing unnecessary abstractions.
- Use `# CLEANUP:` comments for temporary notes about methods pending removal.

---

## 12. Appendix: Examples & Troubleshooting

- Place code snippets, file structure examples, and troubleshooting tips here.

---

## 13. Settings Architecture & Behavior

This plugin uses a structured, card-based Settings system with clear separation of concerns and centralized theming and translations.

Components
- `modules/Settings/SettingsUI.py` (orchestrator)
  - Owns the layout (scrollable list of SetupCards), theming reapplication, and dirty-state aggregation.
  - Creates one `UserCard` and 0..N `ModuleCard`s (one per visible module in sidebar).
  - Lifecycle:
    - `activate()` loads the user via `SettingsLogic`, builds access pills, loads original settings, reflects preferred selection, and activates module cards.
    - `deactivate()` asks module cards to release memory.
  - Module card building: Uses global `MODULES_LIST_BY_NAME` to iterate over available modules, filtering out HOME module.
  - Dirty-state and confirms:
    - User-card (preferred module change) shows a single confirm on that card.
    - Each ModuleCard manages its own confirm visibility via a `pendingChanged` signal.
    - `has_unsaved_changes()` returns true if either the user preferred has changed or any module card is dirty; used to guard navigation.
  - Theming: applies `QssPaths.MAIN` to itself and `QssPaths.SETUP_CARD` to each card; calls `card.retheme()` on theme toggle.

- `modules/Settings/SettingsLogic.py` (persistence, data mapping)
  - Loads user data through `GraphQLQueryLoader` and `APIClient`.
  - Parses roles and maps abilities to module access with `get_module_access_from_abilities()`.
  - Preferred module persistence via `QgsSettings` key `kavitro/preferred_module`.
  - Tracks original vs pending preferred and provides `apply_pending_changes()` / `revert_pending_changes()`.
  - Uses global `MODULES_LIST_BY_NAME` for module access filtering instead of local available modules list.

- `modules/Settings/cards/UserCard.py` (user info, roles, access, preferred)
  - Shows ID, Name, Email, Roles (read-only pills) and Module access pills.
  - Preferred selector uses single-selection behavior implemented with `QCheckBox` (styled like radio via QSS). Allows unselecting all to prefer the Welcome page.
  - Emits `preferredChanged(str|None)` when selection changes.
  - API: `set_user()`, `set_roles()`, `set_access_map()`, `set_preferred()`, `revert()`, `retheme()`.

- `modules/Settings/cards/ModuleCard.py` (per-module settings)
  - Contains two layer selectors (Element/Archive) backed by `QgsMapLayerComboBox` widgets tied directly to the active project.
  - Signals `pendingChanged(bool)` to show/hide its own Confirm button.
  - API: `on_settings_activate()`, `on_settings_deactivate()`, `apply()`, `revert()`, `has_pending_changes()`.

- `widgets/WelcomePage.py` (welcome when no preferred)
  - Displayed when there is no preferred module set.
  - Uses `LanguageManager` centrally; call `welcomePage.retranslate(lang_manager)` when language changes.

Flow
1. Dialog builds modules and sidebar, then passes visible module metadata to Settings.
2. Entering Settings triggers `SettingsUI.activate()`:
   - Load user, set roles, compute access map using global `MODULES_LIST_BY_NAME`, build access pills.
   - Load original preferred via logic, then call `UserCard.set_preferred(original)` to reflect it.
  - Build module cards by iterating over `MODULES_LIST_BY_NAME` (excluding HOME), and call `on_settings_activate()` on each.
3. Changing preferred or module settings marks dirty and shows per-card confirm(s).
4. Confirm applies and persists changes using logic and per-card apply handlers.
5. Leaving Settings or closing dialog prompts to save/discard when `has_unsaved_changes()` is true.

Notes
- Preferred key: `kavitro/preferred_module` (string module name). Removing the key means Welcome page on startup.
- Access mapping is extendable; ensure subjects map to module constants and are filtered by global `MODULES_LIST_BY_NAME`.
- Module cards are built dynamically using `MODULES_LIST_BY_NAME`, excluding the HOME module.
- When programmatically updating preferred, block signals on the checkboxes to avoid spurious dirty state.

---

## 14. Centralized Settings Management

All settings in the Kavitro plugin follow a hierarchical, centralized architecture with consistent key naming and management patterns.

### Settings Categories & Managers

1. **Theme Settings** → `ThemeManager`
  - Key: `"kavitro/theme"`
  - Methods: `save_theme_setting()`, `load_theme_setting()`

2. **Preferred Module Settings** → `SettingsLogic`
  - Key: `"kavitro/preferred_module"`
  - Methods: `load_original_settings()`, `set_user_preferred_module()`, `apply_pending_changes()`

3. **Module-Specific Settings** → `SettingsLogic` + `SettingsService`
  - Key Pattern: `"kavitro/modules/{module_name}/{setting_key}"`
  - Methods: `get_module_layer_ids()`, `set_module_layer_id()`, `load_module_preference_ids()`, `save_module_preference_ids()`, `clear_module_preference_ids()`

4. **Utility Settings** → `SettingsManager`
  - Key Pattern: `"kavitro/{utility_specific_key}"`
  - Methods: `save_setting()`, `load_setting()`, `remove_setting()`

`SettingsService` in `constants/settings_keys.py` is the low-level helper backing `SettingsLogic`. Access it directly only when you are adding a brand-new helper; otherwise call through the logic layer so change tracking stays consistent.

### Settings Key Constants

All settings keys are centralized in `constants/settings_keys.py`:
- **Direct constants**: `THEME`, `PREFERRED_MODULE`, `MAIN_PROPERTY_LAYER_ID`
- **Utility class**: `UtilitySettings` with methods for dynamic keys
- **Consistent prefix**: All keys start with `"kavitro/"`

### SettingsManager API

The `SettingsManager` provides centralized access to utility settings:

```python
from ..utils.SettingsManager import SettingsManager

# Generic settings methods
SettingsManager.save_setting("kavitro/custom_key", value)
value = SettingsManager.load_setting("kavitro/custom_key", default)
SettingsManager.remove_setting("kavitro/custom_key")

# Utility-specific convenience methods
SettingsManager.save_shp_file_path(target_group, file_path)
SettingsManager.save_shp_layer_mapping(layer_name, file_path)
```

### Rules for Settings Management

1. **Always use "kavitro/" prefix** for all settings keys
2. **Use the matching manager** based on category:
  - Theme → `ThemeManager`
  - Preferred module + module-specific values → `SettingsLogic` (which delegates to `SettingsService`)
  - Utility/other → `SettingsManager`
3. **Never use direct QSettings()** in modules or utilities
4. **Define keys in constants** when possible, use dynamic generation otherwise
5. **Handle errors gracefully** - settings failures shouldn't break functionality

### Examples

```python
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ..widgets.theme_manager import ThemeManager
from ..utils.SettingsManager import SettingsManager

logic = SettingsLogic()

# ✅ CORRECT - Using appropriate managers
ThemeManager.save_theme_setting("dark")
logic.set_module_layer_id("property", kind="element", layer_name="Properties")
logic.save_module_preference_ids("property", support_key="statuses", ids=["ACTIVE", "NEW"])
SettingsManager.save_shp_file_path("NEW_PROPERTIES", "/path/to/file.shp")

# ❌ WRONG - Direct QSettings usage
settings = QSettings()
settings.setValue("kavitro/some_key", value)
```

This architecture ensures consistent settings management, easier testing, and maintainable code across the entire plugin.

---

## 15. Layer Selection in SettingsModuleCard

The Settings module now uses the stock `QgsMapLayerComboBox` widgets directly inside `SettingsModuleCard` for both the main and archive layer selectors. No custom snapshot builders or popup trees are involved anymore.

Key points
- `SettingsModuleCard` instantiates two combos with `_create_layer_combobox()`.
- `on_settings_activate()` assigns the active `QgsProject` instance to each combo (`setProject(project)`) so the built-in layer model stays live.
- Stored layer values are persisted as **layer names** via `SettingsLogic.set_module_layer_id()` and resolved back to IDs on activation using `MapHelpers.resolve_layer_id()` / `layer_name_from_id()`.
- Archive selector is optional and only shown for modules with archive support (Property module today).

Usage pattern
```python
# Inside SettingsModuleCard._build_ui()
self._layer_selector = self._create_layer_combobox(parent)
self._layer_selector.layerChanged.connect(self._on_primary_layer_changed)

if self.supports_archive:
    self._archive_picker = self._create_layer_combobox(parent)
    self._archive_picker.layerChanged.connect(self._on_archive_layer_changed)

def on_settings_activate(self, snapshot=None):  # snapshot ignored
    project = QgsProject.instance() if QgsProject else None
    if self._layer_selector:
        self._layer_selector.setProject(project)
    if self.supports_archive and self._archive_picker:
        self._archive_picker.setProject(project)
    # load persisted names via SettingsLogic and call _restore_layer_selection(...)
```

Restoring selections
- `_restore_layer_selection(combo, stored_name)` pulls the previously saved layer name from `SettingsLogic`, resolves it to a current layer id, and calls `combo.setLayer(layer)` without emitting signals.
- When combos change, `_on_element_selected()` / `_on_archive_selected()` convert the selected layer id back to a layer name via `MapHelpers.layer_name_from_id()` before marking pending state.

The old `LayerTreePicker`/snapshot workflow is fully retired; do not reference it when building new Settings cards.

---

## 16. Icons & Themed Assets (REQUIRED)

- All UI icons must be theme-aware and resolved centrally. Do not hardcode absolute file paths in widgets or modules.
- Storage layout:
  - Base icons: `resources/icons/`
  - Theme variants (optional): `resources/icons/Light/` and `resources/icons/Dark/` with identical filenames
- Formats:
  - Prefer transparent PNG; SVG is supported as a fallback. Avoid any white/solid backgrounds.
`ThemeManager` or `ModuleIconPaths`.

---

## Toolbar Filter Widget Pattern

- Filter widgets (status, type, tags, etc.) should be added to the toolbar via `ModuleToolbarArea.add_left(widget)` (or `add_right` for pills/buttons). The toolbar wraps them with labels automatically when they expose `filter_title`.
- Each filter widget is responsible for emitting its own `selectionChanged(texts, ids)` signal. Modules wire those signals to their own handlers (see `ProjectsModule._on_status_filter_selection`).
- To reset filters consistently, attach the shared refresh button from `FilterRefreshHelper.make_filter_refresh_button()` via `toolbar_area.set_refresh_widget(widget)`.
- Store references to active filters (e.g., `self._filter_widgets = [...]`) so utilities can walk and reset them as needed.
- This pattern keeps toolbar wiring consistent without requiring a `register_filter_widget` helper.

## Standardized Module Activation Pattern

- All modules must implement an `activate()` method.
- Shared activation logic (status filter loading, activation flag) is now in `ModuleBaseUI.activate()`.
- Each module should call `super().activate()` in its own `activate()` method, then add any module-specific activation logic (e.g., loading type filters, scheduling initial loads).
- This ensures consistent activation behavior and makes future maintenance easier.

Example:
```python
# In ModuleBaseUI
    def activate(self):
        if getattr(self, '_activated', False):
            return
        self._activated = True
        try:
            if hasattr(self, 'status_filter') and self.status_filter:
                self.status_filter.ensure_loaded()
        except Exception:
            pass

# In child module
    def activate(self):
        super().activate()
        # module-specific activation logic
```

## Code Cleanup Patterns

Recent code quality improvements have established these patterns for maintaining clean, performant code:

### Modern Message Dialog Pattern
- Use ModernMessageDialog methods for all user notifications instead of QMessageBox directly:
  - `ModernMessageDialog.Info_messages_modern(title, message)` - Information messages with ℹ️ icon
  - `ModernMessageDialog.Warning_messages_modern(title, message)` - Warning messages with ⚠️ icon  
  - `ModernMessageDialog.Error_messages_modern(title, message)` - Error messages with ❌ icon
  - `ModernMessageDialog.Message_messages_modern(title, message)` - General messages with 💬 icon
- These methods provide theme-aware styling, proper icon scaling, and consistent UI across the plugin
- Inline simple operations instead of creating unnecessary wrapper methods
- Remove empty callback methods and unused parameters from method signatures

### Streamlined Method Signatures
- Remove progress_callback parameters when not needed
- Simplify method signatures to only include essential parameters
- Update all method calls and documentation when signatures change

### Development Artifact Removal
- Regularly review and remove methods leftover from development iterations
- Document cleanup decisions in commit messages
- Use `# CLEANUP:` comments for temporary notes about pending removals

### Performance Optimization
- Profile method call frequency and consider inlining frequently called simple methods
- Remove method call overhead for basic operations like path manipulation
- Maintain functionality while improving code efficiency

---

## UI Responsiveness Optimization

We use `QCoreApplication.processEvents()` in all major batch UI update loops (feed item insertion, filter widget updates, card updates, widget removals) across modules and widgets. This ensures the UI remains responsive and elements update smoothly during long-running operations or batch loads. It is especially useful for:
- Preventing UI freezing during large data loads
- Keeping scrollbars, buttons, and widgets interactive
- Allowing progressive rendering of feed items and cards
- Profile method call frequency; consider inlining frequently called simple methods to improve performance

Use with care: excessive calls in tight loops may impact performance or cause re-entrancy issues. Tune or remove as needed for your deployment.