# -*- coding: utf-8 -*-
"""DedupeMixin: provides lightweight duplicate suppression for feed items.

Responsibilities:
- Track stable item IDs across a feed session.
- Decide whether to skip insertion for duplicates.

Public-ish API (used by combining UI class):
- _mark_or_skip_duplicate(item) -> bool
- set_deduplication(enabled: bool)

Safe removal: Only if upstream guarantees no duplicate items across pagination.
"""
from typing import Iterable, Any

class DedupeMixin:
    DEFAULT_ID_KEYS: Iterable[str] = ("id", "uid", "key")

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)  # type: ignore[misc]
        self._seen_item_ids = set()
        self._dedupe_enabled = True
        self._duplicate_skip_count = 0
        self._dedupe_session_token = object()

    def set_deduplication(self, enabled: bool) -> None:
        self._dedupe_enabled = enabled

    # Internal helpers -------------------------------------------------
    def _extract_item_id(self, item: Any):
        if not isinstance(item, dict):
            return None
        for k in self.DEFAULT_ID_KEYS:
            if k in item and item[k] is not None:
                return item[k]
        return None

    def _mark_or_skip_duplicate(self, item: Any) -> bool:
        if not self._dedupe_enabled:
            return False
        stable_id = self._extract_item_id(item)
        if stable_id is None:
            return False
        if stable_id in self._seen_item_ids:
            self._duplicate_skip_count += 1
            if self._duplicate_skip_count > 30:
                self._dedupe_enabled = False
            self._on_duplicate_skipped()
            return True
        self._seen_item_ids.add(stable_id)
        return False

    def _reset_dedupe(self):
        self._seen_item_ids.clear()
        self._duplicate_skip_count = 0
        self._dedupe_session_token = object()

    def _on_duplicate_skipped(self) -> None:
        updater = getattr(self, "_update_feed_counter_live", None)
        if callable(updater):
            updater()
