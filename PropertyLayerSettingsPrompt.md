# Property Layer Settings & Tags – Plugin Coding Prompt

## Context

This QGIS plugin manages properties and other modules using:

- A central `SettingsService` for persistent settings.
- Per-module settings via `SettingsModuleCard`.
- Map layer helpers via `MapHelpers.resolve_layer_id`.
- Property-related tags such as `PROPERTY_TAG` and `IMPORT_PROPERTY_TAG`.

Users may work with **multiple QGIS projects**, and **layer IDs are not stable across projects**. Layer *names* and tags are more stable.

This prompt defines how to **store and resolve property layer settings** consistently across the codebase.

---

## High-Level Design Principles

1. **Single source of truth for “property main layer”**
   - Treat `SettingsService.module_main_layer_id("property")` (or an equivalent) as the canonical setting for the main property layer.
   - Any other helper (e.g., `main_property_layer_id`) must either be removed or be a thin alias to the same underlying value.

2. **Never rely on raw layer IDs in plugin-global settings**
   - `QgsMapLayer.id()` is only valid within a single project/session.
   - Global/plugin settings **must not** store raw IDs as the primary key.
   - Instead, store a **name-like key** (e.g., layer name) that is more stable across projects.

3. **Tags are supportive, not authoritative**
   - Tags like `PROPERTY_TAG` and `IMPORT_PROPERTY_TAG` help **classify** layers (e.g., “this is a property layer candidate”), but:
     - They should not be the *only* way to identify the user’s chosen main property layer.
     - They are primarily used for auto-detection and fallback logic, not as the primary persisted preference.

4. **Explicit user choice beats auto-detection**
   - If the user has explicitly chosen a property layer in the settings UI, that choice must be honored and resolved first.
   - Auto-detection based on tags is only used when there is no stored preference or resolution fails.

---

## Storage Strategy

### What to store

- Store a **string key** representing the preferred layer, typically the layer name.
- Example (for the property module):

  ```python
  # Example: store the main property layer name
  settings_service.module_main_layer_id("property", value=layer_name)
  ```

- This is already the pattern used in `SettingsModuleCard` (which writes names), and it should be treated as the canonical form.

### What NOT to store

- Do **not** store `QgsMapLayer.id()` as the primary persisted value in plugin-global settings.
- Do not assume IDs will survive project changes or layer re-imports.

---

## Resolution Strategy

When the plugin needs the actual live `QgsMapLayer` or layer ID, it must **resolve** the stored key at runtime.

### Helper: `resolve_property_layer_id(...)`

Implement and use a single helper function for property layer resolution, for example:

```python
from qgis.core import QgsProject
from ...constants.layer_constants import PROPERTY_TAG
from ...utils.MapTools.MapHelpers import MapHelpers


def resolve_property_layer_id(settings_service, fallback_to_tags: bool = True):
    """
    Resolve the main property layer ID.

    Priority:
    1. Stored preference (via SettingsService) using a name-like key.
    2. Fallback to tag-based auto-detection (PROPERTY_TAG).
    3. Return None if resolution fails and fallback_to_tags is False or no candidates are found.
    """
    # 1) Try stored preference
    stored_key = settings_service.module_main_layer_id("property")  # or alias
    if stored_key:
        # MapHelpers.resolve_layer_id should:
        # - Accept either an ID or a name-like key
        # - Prefer exact name matches; optionally bias towards tagged layers
        resolved_id = MapHelpers.resolve_layer_id(stored_key)
        if resolved_id:
            return resolved_id

    if not fallback_to_tags:
        return None

    # 2) Fallback: auto-detect from tags
    project = QgsProject.instance()
    candidates = []
    for layer in project.mapLayers().values():
        if layer.customProperty(PROPERTY_TAG, False):
            candidates.append(layer)

    if len(candidates) == 1:
        return candidates[0].id()

    # 3) If multiple or none:
    #    - Option A: return None and force the user to fix the settings
    #    - Option B: pick the first candidate as a heuristic
    return candidates[0].id() if candidates else None
```

### Requirements for `MapHelpers.resolve_layer_id`

`MapHelpers.resolve_layer_id` must support the following behavior:

1. **If `value` matches an existing layer ID** → return it directly.
2. **Else, treat `value` as a name-like key**:
   - Find layers whose `name()` matches the key (exact match first, then case-insensitive).
   - Optionally prefer layers tagged with `PROPERTY_TAG` (or module-specific tags) if there are multiple matches.
3. Return `None` if no suitable layer is found.

This ensures that:

- If a setting was accidentally persisted as an ID, it still works as long as that ID exists.
- For normal usage, the stored name resolves correctly even across projects.

---

## UI Integration Rules

### Module Settings UI (`SettingsModuleCard`)

- When the user selects a “main layer” for a module (including the property module):
  - Persist the **layer name** via `SettingsService.module_main_layer_id(module_key, value=name)`.
- When restoring the UI:
  - Read the stored name.
  - Call `MapHelpers.resolve_layer_id(stored_name)` to get a live layer id.
  - Populate the combo box selection using that resolved id.

### Property Behaviour / Modules Using Property Layer

Any code that needs the property layer must **not** try to read settings directly; it must:

1. Ask `SettingsService` for the stored key, and
2. Pass it through the common resolver (`resolve_property_layer_id`).

Example:

```python
# WRONG (bypasses resolution logic)
stored_name = settings_service.module_main_layer_id("property")
# ... directly assume the name is a valid live layer

# RIGHT
layer_id = resolve_property_layer_id(settings_service)
if not layer_id:
    # handle gracefully: warn user, open settings, etc.
    ...
```

---

## Tags Usage Guidelines

- `PROPERTY_TAG` and `IMPORT_PROPERTY_TAG` should be used to:
  - Classify layers as “property-related” or “eligible for import”.
  - Provide auto-detection when no preference is stored or resolution fails.
- They should **not** replace the explicit “main property layer” setting once the user has selected it.
- Where possible, helper functions should:
  - Prefer explicitly configured layers.
  - Use tags only as a **secondary heuristic**.

---

## Summary / Checklist for Future Code

When writing new code that deals with property layers:

- [ ] Do **not** store raw `QgsMapLayer.id()` in plugin-global settings.
- [ ] Store a **name-like key** via `SettingsService.module_main_layer_id("property")` or equivalent.
- [ ] Use a **single helper** (e.g. `resolve_property_layer_id`) to get the live layer ID.
- [ ] Make `MapHelpers.resolve_layer_id` support both IDs and names.
- [ ] Use `PROPERTY_TAG` / `IMPORT_PROPERTY_TAG` only as **support** for auto-detection, never as the only mechanism.
- [ ] If multiple tagged candidates exist, either:
  - force the user to choose in settings, or
  - clearly document the chosen fallback behavior.

This prompt is the authoritative reference for how property-layer-related settings and tags should be handled in this plugin.
