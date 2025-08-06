# Lazy Loading for QGIS Plugin Modules

## Motivation
- Improve startup performance and memory usage by only instantiating modules when the user selects them.
- Avoid loading unused modules during a session.
- Align with modular, maintainable architecture as described in copilot-prompt.md.

## Key Principles
- **Centralize all module metadata** (name, display name, icon, import path, class name) in a registry (e.g., `ModuleRegistry` in `constants/file_paths.py`).
- **No hardcoded paths or filenames**: Always use constants and centralized classes for file paths, QSS, icons, etc.
- **ModuleManager** should handle all module instantiation, activation, and caching.
- **UI code** (e.g., `PluginDialog`) should only reference modules by key/name, not by direct import or instantiation.

## Implementation Outline

1. **Module Registry**
   - Store all module metadata in a single place.
   - Example:
     ```python
     MODULE_REGISTRY = {
         "JOKE_GENERATOR_MODULE": {
             "display_name": "Naljad",
             "icon": ModuleIconPaths.get_module_icon("JokeGenerator"),
             "import_path": "modules.JokeGenerator.JokeGeneratorModule",
             "class_name": "JokeGeneratorModule"
         },
         # ... other modules ...
     }
     ```

2. **ModuleManager Changes**
   - Register modules using only metadata at startup.
   - On first activation, dynamically import and instantiate the module, then cache the instance.
   - Use helper methods to fetch display name, icon, import path, etc.

3. **UI Integration**
   - Sidebar and other UI elements use the registry for display names and icons.
   - When a module is selected, call `ModuleManager.activateModule(moduleName)`; it handles lazy instantiation.

4. **Standardization**
   - All file paths, QSS, and icons referenced via centralized classes (e.g., `QssPaths`, `ResourcePaths`).
   - No hardcoded strings for paths, QSS, or icons anywhere in the codebase.

## Migration Plan

- Refactor all modules and UI code to use centralized constants and registry for paths, QSS, and icons.
- Remove all hardcoded file paths and QSS filenames.
- Ensure all modules follow the structure and naming conventions in copilot-prompt.md.
- After standardization, implement the lazy loading logic as described above.

## Risks & Mitigation

- **Risk:** Breaking login/session/close logic or module-specific features.
- **Mitigation:** Refactor in small steps, write tests, and keep the current eager-loading logic until all modules are standardized.

---

**Do not implement lazy loading until all modules and code follow the new standards.**
