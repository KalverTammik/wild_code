from PyQt5.QtCore import QDateTime, QLocale, Qt, QTimer
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QFrame
import datetime
from typing import Optional
from ..DateHelpers import DateHelpers
from ..theme_manager import ThemeManager
from ...languages.language_manager import LanguageManager
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...python.responses import DataDisplayExtractors
from ...ui.window_state.popup_helpers import PopupHelpers


class DatesPopupWidget(QWidget):
    """Custom popup widget for displaying additional dates with proper theming."""

    def __init__(self, dates_list, parent=None):
        super().__init__(parent)
        self.dates_list = dates_list

        # Set popup properties
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

        # Create a frame for the content with theming
        self.frame = QFrame(self)
        self.frame.setObjectName("PopupFrame")
        self.retheme()
        
        # Main layout on the frame
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Add all dates
        locale = QLocale.system()
        for label_text, dt in self.dates_list:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            label = QLabel(label_text)
            label.setObjectName("Label")
            label.setFixedWidth(60)
            row_layout.addWidget(label)

            date_value = QLabel(self._short_date(dt, locale))
            date_value.setObjectName("Value")
            date_value.setToolTip(DateHelpers.build_label(label_text.replace(":", ""), dt, locale))
            row_layout.addWidget(date_value)

            layout.addLayout(row_layout)

        # Set the frame as the central widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)

    def _short_date(self, dt: Optional[datetime.datetime], locale) -> str:
        if not dt:
            return "–"
        qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        return locale.toString(qdt.date(), QLocale.ShortFormat)

    def retheme(self):
        """Reapply theme styles when theme changes."""
        PopupHelpers.apply_popup_style(self.frame, "dates")
        # Force style refresh
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)

class DatesWidget(QWidget):
    def __init__(self, item_data, parent=None, compact=False, lang_manager=None):
        super().__init__(parent)
        self.setProperty("compact", compact)
        self.item_data = item_data
        self.lang_manager = lang_manager or LanguageManager()

        # Main layout - vertical to stack under status
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        locale = QLocale.system()
        today = datetime.datetime.now().date()
        
        dates = DataDisplayExtractors.extract_dates(item_data)
        start_dt = DateHelpers.parse_iso(dates.start_at)
        due_dt = DateHelpers.parse_iso(dates.due_at)
        created_dt = DateHelpers.parse_iso(dates.created_at)
        updated_dt = DateHelpers.parse_iso(dates.updated_at)

        def short_date(dt: Optional[datetime.datetime]) -> str:
            if not dt:
                return "–"
            qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            return locale.toString(qdt.date(), QLocale.ShortFormat)

        def full_tooltip(prefix: str, dt: Optional[datetime.datetime]) -> str:
            return DateHelpers.build_label(prefix, dt, locale)

        due_label = self.lang_manager.translate(TranslationKeys.DUE)
        start_label = self.lang_manager.translate(TranslationKeys.START)
        created_label = self.lang_manager.translate(TranslationKeys.CREATED)
        updated_label = self.lang_manager.translate(TranslationKeys.UPDATED)

        date_options = [
            {"label": due_label, "dt": due_dt, "type": "due"},
            {"label": start_label, "dt": start_dt, "type": "start"},
            {"label": created_label, "dt": created_dt, "type": "created"},
            {"label": updated_label, "dt": updated_dt, "type": "updated"},
        ]

        primary_option = next((opt for opt in date_options if opt["dt"]), None)

        if primary_option:
            primary_dt = primary_option["dt"]
            state = None
            if primary_option["type"] == "due" and primary_dt:
                state = DateHelpers.due_state(primary_dt.date(), today)

            due_container = QFrame(self)
            due_container.setObjectName("DueDateContainer")
            due_layout = QHBoxLayout(due_container)
            due_layout.setContentsMargins(4, 2, 4, 2)
            due_layout.setSpacing(4)

            due_label = QLabel(f"{primary_option['label']}:")
            due_label.setObjectName("DateLabel")
            due_layout.addWidget(due_label)

            due_value = QLabel(short_date(primary_dt))
            due_value.setObjectName("DateValue")
            due_value.setToolTip(full_tooltip(primary_option['label'], primary_dt))

            if state == 'overdue':
                due_value.setProperty("overdue", "true")
            elif state == 'soon':
                due_value.setProperty("due_soon", "true")

            due_layout.addWidget(due_value)
            due_layout.addStretch()

            due_container.setMouseTracking(True)
            due_container.installEventFilter(self)

            main_layout.addWidget(due_container)
        else:
            placeholder_text = self.lang_manager.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_DATES_EMPTY)
            placeholder = QLabel(placeholder_text)
            placeholder.setObjectName("DateLabel")
            placeholder.setStyleSheet("color: rgb(130, 130, 130);")
            main_layout.addWidget(placeholder)


        # Store other dates for hover popup
        self.other_dates = [
            (f"{opt['label']}:", opt["dt"])
            for opt in date_options
            if opt["dt"] and opt is not primary_option
        ]

        self.hover_popup = None
        self._hover_anchor = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        PopupHelpers.bind_hide_timeout_attr_for(
            "dates",
            owner=self,
            attr_name="hover_popup",
            timer=self._hide_timer,
            anchor_getter=lambda: self._hover_anchor,
            event_filter_owner=self,
        )
        self.retheme()


    def eventFilter(self, obj, event):
        PopupHelpers.handle_popup_hover_event(
            obj,
            event,
            popup_widget=self.hover_popup,
            timer=self._hide_timer,
            anchor_matcher=lambda widget: bool(widget) and widget.objectName() == "DueDateContainer",
            on_anchor_enter=self.show_dates_popup,
            delay_ms=PopupHelpers.popup_delay("dates"),
            close_on_deactivate=PopupHelpers.popup_close_on_deactivate("dates"),
            on_popup_deactivate=lambda: PopupHelpers.hide_popup_attr(self, "hover_popup", self._hide_timer, self),
        )
        return super().eventFilter(obj, event)

    def show_dates_popup(self, anchor_widget):
        if not self.other_dates:
            return

        self._hover_anchor = anchor_widget
        self.hover_popup = PopupHelpers.show_popup_for(
            "dates",
            timer=self._hide_timer,
            current_popup=self.hover_popup,
            anchor_widget=anchor_widget,
            popup_factory=lambda: DatesPopupWidget(self.other_dates, self.window()),
            event_filter_owner=self,
        )

    def retheme(self):
        """Reapply theme styles when theme changes."""
        ThemeManager.apply_module_style(self, [QssPaths.DATES])
        # Force style refresh for dynamic properties
        self.style().unpolish(self)
        self.style().polish(self)
        # Also retheme the popup if it's currently shown
        if self.hover_popup and isinstance(self.hover_popup, DatesPopupWidget):
            self.hover_popup.retheme()
