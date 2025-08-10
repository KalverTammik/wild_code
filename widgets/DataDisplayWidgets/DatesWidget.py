from PyQt5.QtCore import QDateTime, QLocale, Qt
from PyQt5.QtWidgets import QLabel, QWidget, QGridLayout, QSizePolicy
from PyQt5.QtGui import QPixmap
import datetime
from typing import Optional
from ..DateHelpers import DateHelpers
from ...constants.module_icons import ModuleIconPaths, DateIcons

class DatesWidget(QWidget):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setProperty("compact", compact)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8 if not compact else 6)
        grid.setVerticalSpacing(4 if not compact else 2)

        # Column behaviors: icon column is narrow & fixed-ish; date column expands
        grid.setColumnMinimumWidth(0, 20)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        locale = QLocale.system()
        today = datetime.datetime.now().date()

        start_dt   = DateHelpers.parse_iso(item_data.get('startAt'))
        due_dt     = DateHelpers.parse_iso(item_data.get('dueAt'))
        created_dt = DateHelpers.parse_iso(item_data.get('createdAt'))
        updated_dt = DateHelpers.parse_iso(item_data.get('updatedAt'))

        def short_date(dt: Optional[datetime.datetime]) -> str:
            if not dt:
                return "–"
            qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            # keep dd.MM.yyyy so widths match nicely in light theme
            return locale.toString(qdt.date(), QLocale.ShortFormat)

        def full_tooltip(prefix: str, dt: Optional[datetime.datetime]) -> str:
            # Use Qt locale-based formatting to avoid Windows strftime year>=1900 limitation
            return DateHelpers.build_label(prefix, dt, locale)

        def get_icon_pixmap(basename: Optional[str]) -> Optional[QPixmap]:
            if not basename:
                return None
            path = ModuleIconPaths.themed(basename)
            pm = QPixmap(path)
            return pm.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pm.isNull() else None

        row = 0

        def add_row(icon_pm: Optional[QPixmap], fallback_text: str, prefix: str, dt: Optional[datetime.datetime],
                    obj_name: str = None, due_state: Optional[str] = None):
            nonlocal row
            if dt is None:
                return  # hide pair entirely if not set

            # Icon (pixmap if available, else fallback text)
            icon = QLabel(self)
            icon.setFixedWidth(20)
            icon.setAlignment(Qt.AlignCenter)
            icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if icon_pm is not None:
                icon.setPixmap(icon_pm)
            else:
                icon.setText(fallback_text)

            # Date value (centered within its column)
            date = QLabel(short_date(dt), self)
            date.setAlignment(Qt.AlignCenter)
            date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            if obj_name:
                date.setObjectName(obj_name)
            date.setToolTip(full_tooltip(prefix, dt))
            if due_state:
                date.setProperty("dueState", due_state)
                date.style().unpolish(date); date.style().polish(date)

            grid.addWidget(icon, row, 0, alignment=Qt.AlignCenter)
            grid.addWidget(date, row, 1, alignment=Qt.AlignCenter)
            row += 1

        # Start (use a neutral schedule icon for now)
        start_pm = get_icon_pixmap(DateIcons.ICON_DATE_SOON)
        add_row(start_pm, "[S]", "Algus", start_dt, obj_name="DateLine")

        # Due (with state-based icon)
        if due_dt:
            state = DateHelpers.due_state(due_dt.date(), today)  # ok | soon | overdue
        else:
            state = None
        due_icon = None
        if state == 'overdue':
            due_icon = DateIcons.ICON_DATE_OVERDUE
        elif state == 'soon':
            due_icon = DateIcons.ICON_DATE_SOON
        else:
            due_icon = DateIcons.ICON_DATE_SOON
        due_pm = get_icon_pixmap(due_icon)
        add_row(due_pm, "[D]", "Tähtaeg", due_dt, obj_name="DateDueLine", due_state=state)

        # Created
        created_pm = get_icon_pixmap(DateIcons.ICON_DATE_CREATED_AT)
        add_row(created_pm, "[C]", "Loodud", created_dt, obj_name="DateMeta")

        # Updated
        updated_pm = get_icon_pixmap(DateIcons.ICON_DATE_LAST_MODIFIED)
        add_row(updated_pm, "[U]", "Muudetud", updated_dt, obj_name="DateMeta")
