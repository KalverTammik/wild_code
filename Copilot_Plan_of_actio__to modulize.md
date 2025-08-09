# Plan of Action for Modularity in wild_code

This document summarizes the current state, gaps, and future steps for improving modularity in the wild_code plugin, based on the assessment of our `copilot-prompt.md`, `MODULE_MANAGEMENT_MODULARITY.md`, and `PROPERTIES_CONNECTOR_MODULAR_PATTERN.md`.

---

## 1. Current State

- **Modules** are placed in their own subdirectories under `modules/`, each with `__init__.py`, `ui.py`, `logic.py`, and a `lang/` directory.
- **All modules inherit** from `BaseModule` and implement required methods: `activate`, `deactivate`, `run`, `reset`, `get_widget`.
- **Registration** is dynamic: modules are imported, instantiated, and registered in the `loadModules` method of the main dialog.
- **Resource management** (paths, icons, QSS) is centralized via constants and managers.
- **Theming and translation** are handled centrally.
- **No static mapping** of modules to UI elements; everything is dynamic at runtime.

---

## 2. Gaps vs. Aspirational Pattern

- No single `Module` constants class or `all_modules` list for easy iteration/management.
- No dedicated UI mapping class (e.g., `ModuleTriggerButtons`) for button-to-module logic.
- No centralized access control for enabling/disabling modules based on user roles.
- No dedicated translation class for module names (plural/singular, multi-language).
- Controller/helper pattern (as in the properties connector example) is not widely used for modular UI actions.

---

## 3. Plan of Action

### 3.1. Centralized Module Definitions

- Create a `Module` class with all module constants and an `all_modules` list for easy iteration and management.

### 3.2. UI Mapping

- Implement a `ModuleTriggerButtons` class to map modules to UI elements for all UI logic.

### 3.3. Access Control

- Centralize access control logic to enable/disable UI elements based on user roles/abilities.

### 3.4. Translation Support

- Store translations for module names in a dedicated class and provide methods for fetching names in different languages and forms.

### 3.5. Consistent Usage

- Always use the `Module` constants throughout the codebase for clarity and maintainability.

### 3.6. Modular Controllers and Helpers

- Adopt the controller/helper pattern for modular UI actions, as demonstrated in the properties connector example.

### 3.7. Documentation and Guidelines

- Update documentation to reflect these patterns and ensure all new modules follow the improved modularity approach.

---

## 4. Summary

By following this plan, wild_code will achieve a more maintainable, extensible, and clear modular architecture. Each responsibility will be clearly separated, and changes in one area (like adding a new module or language) will require minimal