from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QDateEdit, QGraphicsColorizeEffect
from PyQt5.QtCore import QDate, QLocale, pyqtSignal
from PyQt5.QtGui import QColor
import datetime

from .DateHelpers import DateHelpers
from wild_code.utils.animation import create_colorize_pulse, AnimationGroupManager


class DateWidget(QWidget):
    """Simple date widget with label and picker.

    Signals:
      - dateChanged(QDate)
    """
    dateChanged = pyqtSignal(QDate)

    def __init__(self, label_prefix: str = "Date", parent=None, locale: QLocale = None):
        super().__init__(parent)
        self._prefix = label_prefix
        self._locale = locale or QLocale.system()
        # Animation/group handle attribute name for manager
        self._warn_anim_attr = "_date_warn_anim_group"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel(self)
        # Warning colorize effect for overdue state (inactive by default)
        self._label_colorize = QGraphicsColorizeEffect(self._label)
        self._label_colorize.setColor(QColor(220, 0, 0))
        self._label_colorize.setStrength(0.0)
        self._label.setGraphicsEffect(self._label_colorize)

        self._picker = QDateEdit(self)
        self._picker.setCalendarPopup(True)
        self._picker.setDate(QDate.currentDate())
        self._picker.dateChanged.connect(self._on_date_changed)

        layout.addWidget(self._label)
        layout.addWidget(self._picker)

        self._refresh_label()

    def _on_date_changed(self, qdate: QDate):
        self._refresh_label(qdate)
        self.dateChanged.emit(qdate)

    def _refresh_label(self, qdate: QDate = None):
        qdate = qdate or self._picker.date()
        py_date = qdate.toPyDate()
        text = None
        try:
            dt = datetime.datetime(py_date.year, py_date.month, py_date.day)
            text = DateHelpers.build_label(self._prefix, dt, self._locale)
        except Exception:
            text = None
        # Fall back to simple locale formatting
        if not text:
            try:
                text = f"{self._prefix}: {qdate.toString(self._locale.dateFormat(QLocale.ShortFormat))}"
            except Exception:
                text = f"{self._prefix}: {qdate.toString()}"
        self._label.setText(text)
        # Apply/clear overdue warning animation
        try:
            state = DateHelpers.due_state(py_date)
            self._apply_overdue_warning(state == "overdue")
        except Exception:
            # On any error, ensure animation is stopped
            self._apply_overdue_warning(False)

    def _apply_overdue_warning(self, is_overdue: bool):
        """Blink the label red/orange if overdue; otherwise stop and reset."""
        try:
            if is_overdue and self._label_colorize is not None:
                grp = create_colorize_pulse(
                    self._label_colorize,
                    QColor(220, 0, 0),       # deep red
                    QColor(255, 150, 0),     # amber
                    duration=900,
                    strength_min=0.15,
                    strength_max=0.85,
                    parent=self,
                )
                AnimationGroupManager.ensure(self, self._warn_anim_attr, grp)
            else:
                AnimationGroupManager.ensure(self, self._warn_anim_attr, None)
                try:
                    if self._label_colorize is not None:
                        self._label_colorize.setStrength(0.0)
                except Exception:
                    pass
        except Exception:
            pass

    def setDate(self, qdate: QDate):
        self._picker.setDate(qdate)
        self._refresh_label(qdate)

    def date(self) -> QDate:
        return self._picker.date()

    def closeEvent(self, event):
        """Ensure any running animations are stopped on close."""
        try:
            AnimationGroupManager.ensure(self, self._warn_anim_attr, None)
            try:
                if self._label_colorize is not None:
                    self._label_colorize.setStrength(0.0)
            except Exception:
                pass
        finally:
            try:
                super().closeEvent(event)
            except Exception:
                pass
