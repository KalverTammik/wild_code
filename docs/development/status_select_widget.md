# Status Select Widgets

The status select controls live in `widgets/status_select_widget.py`.

## Purpose

Use these widgets only for status choices. They preserve status-specific product UI that a generic checkable combo cannot express:

- grouped popup sections by backend `status.type`
- color dots from backend `status.color`
- selected-row emphasis in the popup
- popup-local `Select All` and `Clear Selection` actions for multi-select filters

## Public Widgets

`StatusSelectWidget`

- Single-select control.
- Used by the Works create dialog.
- Compatible with the subset of `QComboBox` accessors currently needed there: `currentData()` and `currentText()`.
- Extra status accessor: `current_status_color()`.

`StatusMultiSelectWidget`

- Multi-select control.
- Used by `widgets/Filters/StatusFilterWidget.py`.
- Public filter API is `selected_ids()`, `selected_texts()`, and `set_selected_ids(ids, emit=True)`.
- Emits `selectionChanged(texts, ids)`.

## Data Contract

The widgets expect status option dictionaries with these fields:

- `id`: backend status id
- `name` or `label`: visible text
- `color`: backend color, with or without leading `#`
- `type`: backend status type, normally `OPEN` or `CLOSED`
- `description`: optional tooltip text
- `isDefault`: optional default marker for single-select
- `sortOrder`: optional ordering metadata, already sorted by the loader

Status filters should load options through `APIModuleActions.get_module_status_options(...)` so the same backend payload is shared between filters and create/update flows.

## Migration Notes

The older `BaseSingleFilterWidget` remains in use for non-status filters. Status filters intentionally do not expose `.combo`; callers must use the filter API (`selected_ids`, `selected_texts`, `set_selected_ids`) rather than reaching into widget internals.

`FilterRefreshService` supports both old combo-backed filters and the new status filter API during this transition.
