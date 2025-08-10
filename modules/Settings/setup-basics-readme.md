# Layer Setup Module: Architecture and Card-Based UI (within SettingsUI)

This document defines a general, extensible approach for configuring project layers via a card-based UI inside the Settings module. It replaces one-off, dialog-specific write-ups with a reusable pattern that users (and you) can extend with new setup cards.

## Goals
- Provide a single place where users configure layer-related preferences.
- Use a consistent card pattern for each setup unit (discoverable, reorderable, themed).
- Decouple UI and functionality so new setup cards can be added with minimal boilerplate.
- Follow project rules: no IO in constructors.

## Where it lives
- The Layer Setup module is a section/page inside `SettingsUI`.
- Uses the universal layout in `ModuleBaseUI`. Setup cards follow the SettingsUI active style.

## Card-based UI pattern
- Each setup area (e.g., “Target cadastral layer”, “Basemap selection”, “Style presets”) is represented by a Setup Card widget.
- Cards are stacked in a scrollable feed (like Projects/Contracts), but purpose-built:
  - New QSS selector: `QssPaths.SETUP_CARD` (to be added) for look-and-feel.
  - ObjectName: `SetupCard` per card for targeted styling.
- Each card contains:
  - Title + description
  - Inputs (combo, checkboxes, file pickers)
  - Actions: Save/Apply/Reset
  - Optional: Open advanced editor (can be a frameless tool window)

## Extensibility model (setup cards as general widgets)
- “Providers” are simply general-purpose widgets (cards) that plug into SettingsUI.
- We will develop these widgets later; interface details here are guidance, not a hard contract.
- Minimal expected capabilities for a card widget:
  - Stable id (string) for registration/order
  - Title/description (use LanguageManager in actual implementation)
  - `build_card(ui_context) -> QWidget` returning a styled card widget
  - Optional state helpers: `load_state()`, `save_state(state)` for reading/writing QgsSettings
  - Optional `open_editor(parent)` for an advanced frameless editor
- A lightweight `SetupRegistry` will collect and return these card widgets for rendering in SettingsUI (implementation deferred).

## Data loading & activation
- Do not fetch or compute in constructors.
- In `SettingsUI.activate()`: if not initialized, query `SetupRegistry` for cards, create each card widget, and bind any persisted state.
- For cards that need project context (e.g., list of vector layers), use a `LayersService` pulled from `SetupModularity.md`.

## Services (from SetupModularity.md)
- LayersService
  - `list_vector_layers()` → populate combos
  - `get_layer_by_name(name)`
  - `apply_qml_style(layer, qml_path)`
- SettingsRepository (QgsSettings under wild_code)
  - `read(key)`, `write(key, value)`
- UseCases wrap common flows (save target, apply style, etc.)

## Optional frameless editor per card
- Some cards may expose an advanced editor as a frameless tool window:
  - `Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint`
  - `Qt.WA_TranslucentBackground = True`
  - Optional fade-in via `QPropertyAnimation`.
  - Use shared `DraggableFrame` for dragging.
- Trigger via a button on the card: “Open advanced editor”.

## File and code structure (suggested)
```
modules/Settings/
  SettingsUI.py
  setup/
    registry.py          # SetupRegistry (deferred), ISetupProvider-style hints
    services.py          # LayersService, SettingsRepository, UseCases
    providers/           # Card widgets (to be developed later)
      target_cadastral.py
      basemap.py
  lang/
    en.py, et.py
```

## Adding a new setup card (quickstart)
1) Create a card widget in `modules/Settings/setup/providers/my_card.py`.
2) Register it in `setup/registry.py` (static list initially).
3) Give the root widget `objectName = "SetupCard"` for styling and build the UI consistent with SettingsUI style.
4) Implement optional `load_state`/`save_state` and `open_editor` as needed.

## Suggested UI structure in SettingsUI
- Group: “Layer Setup”
  - Scroll area containing Setup Cards from `SetupRegistry`.

## Next steps
- Add `QssPaths.SETUP_CARD` and a basic QSS for cards in `styles/`.
- Implement `setup/registry.py` and `setup/services.py` skeletons (deferred).
- Port the cadastral target as the first card widget.
- Wire `SettingsUI.activate()` to render cards.