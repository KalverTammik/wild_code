# 🛠️ Refactoring Checklist for Module Standardization

This checklist tracks the progress of refactoring and standardizing key methods and patterns across modules. Items are grouped by status for clarity.

## How to Use
- Review the TODO list and pick the next item to work on.
- Move active tasks to the WORKING section.
- When finished, mark as DONE and add a brief description.

---




## WORKING


## DONE
[*] Consider using `QCoreApplication.processEvents()` for smoother UI updates during long-running operations or batch loads — DONE
  - Added to all major batch UI update loops (feed item insertion, filter widget updates, card updates, widget removals) across modules and widgets. This ensures the UI remains responsive and elements update smoothly during long-running operations or batch loads. You can now tune or remove as needed for performance.
[*] Centralize `_schedule_load` and `_load_next_batch_guarded` logic — DONE
  - Both methods are now fully centralized in FeedLoadEngine and used by all modules via ModuleBaseUI. No duplicate scheduling logic remains in child modules.
[*] Standardize `load_next_batch` logic — DONE
  - All modules now use a unified load_next_batch pattern, calling the base class method and passing any module-specific hooks. The engine and UI are fully harmonized.
[*] Standardize `_on_scroll_value` and `_on_scroll_range` logic — DONE
  - Scroll handling logic is now centralized in `ModuleBaseUI` and used by all modules. No logging is included; override in child modules if needed.
[*] Standardize `activate` method across modules — DONE
  - Shared activation logic is now in `ModuleBaseUI.activate`. Modules call `super().activate()` and add their own custom steps as needed.
[*] Centralize `set_feed_counter` logic in `ModuleBaseUI` and update modules to use it — DONE
  - Both Projects and Contracts modules now use the shared base method for feed counter updates.
  - Note: Feed clearing now uses `clear_feed(self.feed_layout, self._empty_state)`.
- [*] Centralize `clear_feed` logic in `ModuleBaseUI` and update modules to use it — DONE (legacy `_clear_feed_keep_stretch` removed)
  - Both Projects and Contracts modules now use the shared base method for feed clearing.
- [*] Standardize theming for both modules — DONE
  - Theming now uses `ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])`.
- [*] Centralize filter widget registration and signal handling — DONE
  - Filter widgets are registered with `ToolbarArea`, which emits a `filtersChanged` signal for modular, scalable filter management.

---

## Reference: Similar Functionality (for mapping)
- `clear_feed` (Projects) ↔ `clear_feed` (Contracts)
- `set_feed_counter` (Projects) ↔ `set_feed_counter` (Contracts)
- `activate` (Projects) ↔ `activate` (Contracts)
- `_on_scroll_value` (Projects) ↔ `_on_scroll_value` (Contracts)
- `_on_scroll_range` (Projects) ↔ `_on_scroll_range` (Contracts)
- `_schedule_load` (Projects) ↔ `_schedule_load` (Contracts)
- `_load_next_batch_guarded` (Projects) ↔ `_load_next_batch_guarded` (Contracts)
- `load_next_batch` (Projects) ↔ `load_next_batch` (Contracts)