"""Ordering, grouping and saved presentation choices for the Works feed."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ...feed.FeedLogic import UnifiedFeedLogic
from ...languages.translation_keys import TranslationKeys as K
from ...python.responses import DataDisplayExtractors


REMOTE_SORTS = {
    "title": "TITLE", "due": "DUE_AT", "start": "START_AT",
    "created": "CREATED_AT", "updated": "UPDATED_AT",
}
LOCAL_SORTS = ("status", "type", "priority", "responsible")
SORT_FIELDS = ("default", *REMOTE_SORTS, *LOCAL_SORTS)
GROUP_FIELDS = ("none", "status", "type", "priority", "responsible", "deadline")
PRIORITIES = ("URGENT", "HIGH", "MEDIUM", "LOW")
PRIORITY_LABELS = (K.WORKS_PRIORITY_URGENT, K.WORKS_PRIORITY_HIGH,
                   K.WORKS_PRIORITY_MEDIUM, K.WORKS_PRIORITY_LOW)


@dataclass(frozen=True)
class ListChoices:
    sort: str = "default"
    descending: bool = False
    group: str = "none"


class WorksListPreferences:
    def __init__(self, settings, *, user_id, endpoint, module_key="works"):
        self.settings = settings
        identity = json.dumps([endpoint, str(user_id)], ensure_ascii=False)
        self.key = (f"kavitro/list-view/{hashlib.sha256(identity.encode()).hexdigest()}/{module_key}"
                    if user_id else None)

    def load(self):
        raw = self.settings.value(self.key, "") if self.key else ""
        try:
            value = json.loads(raw) if isinstance(raw, str) and raw else {}
        except ValueError:
            value = {}
        if not isinstance(value, dict):
            value = {}
        return ListChoices(
            value.get("sort") if value.get("sort") in SORT_FIELDS else "default",
            value.get("descending") is True,
            value.get("group") if value.get("group") in GROUP_FIELDS else "none",
        )

    def save(self, choices):
        if self.key:
            self.settings.setValue(self.key, json.dumps(vars(choices)))


def _text_key(value):
    # Estonian alphabet and natural number order, independent of OS locale.
    alphabet = "abcdefghijklmnopqrsšzžtuvwõäöüxy"
    return tuple((0, int(part)) if part.isdigit() else
                 (1, tuple(alphabet.find(c) if c in alphabet else ord(c) + 100 for c in part))
                 for part in re.split(r"(\d+)", str(value).casefold()))


def _responsible(item):
    nodes, _ = DataDisplayExtractors.extract_members(item)
    return [node for node in nodes if not node.get("deletedAt")]


def sort_loaded_items(items, choices):
    items = list(items)
    if choices.sort not in LOCAL_SORTS:
        return items  # Preserve the server's order across page boundaries.

    def value(item):
        if choices.sort in ("status", "type"):
            name = (item.get(choices.sort) or {}).get("name")
            return _text_key(name) if name else None
        if choices.sort == "priority":
            priority = DataDisplayExtractors.extract_priority(item)
            return PRIORITIES.index(priority) if priority in PRIORITIES else None
        names = [DataDisplayExtractors.extract_member_display_name(node) for node in _responsible(item)]
        return tuple(sorted(_text_key(name) for name in names)) if names else None

    items.sort(key=lambda item: _text_key(item.get("id", "")))
    present = [item for item in items if value(item) is not None]
    missing = [item for item in items if value(item) is None]
    return sorted(present, key=value, reverse=choices.descending) + missing


@dataclass
class ListGroup:
    key: tuple
    label: str
    order: tuple
    items: list = field(default_factory=list)


def _deadline_bucket(item, today):
    if str((item.get("status") or {}).get("type", "")).upper() == "CLOSED":
        return 7, K.LIST_DEADLINE_CLOSED
    raw = str(item.get("dueAt") or "").strip()
    try:
        if len(raw) == 10:
            due = date.fromisoformat(raw)
        else:
            due = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone().date()
    except ValueError:
        return 8, K.LIST_DEADLINE_NONE
    if due < today:
        return 0, K.LIST_DEADLINE_OVERDUE
    if due == today:
        return 1, K.LIST_DEADLINE_TODAY
    if due == today + timedelta(days=1):
        return 2, K.LIST_DEADLINE_TOMORROW
    week_end = today + timedelta(days=6 - today.weekday())
    if due <= week_end:
        return 3, K.LIST_DEADLINE_WEEK
    if due <= week_end + timedelta(days=7):
        return 4, K.LIST_DEADLINE_NEXT_WEEK
    return 5, K.LIST_DEADLINE_LATER


def group_loaded_items(items, choices, lang, *, today=None):
    today = today or date.today()
    groups = {}
    for item in sort_loaded_items(items, choices):
        descriptors = []
        if choices.group == "none":
            descriptors = [(('none',), "", (0,))]
        elif choices.group in ("status", "type"):
            node = item.get(choices.group) or {}
            name = str(node.get("name") or "").strip()
            label = name or lang.translate(K.LIST_VALUE_MISSING)
            descriptors = [((choices.group, str(node.get("id") or name)), label,
                            (0, _text_key(name)) if name else (1,))]
        elif choices.group == "responsible":
            for node in _responsible(item):
                name = DataDisplayExtractors.extract_member_display_name(node)
                descriptors.append((('responsible', str(node.get('id') or name)), name, (0, _text_key(name))))
            if not descriptors:
                descriptors = [(('responsible', ''), lang.translate(K.CARD_RESPONSIBLE_UNASSIGNED), (1,))]
        elif choices.group == "priority":
            priority = DataDisplayExtractors.extract_priority(item)
            rank = PRIORITIES.index(priority) if priority in PRIORITIES else len(PRIORITIES)
            label = lang.translate(PRIORITY_LABELS[rank] if rank < len(PRIORITIES) else K.WORKS_PRIORITY_NONE)
            descriptors = [(('priority', priority), label, (rank,))]
        elif choices.group == "deadline":
            rank, key = _deadline_bucket(item, today)
            descriptors = [(('deadline', rank), lang.translate(key), (rank,))]
        for key, label, order in dict((d[0], d) for d in descriptors).values():
            if key not in groups:
                groups[key] = ListGroup(key, label, order)
            groups[key].items.append(item)
    return sorted(groups.values(), key=lambda group: (group.order, str(group.key)))


class WorksFeedLogic(UnifiedFeedLogic):
    _PAGE_STATE = (
        'end_cursor', 'has_more', 'total_count', 'last_response', 'last_error',
        'last_error_kind', 'last_error_message', '_missing_phase', '_sort_seen_ids',
        '_loaded_items_debug',
    )

    def snapshot(self):
        """Copy request state so a worker cannot change the visible feed's cursor/filters."""
        from copy import copy, deepcopy
        snapshot = copy(self)
        snapshot.where = deepcopy(self.where)
        snapshot._extra_args = deepcopy(self._extra_args)
        snapshot._sort_seen_ids = set(self._sort_seen_ids)
        snapshot.is_loading = False
        return snapshot

    @staticmethod
    def fetch_snapshot(snapshot):
        return snapshot, snapshot.fetch_next_batch()

    def accept_snapshot(self, snapshot):
        for name in self._PAGE_STATE:
            if hasattr(snapshot, name):
                setattr(self, name, getattr(snapshot, name))
        self.is_loading = False

    """Server sorting with an explicit second pass for missing date values."""
    def __init__(self, *args, **kwargs):
        self.choices = ListChoices()
        self._missing_phase = False
        self._sort_seen_ids = set()
        super().__init__(*args, **kwargs)

    def reset(self):
        super().reset()
        self._missing_phase = False
        self._sort_seen_ids.clear()

    def fetch_next_batch(self):
        if self._single_item_mode or self.choices.sort == "default":
            return super().fetch_next_batch()
        if not self.has_more or self.is_loading:
            return []
        column = REMOTE_SORTS.get(self.choices.sort)
        nullable = column in ("DUE_AT", "START_AT", "CREATED_AT", "UPDATED_AT")
        # At most two requests: an empty non-null page may transition to nulls.
        for _ in range(2):
            original_where, original_extra = self.where, self._extra_args
            order_by = []
            if column and not self._missing_phase:
                order_by.append({"column": column, "order": "DESC" if self.choices.descending else "ASC"})
            order_by.append({"column": "ID", "order": "ASC"})
            self._extra_args = {**original_extra, "orderBy": order_by}
            if nullable:
                condition = {"column": column, "operator": "IS_NULL" if self._missing_phase else "IS_NOT_NULL"}
                self.where = {"AND": [original_where, condition] if original_where else [condition]}
            try:
                items = super().fetch_next_batch()
            finally:
                self.where, self._extra_args = original_where, original_extra
            if self.last_error:
                return items
            self._sort_seen_ids.update(str(item["id"]) for item in items)
            if nullable:
                self.total_count = None  # Each pass has its own server count.
                if not self.has_more and not self._missing_phase:
                    self._missing_phase = True
                    self.end_cursor = None
                    self.has_more = True
                    if not items:
                        continue
                if not self.has_more:
                    self.total_count = len(self._sort_seen_ids)
            return items
        return []
