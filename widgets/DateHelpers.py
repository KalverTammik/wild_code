import re
from typing import Optional
from PyQt5.QtCore import QDate, QDateTime, QLocale


import datetime
from ..Logs.python_fail_logger import PythonFailLogger


class DateHelpers:
    @staticmethod
    def parse_iso(s: Optional[str]) -> Optional[datetime.datetime]:
        if not s:
            return None
        try:
            return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="datehelpers_parse_iso_failed",
            )
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

    @staticmethod
    def format_short_date(dt: Optional[datetime.datetime], locale: QLocale) -> str:
        if not dt:
            return "–"
        qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        return locale.toString(qdt.date(), QLocale.ShortFormat)
    

    def date_to_iso_string(self, date_item):
        """Return an API-safe ISO date string (YYYY-MM-DD) from QDate/QDateTime/date/etc."""
        if date_item is None:
            return ""

        if isinstance(date_item, QDate):
            if date_item.isValid():
                return date_item.toString("yyyy-MM-dd")
            return ""

        if isinstance(date_item, QDateTime):
            d = date_item.date()
            if d.isValid():
                return d.toString("yyyy-MM-dd")
            return ""

        if isinstance(date_item, datetime.datetime):
            return date_item.date().strftime("%Y-%m-%d")

        if isinstance(date_item, datetime.date):
            return date_item.strftime("%Y-%m-%d")

        if isinstance(date_item, str):
            s = date_item.strip()

            # ISO datetime -> ISO date
            dt = DateHelpers.parse_iso(s)
            if dt is not None:
                try:
                    return dt.date().strftime("%Y-%m-%d")
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="datehelpers_iso_date_failed",
                    )

            # Qt string representation
            m = re.search(r'QDate\((\d+),\s*(\d+),\s*(\d+)\)', s)
            if m:
                year, month, day = m.groups()
                d = QDate(int(year), int(month), int(day))
                if d.isValid():
                    return d.toString("yyyy-MM-dd")
                return ""

            # Already ISO?
            m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
            if m:
                return s

            # Estonian display format dd.MM.yyyy -> ISO
            m = re.fullmatch(r'(\d{2})\.(\d{2})\.(\d{4})', s)
            if m:
                day, month, year = m.groups()
                d = QDate(int(year), int(month), int(day))
                if d.isValid():
                    return d.toString("yyyy-MM-dd")
            return ""

        return ""
