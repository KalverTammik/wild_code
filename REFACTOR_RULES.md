# Refactor Checklist (quick reference)

**Logireegel:** iga muudatuse põhjendus ja puudutatud failide loend käib edaspidi ainult
commiti kirjeldusse (PR kirjelduse jaoks kasuta jaotist `REFACTOR_NOTE: <summary>`), MITTE
sellesse faili. See fail hoiab ainult kehtivaid reegleid. Varasemad, siit eemaldatud logikirjed
on failis [REFACTOR_LOG_ARCHIVE.md](REFACTOR_LOG_ARCHIVE.md).

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
- **Theme only at the right scope:** apply the narrowest stylesheet bundle that matches the widget's real scope; root containers may use app/module bundles, but leaf widgets should use exact QSS files or inherited theme selectors instead of broad bundle application.
- **One retheme lifecycle only:** keep a single canonical retheme engine and route dynamic widget/card restyling through the owning base lifecycle instead of per-feature/manual retheme loops.

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
- Document the change's rationale and the files touched in the commit description, not in this file (see the logireegel at the top).
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

