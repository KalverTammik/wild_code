from typing import Optional
from PyQt5.QtCore import QDateTime, QLocale


import datetime


class DateHelpers:
    @staticmethod
    def parse_iso(s: Optional[str]) -> Optional[datetime.datetime]:
        if not s:
            return None
        try:
            return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception:
            return None

    @staticmethod
    def due_state(target_date: datetime.date, today: Optional[datetime.date] = None) -> str:
        today = today or datetime.datetime.now().date()
        if target_date < today:
            return "overdue"
        if (target_date - today).days <= 5:
            return "soon"
        return "ok"

    # NOTE: This helper uses Qt types; if you want a pure-Python helper file,
    # move this function back into the widget.
    @staticmethod
    def build_label(prefix: str, dt: Optional[datetime.datetime], locale: QLocale) -> str:
        if not dt:
            return f"{prefix}: –"
        qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        day = locale.dayName(qdt.date().dayOfWeek())
        short = locale.toString(qdt.date(), QLocale.ShortFormat)
        return f"{prefix}: {short} ({day})"