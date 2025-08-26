# -*- coding: utf-8 -*-
"""ProgressiveLoadMixin: scroll & progressive feed insertion helpers.

Consumer must define / provide:
- feed_load_engine (FeedLoadEngine) after init
- scroll_area with verticalScrollBar()
- feed_layout layout structure
- _progressive_insert_card(item, insert_at_top=False) method or override
"""
from typing import Optional, Callable
from PyQt5.QtCore import Qt, QTimer, QCoreApplication

class ProgressiveLoadMixin:
    PREFETCH_PX: int = 300

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)  # type: ignore[misc]
        self._ignore_scroll_event = False
        self._scroll_connected = False
        self._autofill_ticks = 0

    # Scroll wiring ----------------------------------------------------
    def _connect_scroll_signals(self) -> None:
        if self._scroll_connected:
            return
        if not hasattr(self, 'scroll_area') or self.scroll_area is None:  # type: ignore[attr-defined]
            return
        bar = self.scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
        if bar is None:
            return
        bar.valueChanged.connect(self._on_scroll_value)
        bar.rangeChanged.connect(self._on_scroll_range)
        self._scroll_connected = True

    def _on_scroll_value(self, value: int) -> None:
        if getattr(self, '_ignore_scroll_event', False):
            return
        if not hasattr(self, 'scroll_area') or self.scroll_area is None:  # type: ignore[attr-defined]
            return
        if not getattr(self, 'feed_logic', None):
            return
        bar = self.scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
        near_bottom = value >= max(0, bar.maximum() - self.PREFETCH_PX)
        if not near_bottom or getattr(self.feed_logic, 'is_loading', False):  # type: ignore[attr-defined]
            return
        engine = getattr(self, 'feed_load_engine', None)
        if not engine:
            return
        if engine.has_buffer():
            engine._progressive_insert_next()
        elif getattr(self.feed_logic, 'has_more', False):  # type: ignore[attr-defined]
            engine.schedule_load()

    def _on_scroll_range(self, _min: int, _max: int) -> None:
        if not hasattr(self, 'scroll_area') or self.scroll_area is None:  # type: ignore[attr-defined]
            return
        bar = self.scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
        self._on_scroll_value(bar.value())

    # Viewport fullness hooks ------------------------------------------
    def _is_scrollable(self) -> bool:
        try:
            bar = self.scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
            return bar.maximum() > 0
        except Exception:
            return False

    def _is_filled_plus_one(self) -> bool:
        return self._is_scrollable()

    # Initial autofill -------------------------------------------------
    def _initial_autofill_tick(self) -> None:
        engine = getattr(self, 'feed_load_engine', None)
        fl = getattr(self, 'feed_logic', None)
        if not engine or not fl:
            return
        # Stop when scrollable or no more data upstream
        if self._is_scrollable() or not getattr(fl, 'has_more', False):
            self._autofill_ticks = 0
            return
        # Tick count retained only as a safeguard (not a hard cap now)
        self._autofill_ticks += 1
        if engine.has_buffer():
            engine.feed_until_filled_plus_one(max_cards=50)
        else:
            if getattr(fl, 'has_more', False) and not getattr(fl, 'is_loading', False):
                engine.schedule_load()
        QTimer.singleShot(0, self._initial_autofill_tick)
