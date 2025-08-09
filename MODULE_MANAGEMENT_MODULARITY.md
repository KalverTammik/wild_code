# Modular Plugin Architecture: Module Management

This document summarizes the modular approach for managing modules in a plugin, based on the current implementation in `modules.py`.

---

## 1. Centralized Module Definitions
- The `Module` class defines all module types as constants (e.g., CONTRACT, PROJECT, TASK, etc.).
- An `all_modules` list is maintained for easy iteration and management.

## 2. UI Mapping
- The `ModuleTriggerButtons` class maps module types to their corresponding UI buttons.
- This mapping is used for enabling/disabling buttons and for access control.

## 3. Access Control
- Access control is handled by `apply_button_access_control`, which enables or disables module buttons based on user permissions (abilities).
- Only modules with at least 'read' permission are enabled for the user.

## 4. Translation and Localization
- The `ModuleTranslation` class provides plural and singular translations for each module type in multiple languages (Estonian and Latvian).
- The `module_name` method fetches the correct translation for a given module and language.

## 5. Consistent Usage
- All references to module types throughout the codebase use the `Module` class constants, ensuring consistency and maintainability.

---

## Plan of Action for New Modular Plugins

1. **Define Core Module Types**
   - Create a `Module` class with all relevant module constants and an `all_modules` list.

2. **UI Mapping**
   - Map modules to UI elements in a dedicated class for all UI logic.

3. **Access Control**
   - Implement access control logic to enable/disable UI elements based on user roles/abilities.

4. **Translation Support**
   - Store translations for module names in a dedicated class and provide methods for fetching names in different languages and forms.

5. **Consistent Usage**
   - Always use the `Module` constants throughout your codebase for clarity and maintainability.

6. **Keep Logic Modular**
   - Separate business logic, UI logic, and access control into different classes or modules for easier maintenance and testing.

---

**Summary:**
This modular approach ensures your plugin is easy to maintain, extend, and localize. Each responsibility is clearly separated, and changes in one area (like adding a new module or language) require minimal changes elsewhere.
