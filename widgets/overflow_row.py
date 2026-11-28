"""One line that shows as much as its width allows, at least the first entry; the rest sits behind a
"+N" mark whose popup lists it. Used for the tags and the contacts of a record card."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QSize, Qt, QTimer
from qgis.PyQt.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..ui.window_state.popup_helpers import PopupHelpers


class OverflowRow(QWidget):
    """A subclass says how wide its first `count` entries are, puts them on the line and fills the popup.

    It sets `gap`, calls `reflow()` when its entries change, and adds `row_style()` to its stylesheet.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.gap = 6
        self._visible = -1  # entries on the line; -1: nothing placed yet
        self._mark = QLabel(self)
        self._mark.setObjectName("OverflowMark")
        self._mark.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mark.hide()
        self._probe = QLabel(self)
        self._probe.setObjectName("OverflowMark")
        self._probe.hide()
        self._popup: Optional[QFrame] = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        PopupHelpers.bind_hide_timeout_attr_for(
            "overflow", owner=self, attr_name="_popup", timer=self._hide_timer,
            anchor_getter=lambda: self._mark, event_filter_owner=self,
        )
        # Last: the filter reads the popup and the timer, and Qt 6 ends the process on an error in it.
        self._mark.installEventFilter(self)

    # ---- what a subclass provides -------------------------------------------------
    def entry_count(self) -> int:
        """How many entries there are to place."""
        raise NotImplementedError

    def uncounted(self) -> int:
        """Entries that exist but cannot be placed (not read from the server); the mark counts them."""
        return 0

    def line_width(self, count: int) -> int:
        """The width of the first `count` entries side by side."""
        raise NotImplementedError

    def line_height(self) -> int:
        raise NotImplementedError

    def place(self, count: int) -> None:
        """Show the first `count` entries from the left edge."""
        raise NotImplementedError

    def popup_widgets(self, count: int, parent: QWidget) -> list[QWidget]:
        """The popup's rows when the line holds the first `count` entries."""
        raise NotImplementedError

    # ---- the line -----------------------------------------------------------------
    def visible_count(self) -> int:
        return max(0, self._visible)

    def hidden_count(self) -> int:
        return self.entry_count() - self.visible_count() + self.uncounted()

    def _mark_width(self, hidden: int) -> int:
        # Measured on a label that is never shown: size hints are asked for at any time and must not
        # change the number the visible mark carries.
        self._probe.setText(f"+{hidden}")
        self._probe.ensurePolished()
        return self._probe.sizeHint().width()

    def _width_with_mark(self, count: int) -> int:
        hidden = self.entry_count() - count + self.uncounted()
        width = self.line_width(count)
        return width + (self.gap + self._mark_width(hidden) if hidden > 0 else 0)

    def fitting_count(self, width: int) -> int:
        """As many entries as fit, but never fewer than one."""
        for count in range(self.entry_count(), 1, -1):
            if self._width_with_mark(count) <= width:
                return count
        return min(1, self.entry_count())

    def reflow(self) -> None:
        """The entries changed: place them again for the current width."""
        self._close_popup()
        self._visible = -1
        self.setFixedHeight(max(1, self.line_height()))
        self._apply_width()
        self.updateGeometry()

    def _apply_width(self) -> None:
        count = self.fitting_count(self.width())
        hidden = self.entry_count() - count + self.uncounted()
        if count != self._visible:
            self._close_popup()
            self._visible = count
            self.place(count)
        if hidden > 0:
            width = self._mark_width(hidden)
            self._mark.setText(f"+{hidden}")
            self._mark.ensurePolished()
            height = min(self.height(), max(20, self._mark.sizeHint().height()))
            self._mark.setGeometry(self.line_width(count) + self.gap, 0, width, height)
            self._mark.show()
            self._mark.raise_()
        else:
            self._mark.hide()

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        return QSize(self._width_with_mark(self.entry_count()), self.line_height())

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._width_with_mark(min(1, self.entry_count())), self.line_height())

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._apply_width()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.reflow()  # fonts and padding are final only once the surrounding styles have applied

    def hideEvent(self, event):  # noqa: N802
        self._close_popup()
        super().hideEvent(event)

    # ---- the popup ----------------------------------------------------------------
    def eventFilter(self, obj, event):  # noqa: N802
        PopupHelpers.handle_popup_hover_event(
            obj, event, popup_widget=self._popup, timer=self._hide_timer,
            anchor_matcher=lambda widget: widget is self._mark,
            on_anchor_enter=lambda _widget: self._show_popup(),
            delay_ms=PopupHelpers.popup_delay("overflow"),
        )
        return super().eventFilter(obj, event)

    def _show_popup(self) -> None:
        if self.hidden_count() <= 0 or PopupHelpers.is_popup_alive(self._popup):
            return
        self._popup = PopupHelpers.show_popup_for(
            "overflow", timer=self._hide_timer, current_popup=self._popup, anchor_widget=self._mark,
            popup_factory=self._build_popup, event_filter_owner=self,
        )

    def _build_popup(self) -> QFrame:
        # A child window: it takes this widget's stylesheet and goes away with the card.
        popup = QFrame(self, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        popup.setObjectName("OverflowPopup")
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        outer = QVBoxLayout(popup)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QFrame(popup)
        frame.setObjectName("OverflowPopupFrame")
        outer.addWidget(frame)
        column = QVBoxLayout(frame)
        column.setContentsMargins(8, 8, 8, 8)
        column.setSpacing(self.gap)
        for widget in self.popup_widgets(self.visible_count(), frame):
            column.addWidget(widget)
            widget.show()
        return popup

    def _close_popup(self) -> None:
        self._popup = PopupHelpers.hide_popup(self._hide_timer, self._popup, self)

    @staticmethod
    def row_style(dark: bool, radius: int) -> list[str]:
        """Rules for the mark and the popup; the subclass adds them to its stylesheet."""
        text = "#d4d4de" if dark else "#24292e"
        muted = "#9aa4b2" if dark else "#6a737d"
        line = "rgba(150,150,160,0.35)" if dark else "rgba(60,80,100,0.18)"
        soft = "rgba(150,150,160,0.12)" if dark else "rgba(60,80,100,0.06)"
        surface = "#252932" if dark else "#ffffff"
        accent = "#1f5d5c" if dark else "#2188ff"
        return [
            f"QLabel#OverflowMark {{ background: {soft}; color: {muted}; font-size: 11px; font-weight: bold;"
            f"padding: 1px 7px; border: 1px solid {line}; border-radius: {min(radius, 9)}px; }}",
            f"QLabel#OverflowMark:hover {{ border-color: {accent}; color: {text}; }}",
            "QFrame#OverflowPopup { background: transparent; border: none; }",
            f"QFrame#OverflowPopupFrame {{ background: {surface}; border: 1px solid {accent}; border-radius: 8px; }}",
        ]
