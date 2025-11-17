# -*- coding: utf-8 -*-
"""FeedCounterMixin: encapsulates loaded/total counter logic.

Relies on attributes provided by consumer class:
- feed_counter widget exposing set_loaded_total(loaded, total)
- feed_logic (optional) with has_more, total_count
- feed_layout (QVBoxLayout pattern: [empty_label, cards..., stretch])
"""
from typing import Optional

class FeedCounterMixin:
    feed_counter = None  # type: ignore[attr-defined]
    feed_logic = None  # type: ignore[attr-defined]
    feed_layout = None  # type: ignore[attr-defined]

    def _set_feed_counter(self, loaded: int, total: Optional[int]) -> None:
        counter = self.feed_counter  # type: ignore[attr-defined]
        if not counter:
            return
        display_total = total
        feed_logic = self.feed_logic  # type: ignore[attr-defined]
        has_more = bool(feed_logic and feed_logic.has_more)
        if isinstance(total, int) and loaded > total:
            display_total = f"{total}+" if has_more else loaded
        counter.set_loaded_total(loaded, display_total)

    def _compute_loaded_cards(self) -> int:
        layout = self.feed_layout  # type: ignore[attr-defined]
        if layout is None:
            return 0
        count = layout.count()
        if count == 0:
            return 0
        real_cards = 0
        for i in range(count):
            item = layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if not w:
                continue
            name = w.objectName() or ""
            if name == "ModuleInfoCard":
                real_cards += 1
        if real_cards == 0 and count >= 3:
            return count - 2
        return real_cards

    def _update_feed_counter_live(self) -> None:
        feed_logic = self.feed_logic  # type: ignore[attr-defined]
        total = feed_logic.total_count if feed_logic else None
        loaded = self._compute_loaded_cards()
        self._set_feed_counter(loaded, total)
