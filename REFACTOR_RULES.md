# Refactor Checklist (quick reference)


Use this checklist as a canonical pointer when planning or reviewing refactors (project-specific terminology):

## Simplicity-first policy (default)

When multiple valid refactor options exist, choose the one with fewer moving parts.

- **Prefer deletion over abstraction:** remove dead code and duplicate branches before introducing new helpers/classes.
- **One new concept at a time:** avoid combining renames, architecture moves, and behavior changes in one PR.
- **No wrapper chains:** do not add pass-through methods that only call another method with same args.
- **No speculative extensibility:** avoid adding optional flags, strategy hooks, or config knobs unless a real current caller needs them.
- **Early-return flow:** flatten nested `if/else` logic; prefer guard clauses and one clear happy path.
- **Keep local until reused:** keep logic in-place until it is reused in at least 2 places or clearly blocks readability.
- **Extract only meaningful units:** create a helper only if it has a clear domain name and reduces cognitive load.
- **Minimize file churn:** prefer improving existing files/classes over creating new ones unless separation is necessary.
- **UI composition, not orchestration:** UI should assemble widgets and delegate actions; avoid embedding branching business flows.
- **Exception handling must be explicit and minimal:** catch only where recovery is possible; otherwise log and surface failure.

## Conciseness guardrails

- Target smaller diffs: prefer a focused change set over broad rewrites.
- If a function grows, first try simplification (remove branches/duplication) before splitting.
- Avoid duplicate state (no parallel booleans/fields representing the same thing).
- Prefer direct expressions over temporary variables when readability is not reduced.
- Avoid comments that describe obvious code; keep comments for intent/tradeoffs only.

## Centralization and API consistency

- **One public entrypoint per concern:** expose one canonical API for each concern (e.g., URL opening), and use it everywhere.
- **Reuse-first is mandatory:** before adding any new method/class, search for similar existing implementations and reuse them when possible.
- **Relocate instead of duplicate:** if similar logic exists but is not in a proper shared location (`utils/`/`modules/` service/helper), propose a refactor plan to move/centralize it before adding another implementation.
- **No mixed call styles:** do not use both low-level helper functions and wrapper classes for the same behavior at call sites.
- **Keep internals private:** if a low-level helper is needed, keep it private and never import/use it from feature/UI files.
- **Centralize reusable literals:** move repeated module names, event keys, folder names, and prefixes into shared constants.
- **Log keys from one source:** logging module/event identifiers must come from a central constants owner, not inline strings in feature code.
- **Strict translations only:** UI translation lookups must use strict key resolution (no fallback text/key arguments) so missing keys fail fast during development.
- **Avoid pass-through wrappers:** do not keep methods that only forward arguments unless required for compatibility.
- **Prefer direct signal wiring:** if a signal can connect directly to the canonical callable, do that instead of adding local one-line handlers.
- **Normalize naming to project style:** classes use CamelCase, files use snake_case; avoid introducing new lowercase class names.
- **Import only canonical symbols:** feature modules should import the canonical public API symbol, not alternative aliases.
- **Compatibility shims are temporary:** if a shim is needed, mark and remove it after call sites migrate.
- **Remove obsolete UI flags early:** during widget refactors, verify constructor params and `setProperty(...)` flags are still consumed by call sites/QSS/selectors; delete dead params/properties and update all callers.

## Refactor acceptance gate (quick check)

Before merging, verify all are true:

1. **Less complexity:** branch count and nesting are same or lower than before.
2. **Less surface area:** no unnecessary new classes/files/public methods.
3. **Clearer flow:** main path is readable top-to-bottom without jumping across many helpers.
4. **No hidden behavior changes:** behavior changes are intentional and documented.
5. **No silent fallback masking:** failures are either handled explicitly or logged and returned.
6. **Single call pattern:** one canonical API usage style is applied across all touched call sites.
7. **Centralized constants:** newly introduced repeated literals are extracted to shared constants.
8. **Reuse scan done first:** existing similar methods/classes were searched before creating new ones.
9. **Refactor plan when misplaced:** if reusable logic exists in the wrong layer/location, a move-to-shared-location plan is proposed instead of duplicating code.
10. **Strict i18n compliance:** touched UI code does not introduce translation fallbacks that can mask missing keys or show mixed-language text.
11. **No dead widget API/state:** touched widgets do not keep unused constructor arguments or orphaned dynamic properties without active consumers.

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
- Avoid translation fallback paths in UI (`translate(..., fallback=...)`, hardcoded language fallback strings, or key-as-text fallbacks). Missing keys must surface immediately via strict translation lookup.
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

- 2026-03-02: Senior pass on `PropertyUITools`: enforced strict translation lookups in touched UI flow (removed fallback arguments), replaced silent `bring_dialog_to_front` exception swallow with explicit `PythonFailLogger` diagnostics, and kept behavior unchanged for property search/map/header flows. Files: modules/Property/PropertyUITools.py, REFACTOR_RULES.md.

- 2026-02-27: Added strict translation policy to prevent fallback-masked i18n issues (no UI fallback text/key usage), plus acceptance-gate check for strict i18n compliance. Files: REFACTOR_RULES.md.
- 2026-02-27: Added explicit centralization and API consistency rules from URL-opening/logging cleanup session (single public entrypoint, no mixed call styles, centralized literals, direct signal wiring, naming normalization). Files: REFACTOR_RULES.md.
- 2026-02-27: Strengthened checklist with mandatory reuse-first scan and relocation-before-duplication rule; added acceptance-gate checks for reuse scan and refactor-plan requirement when similar logic exists in wrong location. Files: REFACTOR_RULES.md.
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
- 2026-02-06: Adopted strict activation contract: no hidden guards or silent fallbacks; if a module does not follow the token lifecycle contract, we fix the module rather than masking it. We accept temporary breakage to surface real faults during refactoring. Files: module_manager.py, utils/token_mixin.py, modules/Settings/SettingsUI.py, widgets/WelcomePage.py, modules/signaltest/SignalTestModule.py.
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
- 2026-02-27: Thinned Settings property management UI by extracting remove-selection orchestration into `PropertySelectionActionService`; UI now delegates selection/prompt/action flow and keeps only view wiring/state hooks. Files: utils/mapandproperties/property_action_service.py, modules/Settings/cards/SettingsPropertyManagement.py.
- 2026-02-27: Applied strict translation refactor to Settings remove-selection flow by replacing remaining hardcoded dialog strings with `TranslationKeys` and EN/ET catalog entries. Files: utils/mapandproperties/property_action_service.py, modules/Settings/cards/SettingsPropertyManagement.py, languages/translation_keys.py, languages/en.py, languages/et.py, REFACTOR_RULES.md.
- 2026-02-27: Simplified `ContactsWidget` by removing unused total-count path, consolidating chip creation, dropping inline style hardcoding, and only attaching visible widget instances in card factory. Files: widgets/DataDisplayWidgets/ContactsWidget.py, ui/module_card_factory.py, REFACTOR_RULES.md.
- 2026-02-27: Added explicit widget-API hygiene check (remove unused constructor args/dynamic properties) and applied it by removing obsolete `compact` argument/property from `DatesWidget` and updating all call sites. Files: REFACTOR_RULES.md, widgets/DataDisplayWidgets/DatesWidget.py, ui/module_card_factory.py, modules/Property/property_tree_widget.py.
- 2026-02-27: Senior pass on `ExtraInfoWidget`: removed dead imports/helper, removed hardcoded fallback content, injected shared language manager from caller, and moved inline dialog/list/title styles into new themed `ModuleInfo.qss` files for consistent styling contracts. Files: widgets/DataDisplayWidgets/ExtraInfoWidget.py, ui/module_card_factory.py, styles/Dark/ModuleInfo.qss, styles/Light/ModuleInfo.qss, REFACTOR_RULES.md.
- 2026-02-27: Senior pass on `InfoCardHeader`: removed dead import and stale `module_name` header API/state, stopped per-render `LanguageManager()` creation by injecting shared `lang_manager`, and updated all call sites for cleaner widget contracts. Files: widgets/DataDisplayWidgets/InfoCardHeader.py, ui/module_card_factory.py, modules/Property/property_tree_widget.py, REFACTOR_RULES.md.
- 2026-02-27: Visual parity pass for header row rendering between feed cards and property-tree rows: aligned `ModuleConnectionRow` grid stretch/margins to feed baseline and added full-text tooltip on elided project title labels for consistent overflow UX. Files: modules/Property/property_tree_widget.py, widgets/DataDisplayWidgets/InfoCardHeader.py, REFACTOR_RULES.md.
- 2026-02-27: Removed obsolete `ModuleFeedBuilder` pass-through wrapper and kept `ModuleCardFactory.create_item_card` as the sole canonical card-construction entrypoint to reduce API surface and wrapper chains. Files: widgets/DataDisplayWidgets/ModuleFeedBuilder.py, REFACTOR_RULES.md.
- 2026-02-27: Settings activation/card-loading cleanup: removed dead helper/unused payload state in `SettingsUI`, switched module-card build to one batched pass (instead of per-card timer recursion) to reduce layout thrash, and tightened lazy filter loading triggers in `SettingsModuleCard` by removing `QEvent.Show` auto-load. Files: modules/Settings/SettingsUI.py, modules/Settings/cards/SettingsModuleCard.py, REFACTOR_RULES.md.
- 2026-02-27: Settings loading Phase 2: added lightweight per-card + batch activation timing logs in `SettingsUI` to identify card-level loading hotspots during Settings activation; kept lazy filter loading preload-capable in `SettingsModuleCard` so saved user preferences remain visible on card display. Files: modules/Settings/SettingsUI.py, modules/Settings/cards/SettingsModuleCard.py, REFACTOR_RULES.md.
- 2026-02-27: SettingsUI lighten step: extracted user-fetch worker setup/teardown into `SettingsUserFetchService` to reduce orchestration code in `SettingsUI` while preserving token-aware callback flow and cancellation behavior. Files: modules/Settings/SettingsUI.py, modules/Settings/settings_user_fetch_service.py, REFACTOR_RULES.md.
- 2026-02-27: Settings card-engine extraction: moved Settings module-card creation into `SettingsCardFactory` and batched build/activate/dispose orchestration into `SettingsCardBuildService` to reuse the factory+service pattern used in feed cards without coupling Settings to feed pagination engine internals. Files: modules/Settings/SettingsUI.py, modules/Settings/settings_card_factory.py, modules/Settings/settings_card_build_service.py, REFACTOR_RULES.md.
- 2026-02-27: Settings inspection pass (contract + constants): replaced `SettingsScrollHelper` private `_is_active` fallback checks with explicit token-contract validation (`is_token_active(None)`), removed dynamic fallback access for `_allowed_modules`, and normalized Settings logging module keys to `Module.SETTINGS.value` in UI controller and settings logic. Files: modules/Settings/scroll_helper.py, modules/Settings/settings_ui_controller.py, modules/Settings/SettinsUtils/SettingsLogic.py, REFACTOR_RULES.md.
- 2026-03-02: Settings exception-pass audit: removed remaining silent `except Exception: pass` blocks in Settings UI/card/build flows and replaced them with explicit error logging or logged best-effort handling to preserve resilience without masking faults. Files: modules/Settings/SettingsUI.py, modules/Settings/settings_card_build_service.py, modules/Settings/cards/SettingsModuleCard.py, REFACTOR_RULES.md.
- 2026-03-02: Settings preference-flow reuse pass: extracted status/type/tag preference load/save/revert/reset blocks in `SettingsModuleCard` into reusable internal helper methods and moved bulk label-value loading into `SettingsLogic` (`load_module_label_values`) to reduce repeated branch logic and keep persistence concerns out of UI-card internals. Files: modules/Settings/cards/SettingsModuleCard.py, modules/Settings/SettinsUtils/SettingsLogic.py, REFACTOR_RULES.md.
- 2026-03-02: Module switching architecture pass: split `ModuleSwitchHelper.switch_module` into private phases (resolve/guard/activate/UI-bind/rollback), removed duplicate module-level registration wrappers in favor of class-level canonical registration API, moved Property map-selection window-manager signal wiring into `PropertyModule` lifecycle hooks (`activate`/`deactivate`), and replaced dynamic retheme hook probing in `ModuleManager` with an explicit `retheme` contract. Files: utils/moduleSwitchHelper.py, modules/Property/PropertyUI.py, module_manager.py, REFACTOR_RULES.md.
