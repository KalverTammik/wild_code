# -*- coding: utf-8 -*-
"""ProgressiveLoadMixin: scroll & progressive feed insertion helpers.

Consumer must define / provide:
- feed_load_engine (FeedLoadEngine) after init
- scroll_area with verticalScrollBar()
- feed_layout layout structure
- _progressive_insert_card(item, insert_at_top=False) method or override
"""
from PyQt5.QtCore import QTimer

class ProgressiveLoadMixin:
    PREFETCH_PX: int = 300

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)  # type: ignore[misc]
        self._ignore_scroll_event = False
        self._scroll_connected = False
        self._autofill_ticks = 0
        self.scroll_area = None  # type: ignore[attr-defined]
        self.feed_logic = None  # type: ignore[attr-defined]
        self.feed_load_engine = None  # type: ignore[attr-defined]

    # Scroll wiring ----------------------------------------------------
    def _connect_scroll_signals(self) -> None:
        if self._scroll_connected:
            return
        scroll_area = self.scroll_area  # type: ignore[attr-defined]
        if not scroll_area:
            return
        bar = scroll_area.verticalScrollBar()
        if bar is None:
            return
        bar.valueChanged.connect(self._on_scroll_value)
        bar.rangeChanged.connect(self._on_scroll_range)
        self._scroll_connected = True

    def _on_scroll_value(self, value: int) -> None:
        if self._ignore_scroll_event:
            return
        scroll_area = self.scroll_area  # type: ignore[attr-defined]
        feed_logic = self.feed_logic  # type: ignore[attr-defined]
        if not scroll_area or not feed_logic:
            return
        bar = scroll_area.verticalScrollBar()
        near_bottom = value >= max(0, bar.maximum() - self.PREFETCH_PX)
        if not near_bottom or feed_logic.is_loading:
            return
        engine = self.feed_load_engine  # type: ignore[attr-defined]
        if not engine:
            return
        if engine.has_buffer():
            engine._progressive_insert_next()
        elif feed_logic.has_more:
            engine.schedule_load()

    def _on_scroll_range(self, _min: int, _max: int) -> None:
        scroll_area = self.scroll_area  # type: ignore[attr-defined]
        if not scroll_area:
            return
        bar = scroll_area.verticalScrollBar()
        self._on_scroll_value(bar.value())

    # Viewport fullness hooks ------------------------------------------
    def _is_scrollable(self) -> bool:
        scroll_area = self.scroll_area  # type: ignore[attr-defined]
        if not scroll_area:
            return False
        bar = scroll_area.verticalScrollBar()
        return bar.maximum() > 0

    def _is_filled_plus_one(self) -> bool:
        return self._is_scrollable()

    # Initial autofill -------------------------------------------------
    def _initial_autofill_tick(self) -> None:
        engine = self.feed_load_engine  # type: ignore[attr-defined]
        feed_logic = self.feed_logic  # type: ignore[attr-defined]
        if not engine or not feed_logic:
            return
        # Stop when scrollable or no more data upstream
        if self._is_scrollable() or not feed_logic.has_more:
            self._autofill_ticks = 0
            return
        # Tick count retained only as a safeguard (not a hard cap now)
        self._autofill_ticks += 1
        if engine.has_buffer():
            engine.feed_until_filled_plus_one(max_cards=50)
        else:
            if feed_logic.has_more and not feed_logic.is_loading:
                engine.schedule_load()
        QTimer.singleShot(0, self._initial_autofill_tick)
