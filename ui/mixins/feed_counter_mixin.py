# -*- coding: utf-8 -*-
"""FeedCounterMixin: encapsulates loaded/total counter logic.

Relies on attributes provided by consumer class:
- feed_counter widget exposing set_loaded_total(loaded, total)
- feed_logic (optional) with has_more, total_count
- feed_layout (QVBoxLayout pattern: [empty_label, cards..., stretch])
"""
from typing import Optional

class FeedCounterMixin:
    def _set_feed_counter(self, loaded: int, total: Optional[int]) -> None:
        if not (hasattr(self, 'feed_counter') and getattr(self, 'feed_counter')):
            return
        display_total = total
        try:
            fl = getattr(self, 'feed_logic', None)
            has_more = getattr(fl, 'has_more', False) if fl else False
            if isinstance(total, int) and loaded > total:
                if has_more:
                    display_total = f"{total}+"
                else:
                    display_total = loaded
        except Exception:
            pass
        try:
            self.feed_counter.set_loaded_total(loaded, display_total)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _compute_loaded_cards(self) -> int:
        layout = getattr(self, 'feed_layout', None)
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
        fl = getattr(self, 'feed_logic', None)
        total = getattr(fl, 'total_count', None) if fl else None
        loaded = self._compute_loaded_cards()
        self._set_feed_counter(loaded, total)
