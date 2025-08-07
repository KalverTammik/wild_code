# Lazy Loading for QGIS Plugin Modules

## Motivation
- Improve startup performance and memory usage by only instantiating modules when the user selects them.
- Avoid loading unused modules during a session.
- Align with modular, maintainable architecture as described in copilot-prompt.md.

## Key Principles
- **Static mapping is only for translation keys**: The only static mapping is `MODULE_NAMES` (in `module_manager.py`), which maps module constants to class names for translation purposes. It does **not** include import paths, icons, or other metadata.
- **All other module metadata is dynamic**: Module registration, icons, display names, and other metadata are handled dynamically at runtime by `ModuleManager.registerModule`, which stores modules in `self.modules`.
- **No hardcoded paths or filenames**: Always use constants and centralized classes for file paths, QSS, icons, etc.
- **ModuleManager** handles all module instantiation, activation, and caching.
- **UI code** (e.g., `PluginDialog`) should only reference modules by key/name, not by direct import or instantiation.
- **Future-proofing**: In the future, you may add a static or dynamic mapping for module components (e.g., submodules or UI parts), but currently, only translation keys are static.

## Implementation Outline


1. **Module Metadata (Dynamic Only)**
   - All module metadata (except translation key mapping) is built dynamically at runtime (e.g., by scanning the modules directory, using a config file, or registering modules in code).
   - Example dynamic registration:
     ```python
     # At startup, scan modules/ and register all found modules with their metadata
     for module_info in discover_modules():
         module_manager.registerModule(module_info)
     ```

2. **ModuleManager Changes**
   - Register modules using only metadata (from dynamic discovery) at startup.
   - On first activation, dynamically import and instantiate the module, then cache the instance.
   - Use helper methods to fetch display name, icon, import path, etc.

3. **UI Integration**
   - Sidebar and other UI elements use the dynamic registry (`self.modules`) for display names and icons.
   - When a module is selected, call `ModuleManager.activateModule(moduleName)`; it handles lazy instantiation.

4. **Standardization**
   - All file paths, QSS, and icons referenced via centralized classes (e.g., `QssPaths`, `ResourcePaths`).
   - No hardcoded strings for paths, QSS, or icons anywhere in the codebase.
   - The only static mapping is for translation keys; all other module data is dynamic.

## Migration Plan

- Refactor all modules and UI code to use centralized constants and dynamic discovery for paths, QSS, and icons.
- Remove all hardcoded file paths and QSS filenames.
- Ensure all modules follow the structure and naming conventions in copilot-prompt.md.
- After standardization, implement the lazy loading logic as described above.

## Risks & Mitigation

- **Risk:** Breaking login/session/close logic or module-specific features.
- **Mitigation:** Refactor in small steps, write tests, and keep the current eager-loading logic until all modules are standardized.

---

**Do not implement lazy loading until all modules and code follow the new standards.**
