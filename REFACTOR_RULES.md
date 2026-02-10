# Refactor Checklist (quick reference)


Use this checklist as a canonical pointer when planning or reviewing refactors (project-specific terminology):

- Prefer explicit submodule imports: import symbols from their defining module (no eager package-level re-exports).
- Avoid work at import time: no network, DB, or heavy CPU in module scope — initialize lazily or via constructors.
- Make helpers pure or `@staticmethod`/module functions where appropriate; inject clients (GraphQL/DB) rather than import them globally.
- **Keep UI thin:** Move business logic out of dialogs and widgets (see `dialog.py`, `login_dialog.py`, `widgets/`). Place business logic in `utils/` or `modules/` as appropriate.
- **Enforce one-way dependencies:** UI (dialogs, widgets) may depend on `utils/` or `modules/`, but never the reverse. Helpers and business logic must not import UI code.
- Replace fragile `__all__`/top-level re-exports with explicit imports or a lazy `__getattr__` shim only when compatibility is required.
- When changing public symbols, update call sites across the repo and run a targeted import-sanity pass (compile and validate the main import path; grep for removed symbols).
- Add/update tests for any changed helper or business logic boundary; prefer unit tests that mock IO.
- Document the change in this file with a short rationale and the files touched.
- Never mask exceptions in helpers or business logic (no try/except that silently passes). If you must handle errors, log and return an explicit failure.
- Avoid `hasattr`/`getattr` fallback checks for required methods or properties; prefer explicit interfaces/contracts and fix the caller/implementation rather than masking missing API.
- Avoid UI fallback paths that bypass business logic contexts (e.g., required context objects must be enforced, not optional). UI must not implement alternate code paths that “still work” when context is missing.
- Never mark modules active before calling `activate()`; activation must initialize feed/UI and set activation flags afterward.
- Avoid calling `setText()` inside `resizeEvent` without reentry guards or queued updates; use scheduled eliding to prevent recursion.
- Never touch map layers (selection/visibility/feature iteration) when lookup yields no matches; return early and show a user message instead.
- Validate layer fields before feature scans; log and return if the field is missing or the layer is invalid.
- Avoid starting reload/API work in widget `__init__`. If auto-load is required, defer with `QTimer.singleShot(0, ...)`; prefer explicit load on activate/user action.
- Never implement “Select all” as a fake data row. Use a control (checkbox) or native widget context menu.

**Naming and file/class patterns:**
- When extracting business logic from UI, prefer placing new logic in `utils/` (for general helpers) or `modules/` (for domain-specific logic).
- Use naming patterns like `*Helper`, `*Manager`, or `*Service` for new classes or files in `utils/` or `modules/` (e.g., `SessionHelper`, `PropertyManager`).
- For new files, use lowercase with underscores (e.g., `session_helper.py`, `property_manager.py`).
- For new classes, use CamelCase (e.g., `SessionHelper`).
- Before creating a new file or class, **search for suitable candidates in existing files and classes** in `utils/` and `modules/` to avoid duplication and promote reuse.
- Prefer using `DialogHelpers` in [ui/window_state/dialog_helpers.py](ui/window_state/dialog_helpers.py) for shared dialog callbacks instead of creating new inline lambdas in UI code.
- If a suitable existing candidate is found during refactoring, propose moving the logic there rather than creating a new helper.
- When reorganizing related code, it is acceptable (and sometimes preferred) to keep related classes/methods in a single file with clear section headers, as long as responsibilities are separated and searchable (e.g., `SessionManager` + `SessionUIController` in one file). Prefer consolidating in one place over duplicating across files.

Tag edits by adding `REFACTOR_NOTE: <summary>` at the top of the PR description so reviewers can find this checklist.

---

## Refactor Log

_Add a short rationale and list of files touched for each refactor here._

- 2026-02-06: Extracted folder selection and naming-rule dialog handlers into static dialog helpers to thin `PluginDialog` and centralize UI callbacks. Files: ui/window_state/dialog_helpers.py, dialog.py.
- 2026-02-06: Moved settings navigation confirmation and focus handling into `DialogHelpers` to reduce UI logic in `PluginDialog`. Files: ui/window_state/dialog_helpers.py, dialog.py.
- 2026-02-06: Routed logout and show lifecycle session handling through `DialogHelpers` to keep dialog UI thin while keeping session logic in `SessionManager`. Files: ui/window_state/dialog_helpers.py, dialog.py.
- 2026-02-06: Moved session UI lifecycle handlers into `SessionUIController` for clarity while keeping `SessionManager` as the sole session authority. Files: utils/session_ui_controller.py, dialog.py, ui/window_state/dialog_helpers.py.
- 2026-02-06: Consolidated `SessionUIController` into `SessionManager` (shim kept for backwards imports). Files: utils/SessionManager.py, dialog.py, utils/session_ui_controller.py.
- 2026-02-06: Added `SearchUIController` and `SettingsUIController` to route UI callbacks out of `PluginDialog`. Files: utils/search/searchHelpers.py, modules/Settings/settings_ui_controller.py, dialog.py.
- 2026-02-06: Moved module registration into `ModulesRegistry` to thin `PluginDialog`. Files: ui/modules_registry.py, dialog.py.
- 2026-02-06: Extracted module card creation into `ModuleCardFactory` to reduce UI logic in `ModuleBaseUI`. Files: ui/module_card_factory.py, ui/ModuleBaseUI.py.
- 2026-02-06: Moved `ModuleFeedBuilder.create_item_card` implementation into `ModuleCardFactory` (ModuleFeedBuilder now delegates). Files: ui/module_card_factory.py, widgets/DataDisplayWidgets/ModuleFeedBuilder.py.
- 2026-02-04: Moved empty import-layer cleanup into `MapHelpers` as a reusable helper (startup safeplace). Files: utils/MapTools/MapHelpers.py, main.py.
- 2026-02-04: Removed UI dependencies from module switch helper, added UI-owned handlers and improved switch logging/rollback. Files: utils/moduleSwitchHelper.py, dialog.py, utils/messagesHelper.py, utils/access_creditentials.py, modules/Settings/SettinsUtils/SettingsLogic.py.
- 2026-02-05: Stabilized module activation, property search, and UI text eliding; added per-module logging and crash diagnostics. Root causes: activation token pre-set blocked ModuleBaseUI.activate; missing features on layer triggered unsafe map access; ElidedLabel resize/setText recursion caused stack overflow. Files: module_manager.py, ui/ModuleBaseUI.py, Logs/switch_logger.py, Logs/python_fail_logger.py, Logs/logger.py, utils/switch_logger.py, utils/logger.py, utils/search/UnifiedSearchController.py, python/workers.py, modules/Property/PropertyUITools.py, utils/MapTools/item_selector_tools.py, utils/MapTools/MapHelpers.py, widgets/DataDisplayWidgets/InfoCardHeader.py, main.py.
- 2026-02-06: Adopted strict activation contract: no hidden guards or silent fallbacks; if a module does not follow the token lifecycle contract, we fix the module rather than masking it. We accept temporary breakage to surface real faults during refactoring. Files: module_manager.py, utils/token_mixin.py, modules/Settings/SettingsUI.py, BaseModule.py, widgets/WelcomePage.py, modules/signaltest/SignalTestModule.py.
- 2026-02-06: Removed silent exception swallowing in module switching and base feed UI; replaced with explicit logging to surface real failures. Files: utils/moduleSwitchHelper.py, ui/ModuleBaseUI.py.
- 2026-02-06: Removed silent exception swallowing in dialog callbacks; added switch log entries for UI failures. Files: dialog.py.
- 2026-02-06: Removed silent exception swallowing in unified feed logic; errors now surface via PythonFailLogger. Files: feed/FeedLogic.py.
- 2026-02-06: Removed silent exception swallowing in Settings cards and added PythonFailLogger diagnostics. Files: modules/Settings/cards/SettingsBaseCard.py, modules/Settings/cards/SettingsUserCard.py, modules/Settings/cards/ModuleLabelsWidget.py, modules/Settings/cards/SettingsPropertyManagement.py, modules/Settings/cards/SettingsModuleCard.py.
- 2026-02-06: Removed silent exception swallowing in map tool helpers; added PythonFailLogger diagnostics for selection and layer helpers. Files: utils/MapTools/item_selector_tools.py, utils/MapTools/MapHelpers.py, utils/MapTools/map_selection_controller.py, utils/MapTools/MapSelectionOrchestrator.py.
- 2026-02-06: Removed silent exception swallowing in module action buttons and property add dialogs; added PythonFailLogger diagnostics. Files: widgets/DataDisplayWidgets/module_action_buttons.py, widgets/AddFromMapPropertyDialog.py, widgets/AddUpdatePropertyDialog.py.
- 2026-02-07: Simplified ModuleBaseUI to a thinner UI layer by moving error handling into feed logic, removing redundant wrappers, and tightening typing/Protocols. Files: ui/ModuleBaseUI.py, feed/FeedLogic.py.
- 2026-02-07: Extracted feed UI reset steps into a dedicated helper for clearer UI state management. Files: ui/ModuleBaseUI.py.
- 2026-02-07: Added `empty_state` property to centralize UI empty-state access and improve IDE support. Files: ui/ModuleBaseUI.py.
- 2026-02-07: Reused map/layer helpers in Settings property management and added best-effort UI helper to make UI-only failures explicit. Files: modules/Settings/cards/SettingsPropertyManagement.py.
- 2026-02-07: Extracted property action service, centralized backend action dialog flow, and moved tunnus extraction/dedupe helpers into PropertyRowBuilder; switched selection start to MapSelectionOrchestrator. Files: utils/mapandproperties/property_action_service.py, ui/window_state/dialog_helpers.py, utils/mapandproperties/property_row_builder.py, utils/MapTools/MapSelectionOrchestrator.py, modules/Settings/cards/SettingsPropertyManagement.py.
- 2026-02-07: Hardened Settings close guard flow and logging; removed UI prompt from SettingsLogic; added SettingsManager logging; made userUtils abilities parsing resilient; replaced SettingsScrollHelper prints. Files: modules/Settings/settings_ui_controller.py, modules/Settings/SettingsUI.py, modules/Settings/SettinsUtils/SettingsLogic.py, utils/SettingsManager.py, modules/Settings/SettinsUtils/userUtils.py, modules/Settings/scroll_helper.py.
- 2026-02-09: Refactored filter widgets into widgets/Filters with a shared BaseSingleFilterWidget, added tri-state select-all checkbox (no sentinel rows), request-id stale-result guards, and updated import paths. Files: widgets/Filters/BaseSingleFilterWidget.py, widgets/Filters/StatusFilterWidget.py, widgets/Filters/TagsFilterWidget.py, widgets/Filters/TypeFilterWidget.py, widgets/Filters/__init__.py, widgets/StatusFilterWidget.py, widgets/TagsFilterWidget.py, widgets/TypeFilterWidget.py, utils/FilterHelpers/FilterHelper.py, modules/Settings/cards/SettingsModuleCard.py, modules/projects/ProjectsUi.py, modules/coordination/CoordinationModule.py, modules/contract/ContractUi.py.
- 2026-02-09: Moved contact name extraction into a shared data extractor to thin `ContactsWidget`. Files: utils/data_extractors.py, widgets/DataDisplayWidgets/ContactsWidget.py.
- 2026-02-09: Plan A: Centralized DataDisplayWidgets parsing into responses extractors. Moved GraphQL dict traversal into `DataDisplayExtractors`; widgets now consume safe defaults; no behavior change intended. Files: python/responses.py, widgets/DataDisplayWidgets/ContactsWidget.py, widgets/DataDisplayWidgets/TagsWidget.py, widgets/DataDisplayWidgets/StatusWidget.py, widgets/DataDisplayWidgets/MembersView.py, widgets/DataDisplayWidgets/DatesWidget.py, widgets/DataDisplayWidgets/InfoCardHeader.py, widgets/DataDisplayWidgets/ModuleConnectionActions.py, utils/data_extractors.py.
- 2026-02-09: Applied DataDisplayWidgets translation keys and completed extractor usage for remaining fields. Files: languages/translation_keys.py, languages/en.py, languages/et.py, widgets/DataDisplayWidgets/DatesWidget.py, widgets/DataDisplayWidgets/ExtraInfoWidget.py, widgets/DataDisplayWidgets/InfoCardHeader.py, widgets/DataDisplayWidgets/MembersView.py, widgets/DataDisplayWidgets/module_action_buttons.py, python/responses.py.
