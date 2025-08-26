from PyQt5.QtCore import QTimer, QCoreApplication

class FeedLoadEngine:
    """
    Centralized engine for scheduling and guarding batch loads in modules.

    Improvements:
    - Adds a public buffer API (has_buffer, drip_from_buffer, feed_until_filled_plus_one).
    - Optional parent_ui attachment to cooperate with viewport fullness logic.
    - Safer initial insert (delegates "fill" decisions to UI, avoids runaway loops).
    - Keeps one fetch in flight; debounced scheduling remains intact.
    """

    def __init__(self, load_next_batch, debounce_ms=80, progressive_insert_func=None, buffer_size=20):
        # Core inputs
        self.load_next_batch = load_next_batch
        self.debounce_ms = debounce_ms

        # State flags
        self._load_pending = False
        self._is_loading = False

        # Buffer
        self.buffer = []
        self.buffer_size = buffer_size

        # Hook for UI insertion callback; may be set later via attach()
        self.progressive_insert_func = progressive_insert_func

        # cooperation hooks
        self.parent_ui = None  # set by UI (e.g., ContractUi)

        # Auto-drip pacing (small, configurable batches driven by QTimer)
        self._auto_drip_ms = 20
        self._auto_drip_batch = 3
        self._auto_drip_running = False
        # First batch acceleration flag
        self._first_batch_fast = True

    # -------------------- Public wiring --------------------
    def attach(self, parent_ui=None, progressive_insert_func=None):
        if parent_ui is not None:
            self.parent_ui = parent_ui
        if progressive_insert_func is not None:
            self.progressive_insert_func = progressive_insert_func
        return self

    # -------------------- Scheduling --------------------
    def schedule_load(self):
    # Debug print removed
        if self._load_pending or self._is_loading:
            return
        self._load_pending = True
        QTimer.singleShot(self.debounce_ms, self._load_next_batch_guarded)

    def _load_next_batch_guarded(self):
    # Debug print removed
        self._load_pending = False
        self._is_loading = True
    # Debug print removed
        if not callable(self.load_next_batch):
            raise TypeError(
                "FeedLoadEngine: load_next_batch is not callable. Did you pass a valid function? Value: {}".format(self.load_next_batch)
            )
        new_items = self.load_next_batch() or []
    # Debug print removed
        if new_items:
            self.buffer.extend(new_items)
        self._start_progressive_insert()
        self._is_loading = False

    # -------------------- Buffer API --------------------
    def has_buffer(self) -> bool:
        return bool(self.buffer)

    def drip_from_buffer(self, max_cards: int = 1):
        """Release up to max_cards from engine buffer to progressive_insert_func."""
        pushed = 0
        while pushed < max_cards and self.buffer:
            self._progressive_insert_next()
            pushed += 1

    def feed_until_filled_plus_one(self, max_cards: int = 50):
        """Ask UI whether the viewport is filled+1 and stop when it is (or buffer ends)."""
        ui = getattr(self, "parent_ui", None)
        for _ in range(max_cards):
            if not self.buffer:
                break
            if ui and hasattr(ui, "_is_filled_plus_one") and ui._is_filled_plus_one():
                break
            self._progressive_insert_next()

    # -------------------- Progressive insert --------------------
    def _start_progressive_insert(self):
    # Debug print removed
        if not self.buffer:
            return
        # On the very first batch, insert a larger chunk immediately to avoid perceived slowness
        if self._first_batch_fast:
            self._first_batch_fast = False
            burst = min(len(self.buffer), max(self._auto_drip_batch * 4, 10))
            for _ in range(burst):
                if not self.buffer:
                    break
                self._progressive_insert_next()
            # If buffer emptied fully, no need to schedule timer
            if not self.buffer:
                return
        # Start paced auto-drip which will consume small batches per tick until buffer is drained
        if not self._auto_drip_running:
            self._auto_drip_running = True
            QTimer.singleShot(self._auto_drip_ms, self._auto_drip_tick)

    def _auto_drip_tick(self):
        """Called via QTimer to drain a few items per tick.

        Stops when buffer empty or UI reports filled+1 (via parent_ui._is_filled_plus_one()).
        """
        try:
            if not self.buffer:
                # Buffer drained: allow another fetch if upstream has more
                self._auto_drip_running = False
                try:
                    fl = getattr(getattr(self, 'parent_ui', None), 'feed_logic', None)
                    if fl and getattr(fl, 'has_more', False) and not self._is_loading:
                        self.schedule_load()
                except Exception:
                    pass
                return
            ui = getattr(self, 'parent_ui', None)
            # If UI says viewport is filled+1, stop auto-dripping for now
            if ui and hasattr(ui, '_is_filled_plus_one') and ui._is_filled_plus_one():
                self._auto_drip_running = False
                return
            count = 0
            while count < self._auto_drip_batch and self.buffer:
                # Each progressive insert will also check duplicates defensively
                self._progressive_insert_next()
                count += 1
            if self.buffer:
                # Schedule next tick
                QTimer.singleShot(self._auto_drip_ms, self._auto_drip_tick)
            else:
                self._auto_drip_running = False
        except Exception:
            # On unexpected error, stop auto-drip to avoid busy loop
            self._auto_drip_running = False

    def _progressive_insert_next(self):
    # Debug print removed
        if not self.buffer:
            # Debug print removed
            return
        if not callable(self.progressive_insert_func):
            # Debug print removed
            return
        item = self.buffer.pop(0)
    # Debug print removed
    # (Dedupe removed here; handled solely in ModuleBaseUI during actual insertion
    # to prevent double-marking and early duplicate skips.)
        # Guard scroll handler re-entry while inserting programmatically
        ui_for_flag = getattr(self, 'parent_ui', None)
        if ui_for_flag:
            try:
                ui_for_flag._ignore_scroll_event = True
            except Exception:
                pass
        try:
            self.progressive_insert_func(item)
        finally:
            if ui_for_flag:
                try:
                    ui_for_flag._ignore_scroll_event = False
                except Exception:
                    pass
        QCoreApplication.processEvents()

        # If buffer is low, we may prefetch; UI still governs when to render them
        if len(self.buffer) < max(2, self.buffer_size // 4):
            # Only prefetch if upstream still reports more pages
            try:
                fl = getattr(getattr(self, 'parent_ui', None), 'feed_logic', None)
                has_more = getattr(fl, 'has_more', False) if fl else False
            except Exception:
                has_more = False
            if has_more:
                self.schedule_load()

    # -------------------- Reset --------------------
    def reset(self):
        self._load_pending = False
        self._is_loading = False
        self.buffer.clear()
        # Stop any auto-drip loop; future schedule_load will restart
        self._auto_drip_running = False
        # First-batch acceleration re-armed
        self._first_batch_fast = True

    def cancel(self):
        """Alias for reset for external clarity."""
        self.reset()
