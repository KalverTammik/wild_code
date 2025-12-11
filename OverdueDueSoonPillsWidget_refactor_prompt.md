# Prompt: OverdueDueSoonPillsWidget – remaining cleanup & unification tasks

You are working in a PyQt5/QGIS plugin codebase. The file `OverdueDueSoonPillsWidget.py` was recently partially refactored to remove checkable pills and move “active” styling to dynamic properties. Review the current implementation and apply the remaining improvements below.

## Context summary (current state)
- `OverdueDueSoonPillsWidget` builds a compact UI: QWidget → QVBoxLayout → QGroupBox → QHBoxLayout → two QPushButtons.
- Buttons are **not checkable** and emit `overdueClicked` / `dueSoonClicked`.
- Counts are set via `set_counts`.
- Visual “active” state is now property-based: `setProperty("active", ...)` + repolish.
- `load_first_overdue_by_module` now uses `self._is_loading` and calls `OverdueDueSoonPillsUtils.refresh_counts_for_module(...)`.
- `ThemeManager.apply_module_style` loads QSS via `QssPaths.OVERDUE_PILLS`.

## Goal
Finish the refactor so that:
1) there is a single clean source of truth for counts/query building,
2) no legacy module-level state remains unless truly required elsewhere,
3) the API is small and explicit (loading, counts, active state),
4) error handling and typing are consistent with the rest of the plugin style,
5) the QSS and widget property contract is clear.

---

## Tasks to implement

### 1. Remove remaining legacy globals (if not used externally)
Currently still present:
```python
OVERDUE_BTN = None
DUE_SOON_BTN = None
```
Action:
- Search the codebase for any external usage of these names.
- If unused, remove them entirely.
- If used somewhere for backward compatibility, replace external references with instance access (`module.overdue_pills.overdue_btn` etc.) and then remove globals.

### 2. Collapse duplicate logic classes
The file still contains:
- `UIControllers`
- `OverdueDueSoonPillsLogic` (almost no value)
- `OverdueDueSoonPillsUtils` (the real workhorse)

Action:
- Prefer **one** path.
- Recommended: **keep `OverdueDueSoonPillsUtils`** and delete `UIControllers` and `OverdueDueSoonPillsLogic`.
- If you keep `UIControllers`, then:
  - fix its state handling and make it call into `OverdueDueSoonPillsUtils`,
  - avoid duplicated query building.

### 3. Fix incorrect class/instance state reference
In `UIControllers.try_fetch`:
```python
except Exception:
    OverdueDueSoonPillsWidget._is_loading = False
```
This is incorrect because `_is_loading` is an instance field.

Action:
- If `UIControllers` is removed, this disappears.
- If retained, remove this line and never mutate widget state from this utility class.

### 4. Unify “days due soon” configuration
You currently have:
- `OverdueDueSoonPillsWidget._days_due_soon`
- `OverdueDueSoonPillsUtils._days_due_soon`

Action:
- Choose **one** source of truth.
- Recommended:
  - store default in `OverdueDueSoonPillsUtils`,
  - allow widget to pass an override to utils when needed,
  - add a small setter on the widget:
    ```python
    def set_due_soon_window(self, days: int) -> None:
        ...
    ```
  - ensure `refresh_counts_for_module` can accept `days` optionally:
    ```python
    def refresh_counts_for_module(module, days: Optional[int] = None)
    ```

### 5. Add explicit loading API
Right now loading is implicit via “…” text during init only.

Action:
- Add:
  ```python
  def set_loading(self, loading: bool) -> None:
      self._is_loading = loading
      if loading:
          self.overdue_btn.setText("…")
          self.due_soon_btn.setText("…")
      self.overdue_btn.setEnabled(not loading)
      self.due_soon_btn.setEnabled(not loading)
  ```
- Update `load_first_overdue_by_module` to use `set_loading(True/False)`.

### 6. Make count refresh non-blocking (if APIClient is synchronous)
If `APIClient.send_query` is synchronous and can block UI, consider:
- moving count fetch into a lightweight worker or queued single-shot pattern used elsewhere in the plugin,
- or at minimum defer the fetch call itself with `QTimer.singleShot(0, ...)` and keep UI responsive.

Action:
- Follow the plugin’s established async pattern if you already have a helper for background networking.

### 7. Tighten typing and naming
Action:
- Add type hints for `module` expected in:
  - `load_first_overdue_by_module(self, module)`
  - `OverdueDueSoonPillsActionHelper.apply_due_filter(module, ...)`
- Consider renaming parameters to clarify intent:
  - `module_enum` vs `module_instance`.
- Ensure return types:
  - `refresh_counts_for_module` returns `tuple[int, int]`.

### 8. QSS contract for `active` property
Ensure the QSS file `OverduePills.qss` matches the new property-based state.

Action:
- Verify selectors like:
  ```css
  #PillOverdue[active="true"] { ... }
  #PillDueSoon[active="true"] { ... }
  ```
- Remove any reliance on `:checked` state for these pills.

### 9. Optional: micro UX enhancements
Action:
- Add tooltips for pills explaining what they filter.
- Consider showing text labels + counts if space allows, e.g.:
  - “Overdue (3)”
  - “Due soon (5)”
  possibly controlled by a flag.

---

## Acceptance criteria
- No module-level state in this file unless proven necessary.
- Only one count/query implementation path.
- Buttons remain **non-checkable**.
- Active state is purely property-based and matches QSS.
- `load_first_overdue_by_module` uses a clean loading API.
- The file reads as a small reusable UI component + a small, focused helper layer.

---

## Suggested final structure
Keep:
- `OverdueDueSoonPillsWidget`
- `OverdueDueSoonPillsUtils`
- `OverdueDueSoonPillsActionHelper`
- `OverduePillsMixin`

Remove:
- `UIControllers`
- `OverdueDueSoonPillsLogic`
- legacy globals

---

## Implementation notes
- Keep the code style consistent with the plugin: elegant, minimal packing/unpacking, instance-driven state.
- Prefer early returns and small helpers.
- Avoid repeated query-string construction logic in multiple places.

