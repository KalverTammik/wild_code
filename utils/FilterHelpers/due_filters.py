"""The where-conditions of "overdue" and "due soon"; the lists and the indicators count the same records."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

DAYS_DUE_SOON = 3


def between(column: str, first: date, last: date) -> list[dict]:
    return [{"column": column, "operator": "GTE", "value": first.isoformat()},
            {"column": column, "operator": "LTE", "value": last.isoformat()}]


def overdue_conditions() -> list[dict]:
    """Overdue as the server counts it: the due date has passed and the record is not settled."""
    return [{"column": "IS_OVERDUE", "operator": "EQ", "value": True}]


def due_soon_conditions(today: Optional[date] = None) -> list[dict]:
    """Due from today within the next days."""
    first = today or date.today()
    return between("DUE_AT", first, first + timedelta(days=DAYS_DUE_SOON))
