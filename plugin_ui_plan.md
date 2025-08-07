# Modular Plugin UI Development Plan

This document outlines the step-by-step plan for building a scalable, beautiful, and maintainable plugin UI for Wild Code. The plan is designed to be agile—feel free to update as new ideas or requirements emerge.

**Important:** When writing code, always refer to `copilot-prompt.md` for best practices and guidance.

---

## 1. Universal Module UI Layout
- [ ] Create a `ModuleBaseUI` widget/class that every module can inherit or use.
    - [ ] **Toolbar Area** (top): For module-specific actions and widgets (e.g., status dropdown, search, filters, etc.)
    - [ ] **Display Area** (center): For main content (tables, forms, etc.)
    - [ ] **Footer Area** (bottom): For navigation, info, or actions.

## 2. Toolbar Widget
- [ ] Build a reusable `ToolbarWidget` that can be easily added to any module.
    - [ ] Add/remove buttons or widgets dynamically
    - [ ] Custom signals for actions (e.g., refresh, add, filter)
    - [ ] Slot for custom widgets (like status dropdown)

## 3. Status Dropdown Widget
- [ ] Create a `StatusDropdownWidget`:
    - [ ] Loads statuses (from GraphQL or static config)
    - [ ] Displays as a checkable dropdown (multi-select)
    - [ ] Emits signals when selection changes
    - [ ] Can be plugged into any toolbar

## 4. Standardized Data Fetching
- [ ] Use a standard GraphQL query pattern for modules (e.g., always fetch `id`, `name`, `status`, etc.)
- [ ] Each module can define its own query fragment for extra fields
- [ ] Centralize GraphQL client logic for easy reuse

## 5. Example: Project List Module
- [ ] Inherit from `ModuleBaseUI`
- [ ] Use `ToolbarWidget` with `StatusDropdownWidget`
- [ ] Display project table in display area
- [ ] Footer for paging or actions

---

### Next Steps
- [ ] Scaffold `ModuleBaseUI` (universal layout)
- [ ] Build `ToolbarWidget` (with slot for custom widgets)
- [ ] Build `StatusDropdownWidget` (checkable, signal-based)
- [ ] Integrate into a sample module (e.g., Project List)

---

**Note:** This plan is a living document. Update as needed to reflect changes in workflow or requirements.
