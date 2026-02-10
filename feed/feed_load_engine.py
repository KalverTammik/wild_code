from collections import deque

from PyQt5.QtCore import QTimer, QCoreApplication
from ..Logs.switch_logger import SwitchLogger


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
        self.buffer = deque()
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

    def _upstream_feed_logic(self):
        return self.parent_ui.feed_logic if self.parent_ui else None

    def _is_active(self) -> bool:
        if self.parent_ui is not None:
            return bool(getattr(self.parent_ui, "_activated", True))
        # Fallback: check bound load_next_batch target if parent_ui was cleared
        target = getattr(self.load_next_batch, "__self__", None)
        if target is not None and hasattr(target, "_activated"):
            return bool(getattr(target, "_activated", False))
        return True

    def _current_token(self) -> int | None:
        ui = self.parent_ui
        if ui is not None:
            return getattr(ui, "_active_token", None)
        target = getattr(self.load_next_batch, "__self__", None)
        if target is not None:
            return getattr(target, "_active_token", None)
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if token is None:
            return self._is_active()
        ui = self.parent_ui
        if ui is not None and hasattr(ui, "is_token_active"):
            try:
                return bool(ui.is_token_active(token))
            except Exception:
                return False
        target = getattr(self.load_next_batch, "__self__", None)
        if target is not None and hasattr(target, "is_token_active"):
            try:
                return bool(target.is_token_active(token))
            except Exception:
                return False
        if ui is not None:
            return bool(getattr(ui, "_activated", False)) and token == getattr(ui, "_active_token", None)
        if target is not None:
            return bool(getattr(target, "_activated", False)) and token == getattr(target, "_active_token", None)
        return self._is_active()

    def _upstream_has_more(self) -> bool:
        feed_logic = self._upstream_feed_logic()
        return bool(feed_logic and feed_logic.has_more)

    def _should_prefetch(self) -> bool:
        if len(self.buffer) >= max(2, self.buffer_size // 4):
            return False
        return self._upstream_has_more()

    def _request_next_batch_on_drain(self):
        if self._upstream_has_more() and not self._is_loading:
            self.schedule_load()

    # -------------------- Scheduling --------------------
    def schedule_load(self):
    # Debug print removed
        SwitchLogger.log("feed_schedule_load", extra={"pending": self._load_pending, "loading": self._is_loading})
        if not self._is_active():
            SwitchLogger.log("feed_schedule_blocked_inactive")
            return
        if self._load_pending or self._is_loading:
            SwitchLogger.log("feed_schedule_blocked_busy")
            return
        self._load_pending = True
        token = self._current_token()
        QTimer.singleShot(self.debounce_ms, lambda t=token: self._load_next_batch_guarded(t))

    def _load_next_batch_guarded(self, token: int | None = None):
    # Debug print removed
        self._load_pending = False
        SwitchLogger.log("feed_load_guarded_start")
        if not self._is_token_active(token):
            SwitchLogger.log("feed_load_guarded_inactive_token")
            self._is_loading = False
            return
        self._is_loading = True
    # Debug print removed
        if not callable(self.load_next_batch):
            raise TypeError(
                "FeedLoadEngine: load_next_batch is not callable. Did you pass a valid function? Value: {}".format(self.load_next_batch)
            )
        new_items = self.load_next_batch() or []
        SwitchLogger.log("feed_load_guarded_done", extra={"count": len(new_items)})
    # Debug print removed
        if new_items:
            self.buffer.extend(new_items)
        self._start_progressive_insert(token=token)
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
        for _ in range(max_cards):
            if not self.buffer:
                break
            if self.parent_ui and self.parent_ui._is_filled_plus_one():
                break
            self._progressive_insert_next()

    # -------------------- Progressive insert --------------------
    def _start_progressive_insert(self, token: int | None = None):
    # Debug print removed
        if not self.buffer:
            return
        SwitchLogger.log("feed_insert_start", extra={"buffer": len(self.buffer)})
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
            QTimer.singleShot(self._auto_drip_ms, lambda t=token: self._auto_drip_tick(t))

    def _auto_drip_tick(self, token: int | None = None):
        """Called via QTimer to drain a few items per tick.

        Stops when buffer empty or UI reports filled+1 (via parent_ui._is_filled_plus_one()).
        """
        if not self.buffer:
            # Buffer drained: allow another fetch if upstream has more
            self._auto_drip_running = False
            SwitchLogger.log("feed_drip_end_empty")
            self._request_next_batch_on_drain()
            return
        if not self._is_token_active(token):
            self._auto_drip_running = False
            SwitchLogger.log("feed_drip_end_inactive_token")
            return
        ui = self.parent_ui
        # If UI says viewport is filled+1, stop auto-dripping for now
        if ui and ui._is_filled_plus_one():
            self._auto_drip_running = False
            return
        count = 0
        while count < self._auto_drip_batch and self.buffer:
            # Each progressive insert will also check duplicates defensively
            self._progressive_insert_next()
            count += 1
        if self.buffer:
            # Schedule next tick
            QTimer.singleShot(self._auto_drip_ms, lambda t=token: self._auto_drip_tick(t))
        else:
            self._auto_drip_running = False
            self._request_next_batch_on_drain()

    def _progressive_insert_next(self):
    # Debug print removed
        if not self.buffer:
            # Debug print removed
            return
        if not callable(self.progressive_insert_func):
            # Debug print removed
            return
        item = self.buffer.popleft()
    # Debug print removed
    # (Dedupe removed here; handled solely in ModuleBaseUI during actual insertion
    # to prevent double-marking and early duplicate skips.)
        # Guard scroll handler re-entry while inserting programmatically
        ui = self.parent_ui
        if ui:
            ui._ignore_scroll_event = True
        try:
            self.progressive_insert_func(item)
        finally:
            if ui:
                ui._ignore_scroll_event = False
        QCoreApplication.processEvents()

        # If buffer is low, we may prefetch; UI still governs when to render them
        if self._should_prefetch():
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
