# Audit Prompt for QGIS Plugin Standards Compliance

This audit prompt provides a step-by-step checklist to ensure your project complies with the standards in `copilot-prompt.md`. Run this audit before deployment to catch issues early and maintain code quality.

---

## Stage 1: Centralized Path and Resource Management
- [ ] All file, directory, and QSS paths are referenced via `constants/file_paths.py`.
- [ ] No `os.path.join` or string-literal paths in modules/widgets; all paths use constants.
- [ ] All QSS filenames are referenced via `QssPaths` or similar constants.
- [ ] All theme directory paths use `StylePaths` constants.
- [ ] Module names are only referenced via `constants/module_names.py`.
- [ ] Module icons are only referenced via `constants/module_icons.py`.
- [ ] No hardcoded file paths or QSS filenames in any module or widget.

## Stage 2: UI and Theme Compliance
- [ ] All UI components use layouts (`QVBoxLayout`, `QHBoxLayout`), not absolute positioning.
- [ ] All dialogs and widgets use the shared stylesheet from `widgets/theme_manager.py`.
- [ ] No inline styling; all styles are in QSS files.
- [ ] All dialogs and widgets support theme switching (dark/light).
- [ ] All QSS files are named and organized as per standards (e.g., `main.qss`, `header.qss`).

## Stage 3: Translation and Localization
 [ ] All user-facing text uses translation keys via `LanguageManager_NEW.translate(key)` or equivalent.
 [ ] The global `lang_manager` instance is defined after the `LanguageManager_NEW` class in `language_manager.py`.

## Stage 4: Module and Logic Structure
- [ ] All modules inherit from `BaseModule` and follow the modular structure.
- [ ] Each module implements `activate()`, `deactivate()`, `run()`, and `reset()` as needed. 
- [ ] Module logic and UI are separated (e.g., `logic.py` and `ui.py`).
- [ ] All modules are registered via `ModuleManager`.

## Stage 5: Coding Style and Best Practices
- [ ] All code uses Python 3.9+ syntax and follows PEP8.
- [ ] No wildcard imports; imports are grouped by standard, PyQt5, and QGIS.
- [ ] All public methods have docstrings.
- [ ] Comments are concise and useful; TODOs are marked.
- [ ] No business logic inside UI classes; use helpers for logic.

## Stage 6: Safety, Performance, and Documentation
- [ ] No blocking of the UI thread with long-running operations.
- [ ] All layers and QGIS objects are validated before use.
- [ ] All new features are documented in `copilot-prompt.md` if they introduce new standards.

---

## How to Use
1. Open this checklist before each deployment or major release.
2. Work through each stage, checking off items as you verify compliance.
3. If you find a non-compliance, fix it immediately or add a TODO for follow-up.
4. Update `copilot-prompt.md` if you introduce new standards or patterns.

---

**Tip:** Keep this file (`audit.md`) in your project root and update as your standards evolve.
