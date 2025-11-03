# AI Coding Instructions for wild_code QGIS Plugin

## Project Overview
**wild_code** is a modular QGIS plugin built with PyQt5 that provides property management, project tracking, and contract administration features. It follows a strict modular architecture with centralized resource management.

## Architecture Fundamentals

### Core Components
- **Main Entry Point**: `main.py` - Plugin initialization, authentication flow, module activation
- **UI Framework**: `dialog.py` - Main dialog with sidebar navigation and module stacking
- **Module System**: `BaseModule` inheritance with `activate()`/`deactivate()`/`get_widget()` lifecycle
- **Authentication**: `SessionManager` with QGIS AuthManager integration and GraphQL API client

### Data Flow
1. **Authentication**: Login → SessionManager → API token storage
2. **Module Loading**: PluginDialog → ModuleManager → Sidebar registration
3. **API Calls**: APIClient → GraphQL queries → Session validation
4. **UI Updates**: ThemeManager → QSS application → Module retheming

## Critical Patterns & Conventions

### Module Development
```python
# ✅ CORRECT: All modules inherit from BaseModule
class NewModule(BaseModule):
    def __init__(self, name, display_name, icon, lang_manager, theme_manager):
        super().__init__(name, display_name, icon, lang_manager, theme_manager)
        self.name = name  # Required: matches constants/module_names.py
        self.setup_ui()

    def setup_ui(self):
        # Apply theming immediately
        ThemeManager.apply_module_style(self.widget, [QssPaths.MAIN])
        # Build UI components...

    def activate(self):
        super().activate()  # Required: calls base activation
        # Module-specific activation logic

    def get_widget(self):
        return self.widget  # Must return QWidget instance, never class
```

### Path & Resource Management
```python
# ✅ CORRECT: Never hardcode paths
from constants.file_paths import QssPaths, ResourcePaths
icon_path = ResourcePaths.ICON
ThemeManager.apply_module_style(widget, [QssPaths.MAIN])

# ❌ WRONG: Direct path construction
icon_path = os.path.join("resources", "icon.png")
```

### Theming Requirements
```python
# ✅ CORRECT: Centralized theming application
ThemeManager.apply_module_style(self, [QssPaths.MAIN])
ThemeManager.apply_module_style(self, [QssPaths.PILLS, QssPaths.SETUP_CARD])

# ❌ WRONG: Global stylesheet application
QApplication.setStyleSheet("...")  # Breaks QGIS UI
```

### Translation Integration
```python
# ✅ CORRECT: Centralized translation
text = lang_manager.translate("key_from_lang_files")
button_text = lang_manager.sidebar_button("ModuleName")

# ❌ WRONG: Inline strings
button.setText("Hardcoded Text")
```

### API Communication
```python
# ✅ CORRECT: Always use APIClient
from utils.api_client import APIClient
client = APIClient(lang_manager)
data = client.send_query(query, variables={"id": item_id})

# ❌ WRONG: Direct requests
response = requests.post(url, json=payload)
```

## Module Registration Flow

### 1. Define Module Constant
```python
# constants/module_names.py
NEW_MODULE = "NewModule"
```

### 2. Create Module Structure
```
modules/NewModule/
├── __init__.py
├── NewModuleUI.py    # Main UI class
├── lang/
│   ├── en.py        # Translations
│   └── et.py
```

### 3. Register in Dialog
```python
# dialog.py loadModules() method
from modules.NewModule.NewModuleUI import NewModuleUI
module = NewModuleUI(NEW_MODULE, display_name, icon_path, lang_manager, theme_manager)
self.moduleManager.registerModule(module)
```

## Settings Architecture

### Hierarchical Settings Management
- **Theme**: `ThemeManager.save_theme_setting()`
- **Preferred Module**: `SettingsLogic` via QSettings key `"wild_code/preferred_module"`
- **Module-specific**: `ThemeManager.save_module_setting(module_name, key, value)`
- **Utility**: `SettingsManager.save_setting("wild_code/key", value)`

### Layer Selection Pattern
```python
# Use LayerTreePicker for all layer selections
picker = LayerTreePicker(self, placeholder=lang_manager.translate("select_layer"))
picker.layerIdChanged.connect(self.on_layer_changed)
```

## Development Workflow

### Adding New Features
1. **Check existing patterns** in similar modules (Property, Contract, Projects)
2. **Use centralized managers** (ThemeManager, LanguageManager, SettingsManager)
3. **Apply QSS theming** immediately in UI setup
4. **Handle translations** from module-specific lang files
5. **Test with both themes** (Light/Dark) and languages (en/et)

### Code Quality Standards
- **No global stylesheets** - use `ThemeManager.apply_module_style()`
- **No hardcoded paths** - use constants from `file_paths.py`
- **No direct QSettings** - use appropriate manager classes
- **No inline translations** - use `lang_manager.translate()`
- **No direct API calls** - use `APIClient`

## Common Pitfalls

### ❌ Anti-patterns to Avoid
- `QApplication.setStyleSheet()` - corrupts QGIS interface
- Direct `os.path.join()` for resources - breaks portability
- Inline English strings - not translatable
- `requests` library usage - bypasses authentication/session handling
- Direct `QSettings()` - bypasses centralized settings management

### ✅ Correct Approaches
- ThemeManager for all styling
- constants/file_paths.py for all paths
- LanguageManager for all user-facing text
- APIClient for all HTTP communication
- SettingsManager/ThemeManager for persistence

## Key Files for Understanding
- `copilot-prompt.md` - Complete detailed guidelines
- `BaseModule.py` - Module architecture foundation
- `dialog.py` - Main UI orchestration
- `utils/SessionManager.py` - Authentication patterns
- `widgets/theme_manager.py` - Theming system
- `constants/file_paths.py` - Resource management
- `languages/language_manager.py` - Translation system</content>
<parameter name="filePath">c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code\.github\copilot-instructions.md