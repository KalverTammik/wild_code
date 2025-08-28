from PyQt5.QtCore import QDateTime, QLocale, Qt, QPoint, QEvent, QTimer
from PyQt5.QtWidgets import QLabel, QWidget, QGridLayout, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtGui import QPixmap
import datetime
from typing import Optional
from ..DateHelpers import DateHelpers
from ...constants.module_icons import ModuleIconPaths, DateIcons

class DatesWidget(QWidget):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setProperty("compact", compact)
        self.item_data = item_data

        # Main layout - vertical to stack under status
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

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
            return locale.toString(qdt.date(), QLocale.ShortFormat)

        def full_tooltip(prefix: str, dt: Optional[datetime.datetime]) -> str:
            return DateHelpers.build_label(prefix, dt, locale)

        # Create the main due date display
        if due_dt:
            state = DateHelpers.due_state(due_dt.date(), today)

            # Due date container
            due_container = QFrame(self)
            due_container.setObjectName("DueDateContainer")
            due_layout = QHBoxLayout(due_container)
            due_layout.setContentsMargins(4, 2, 4, 2)
            due_layout.setSpacing(4)

            # Due date label
            due_label = QLabel("Tähtaeg:")
            due_label.setObjectName("DateLabel")
            due_label.setStyleSheet("font-size: 10px; color: #666; font-weight: 500;")
            due_layout.addWidget(due_label)

            # Due date value
            due_value = QLabel(short_date(due_dt))
            due_value.setObjectName("DateValue")
            due_value.setStyleSheet("font-size: 11px; font-weight: 600;")
            due_value.setToolTip(full_tooltip("Tähtaeg", due_dt))

            # Apply state-based styling
            if state == 'overdue':
                due_value.setStyleSheet("font-size: 11px; font-weight: 600; color: #d32f2f;")
            elif state == 'soon':
                due_value.setStyleSheet("font-size: 11px; font-weight: 600; color: #f57c00;")

            due_layout.addWidget(due_value)
            due_layout.addStretch()

            # Make the container hoverable for showing all dates
            due_container.setMouseTracking(True)
            due_container.installEventFilter(self)

            main_layout.addWidget(due_container)

        # Store other dates for hover popup
        self.other_dates = []
        if start_dt:
            self.other_dates.append(("Algus:", start_dt))
        if created_dt:
            self.other_dates.append(("Loodud:", created_dt))
        if updated_dt:
            self.other_dates.append(("Muudetud:", updated_dt))

        self.hover_popup = None

    def eventFilter(self, obj, event):
        if obj.objectName() == "DueDateContainer":
            if event.type() == QEvent.Enter:
                self.show_dates_popup(obj)
            elif event.type() == QEvent.Leave:
                self.hide_dates_popup()
        return super().eventFilter(obj, event)

    def show_dates_popup(self, anchor_widget):
        if not self.other_dates:
            return

        if self.hover_popup:
            self.hide_dates_popup()

        # Create popup widget
        self.hover_popup = QWidget(self.window(), Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.hover_popup.setObjectName("DatesPopup")
        self.hover_popup.setAttribute(Qt.WA_DeleteOnClose, True)
        self.hover_popup.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.hover_popup.setFocusPolicy(Qt.NoFocus)
        self.hover_popup.setMouseTracking(True)

        layout = QVBoxLayout(self.hover_popup)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Add all other dates
        locale = QLocale.system()
        for label_text, dt in self.other_dates:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            label = QLabel(label_text)
            label.setStyleSheet("font-size: 10px; color: #666; font-weight: 500;")
            label.setFixedWidth(60)
            row_layout.addWidget(label)

            date_value = QLabel(self.short_date(dt, locale))
            date_value.setStyleSheet("font-size: 11px; font-weight: 500;")
            date_value.setToolTip(DateHelpers.build_label(label_text.replace(":", ""), dt, locale))
            row_layout.addWidget(date_value)

            layout.addLayout(row_layout)

        # Position popup near the anchor widget
        self.hover_popup.adjustSize()
        pos = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
        self.hover_popup.move(pos)
        self.hover_popup.show()
        self.hover_popup.raise_()

    def hide_dates_popup(self):
        if self.hover_popup:
            self.hover_popup.close()
            self.hover_popup = None

    def short_date(self, dt: Optional[datetime.datetime], locale) -> str:
        if not dt:
            return "–"
        qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        return locale.toString(qdt.date(), QLocale.ShortFormat)
