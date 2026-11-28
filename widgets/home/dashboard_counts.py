"""The numbers of the home page and of the module toolbars, read from Kavitro: one request per module,
each number the total of a one-record page, all of them aliases of the same query."""
from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple, Optional

from ...constants.module_names import Module, ModuleSupports
from ...module_manager import ModuleManager
from ...python.api_client import APIClient
from ...utils.FilterHelpers.due_filters import between, due_soon_conditions, overdue_conditions
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.settings_logic import SettingsLogic

PROJECT, CONTRACT, COORDINATION = Module.PROJECT.value, Module.CONTRACT.value, Module.COORDINATION.value
EASEMENT = Module.EASEMENT.value
WORKS = Module.WORKS.value
ASBUILT = Module.ASBUILT.value

# module -> (query root, name inside the argument types, further arguments)
SOURCES = {
    PROJECT: ("projects", "Projects", "trashed: WITHOUT"),
    CONTRACT: ("contracts", "Contracts", ""),
    COORDINATION: ("coordinations", "Coordinations", ""),
    EASEMENT: ("easements", "Easements", ""),
    WORKS: ("tasks", "Tasks", ""),
    ASBUILT: ("tasks", "Tasks", ""),
}
WEEKS_AHEAD = 5  # the contracts card: deadlines of the coming weeks
MONTHS_BACK = 12  # the works card: records created, this month included
_WHOLE = "all_"  # alias prefix of the module's whole data


class Selection(NamedTuple):
    """Which records are counted: where-conditions and the tag condition."""

    conditions: tuple = ()
    where_has: Optional[list] = None


class ModuleCounts(NamedTuple):
    total: int
    late: int
    soon: int
    weeks: tuple[int, ...] = ()  # contracts: due in each coming week, this one first
    months: tuple[int, ...] = ()  # works: created in each month, oldest first

    @property
    def fine(self) -> int:
        return max(0, self.total - self.late - self.soon)


class Overview(NamedTuple):
    shown: ModuleCounts  # what the list's filters leave
    whole: ModuleCounts  # everything of the module


def saved_selection(module_key: str) -> Selection:
    """The user's saved status, type and tag preferences of the module."""
    supports = ModuleManager().getModuleSupports(module_key) or (False, False, False, False)
    settings = SettingsLogic()

    def saved(supported: bool, support: ModuleSupports) -> list[str]:
        if not supported:
            return []
        values = settings.load_module_preference_ids(module_key, support_key=support.value) or []
        return [str(value).strip() for value in values if str(value).strip()]

    types = saved(supports[0], ModuleSupports.TYPES)
    statuses = saved(supports[1], ModuleSupports.STATUSES)
    tags = saved(supports[2], ModuleSupports.TAGS)
    conditions = tuple(
        {"column": column, "operator": "IN", "value": ids}
        for column, ids in (("STATUS", statuses), ("TYPE", types)) if ids
    )
    return Selection(conditions, FilterHelper.build_has_tags_condition(tags))


def _month_start(today: date, months_ago: int) -> date:
    year, month = divmod(today.year * 12 + today.month - 1 - months_ago, 12)
    return date(year, month + 1, 1)


def _where(*conditions: dict) -> Optional[dict]:
    return {"AND": list(conditions)} if conditions else None


def basic_wheres(base: tuple, today: date) -> dict[str, Optional[dict]]:
    return {
        "total": _where(*base),
        "late": _where(*base, *overdue_conditions()),
        "soon": _where(*base, *due_soon_conditions(today)),
    }


def conditions_by_alias(module_key: str, base: tuple, today: date) -> dict[str, Optional[dict]]:
    """The where of every number the module's cards show."""
    found = basic_wheres(base, today)
    if module_key == CONTRACT:
        for week in range(WEEKS_AHEAD):
            first = today + timedelta(days=7 * week)
            found[f"week{week}"] = _where(*base, *between("DUE_AT", first, first + timedelta(days=6)))
    if module_key == WORKS:
        for index, months_ago in enumerate(range(MONTHS_BACK - 1, -1, -1)):
            found[f"month{index}"] = _where(
                *base,
                {"column": "CREATED_AT", "operator": "GTE", "value": _month_start(today, months_ago).isoformat()},
                {"column": "CREATED_AT", "operator": "LT", "value": _month_start(today, months_ago - 1).isoformat()})
    return found


def build_query(module_key: str, aliases: list[str], tagged: set[str]) -> str:
    """`tagged`: the aliases that also take the tag condition."""
    root, name, arguments = SOURCES[module_key]
    declared = [f"$where_{alias}: Query{name}WhereWhereConditions" for alias in aliases]
    if tagged:
        declared.append(f"$whereHas: [{name}WhereHasInput!]")
    fields = []
    for alias in aliases:
        taken = ["first: 1", f"where: $where_{alias}", *([arguments] if arguments else [])]
        if alias in tagged:
            taken.append("whereHas: $whereHas")
        fields.append(f"{alias}: {root}({', '.join(taken)}) {{ pageInfo {{ total }} }}")
    return f"query ModuleCounts({', '.join(declared)}) {{\n  " + "\n  ".join(fields) + "\n}"


def fetch_overview(module_key: str, shown: Selection, whole: Selection, today: Optional[date] = None) -> Overview:
    """Raises when a number is missing from the answer: a card never shows a guessed zero."""
    today = today or date.today()
    wheres = conditions_by_alias(module_key, shown.conditions, today)
    tagged = set(wheres) if shown.where_has else set()
    # Without any filter the two are the same records, asked once.
    differs = whole != shown
    if differs:
        # The whole data is narrowed by the module's own scope only, never by tags.
        wheres.update({_WHOLE + alias: where for alias, where in basic_wheres(whole.conditions, today).items()})

    variables = {f"where_{alias}": where for alias, where in wheres.items() if where}
    if tagged:
        variables["whereHas"] = shown.where_has
    data = APIClient().send_query(build_query(module_key, list(wheres), tagged), variables) or {}

    totals = {}
    for alias in wheres:
        total = ((data.get(alias) or {}).get("pageInfo") or {}).get("total")
        if not isinstance(total, int):
            raise RuntimeError(f"module_count_missing: {module_key}.{alias}")
        totals[alias] = total
    counted = ModuleCounts(
        totals["total"], totals["late"], totals["soon"],
        tuple(totals[alias] for alias in wheres if alias.startswith("week")),
        tuple(totals[alias] for alias in wheres if alias.startswith("month")),
    )
    if not differs:
        return Overview(counted, counted)
    return Overview(counted, ModuleCounts(*(totals[_WHOLE + alias] for alias in ("total", "late", "soon"))))


def fetch_counts(module_key: str, today: Optional[date] = None) -> ModuleCounts:
    """The home page: the records the saved preferences leave."""
    saved = saved_selection(module_key)
    return fetch_overview(module_key, saved, saved, today).shown
