from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...python.responses import DataDisplayExtractors
from ...ui.window_state.popup_helpers import PopupHelpers
from ...utils.status_color_helper import StatusColorHelper
from ...ui.theme_manager import ThemeManager, Theme, is_dark, styleExtras, ThemeShadowColors, IntensityLevels
from .status_change_controller import StatusChangeController


class StatusPopupWidget(QWidget):
    def __init__(self, status_name: str, parent=None):
        super().__init__(parent, flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("StatusPopup")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        frame = QFrame(self)
        frame.setObjectName("PopupFrame")
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(6, 4, 6, 4)
        frame_layout.setSpacing(0)

        label = QLabel(status_name, frame)
        label.setObjectName("Value")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        frame_layout.addWidget(label)

        layout.addWidget(frame)
        PopupHelpers.apply_popup_style(self)


class MainStatusWidget(QWidget):
    RAIL_WIDTH = 8
    SHELL_TOP_BOTTOM_RIGHT_GAP = 1
    CORE_TOP_BOTTOM_RIGHT_GAP = 1
    HOVER_POPUP_OFFSET = QPoint(4, 9)

    def __init__(self, item_data, module_name: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("MainStatusWidget")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(self.RAIL_WIDTH)
        self._module_name = str(module_name or "").strip().lower()
        self.hover_popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        # The hover popup is a window of its own. When the card is replaced after a status change this rail
        # is deleted, and with it the timer that would hide the popup, so the popup is closed here.
        popup_holder = {"popup": None}
        self._hover_popup_holder = popup_holder
        self.destroyed.connect(lambda _obj=None, holder=popup_holder: PopupHelpers.close_popup_widget(holder["popup"]))

        status_info = DataDisplayExtractors.extract_status(item_data)
        self._status_name = str(status_info.name or "-").strip() or "-"
        self._busy = False
        self._status_color = str(status_info.color or "cccccc")
        self._status_changes = StatusChangeController(self, item_data, self._module_name)
        self._status_changes.busy_changed.connect(self._set_busy)
        self._status_changes.status_changed.connect(self.apply_status)

        theme_name = ThemeManager.effective_theme()
        dark_theme = is_dark(theme_name) if theme_name in (Theme.DARK, Theme.LIGHT, Theme.SYSTEM) else False
        self._shell_fill = "rgba(255,255,255,0.82)" if not dark_theme else "rgba(255,255,255,0.08)"
        self._shell_border = "rgba(25,35,45,0.12)" if not dark_theme else "rgba(255,255,255,0.10)"
        self._glow_alpha = 0.26 if not dark_theme else 0.32
        self._core_alpha = 0.56 if not dark_theme else 0.62
        inner_glow_width = max(1, self.RAIL_WIDTH - 2)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.rail_frame = QFrame(self)
        self.rail_frame.setObjectName("MainStatusRail")
        self.rail_frame.setFixedWidth(self.RAIL_WIDTH)
        self.rail_frame.setMinimumHeight(0)
        self.rail_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.rail_frame.setToolTip("")
        self.rail_frame.setMouseTracking(True)
        self.rail_frame.installEventFilter(self)
        styleExtras.apply_chip_shadow(
            self.rail_frame,
            color=ThemeShadowColors.GRAY,
            blur_radius=10,
            x_offset=0,
            y_offset=1,
            alpha_level=IntensityLevels.LOW,
        )

        rail_layout = QVBoxLayout(self.rail_frame)
        rail_layout.setContentsMargins(0, self.SHELL_TOP_BOTTOM_RIGHT_GAP, self.SHELL_TOP_BOTTOM_RIGHT_GAP, self.SHELL_TOP_BOTTOM_RIGHT_GAP)
        rail_layout.setSpacing(0)

        self.core_fill = QFrame(self.rail_frame)
        self.core_fill.setObjectName("MainStatusCore")
        core_layout = QVBoxLayout(self.core_fill)
        core_layout.setContentsMargins(0, self.CORE_TOP_BOTTOM_RIGHT_GAP, self.CORE_TOP_BOTTOM_RIGHT_GAP, self.CORE_TOP_BOTTOM_RIGHT_GAP)
        core_layout.setSpacing(0)

        self.inner_glow = QFrame(self.core_fill)
        self.inner_glow.setObjectName("MainStatusGlow")
        self.inner_glow.setMinimumWidth(inner_glow_width)
        core_layout.addWidget(self.inner_glow, 1)

        rail_layout.addWidget(self.core_fill, 1)

        root.addWidget(self.rail_frame, 0, Qt.AlignLeft)
        self._apply_status_colors(str(status_info.color or "cccccc"))

        PopupHelpers.bind_hide_timeout_attr_for(
            None,
            owner=self,
            attr_name="hover_popup",
            timer=self._hide_timer,
            anchor_getter=lambda: self.rail_frame,
            event_filter_owner=self,
        )

        self._idle_cursor = Qt.PointingHandCursor if self._status_changes.can_edit_status() else None
        self._show_idle_cursor()

    def apply_status(self, item_data) -> None:
        """Show a status the item got after its card was built, without building the card again."""
        status_info = DataDisplayExtractors.extract_status(item_data)
        self._status_name = str(status_info.name or "-").strip() or "-"
        self._apply_status_colors(str(status_info.color or "cccccc"))
        self._status_changes.set_item_data(item_data)

    def _show_idle_cursor(self) -> None:
        for widget in (self, self.rail_frame):
            if self._idle_cursor is None:
                widget.unsetCursor()
            else:
                widget.setCursor(self._idle_cursor)

    def _set_busy(self, busy: bool) -> None:
        """The rail fades and shows a busy cursor while a status list or a status change is loading."""
        self._busy = bool(busy)
        for widget in (self, self.rail_frame):
            if self._busy:
                widget.setCursor(Qt.BusyCursor)
        if not self._busy:
            self._show_idle_cursor()
        self._apply_status_colors(self._status_color)

    def _apply_status_colors(self, status_color: str) -> None:
        self._status_color = status_color
        fade = 0.35 if self._busy else 1.0
        bg, _fg, border = StatusColorHelper.upgrade_status_color(status_color)
        self.rail_frame.setStyleSheet(
            f"background-color: {self._shell_fill};"
            f"border: 1px solid {self._shell_border};"
            f"border-right: 1px solid rgba({bg[0]},{bg[1]},{bg[2]}, 0.96);"
        )
        self.core_fill.setStyleSheet(
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, {self._core_alpha * fade});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.30);"
        )
        self.inner_glow.setStyleSheet(
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, {self._glow_alpha * fade});"
        )

    def eventFilter(self, obj, event):  # noqa: N802 - Qt override
        event_type = event.type()

        if obj is self.rail_frame:
            if event_type == QEvent.Enter:
                self.show_status_popup(event.globalPos())
            elif event_type == QEvent.MouseMove:
                self._reposition_status_popup(event.globalPos())

        PopupHelpers.handle_popup_hover_event(
            obj,
            event,
            popup_widget=self.hover_popup,
            timer=self._hide_timer,
            anchor_matcher=lambda widget: widget is self.rail_frame,
            on_anchor_enter=None,
            delay_ms=PopupHelpers.popup_delay(None),
            close_on_deactivate=PopupHelpers.popup_close_on_deactivate(None),
            on_popup_deactivate=lambda: PopupHelpers.hide_popup_attr(self, "hover_popup", self._hide_timer, self),
        )
        return super().eventFilter(obj, event)

    def _reposition_status_popup(self, global_pos) -> None:
        if self.hover_popup is None or global_pos is None:
            return

        PopupHelpers.position_popup_at_global(
            self.hover_popup,
            global_pos,
            offset=self.HOVER_POPUP_OFFSET,
        )

    def close_hover_popup(self) -> None:
        PopupHelpers.hide_popup_attr(self, "hover_popup", self._hide_timer, self)
        self._hover_popup_holder["popup"] = None

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt override
        self.close_hover_popup()
        super().hideEvent(event)

    def show_status_popup(self, global_pos=None) -> None:
        if not self._status_name:
            return

        self.hover_popup = PopupHelpers.show_popup_for(
            None,
            timer=self._hide_timer,
            current_popup=self.hover_popup,
            anchor_widget=self.rail_frame,
            popup_factory=lambda: StatusPopupWidget(self._status_name, self.window()),
            event_filter_owner=self,
        )
        self._hover_popup_holder["popup"] = self.hover_popup
        self._reposition_status_popup(global_pos)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if (
            event.button() == Qt.LeftButton
            and self._status_changes.can_edit_status()
        ):
            self.close_hover_popup()  # the menu replaces the name tooltip
            self._status_changes.show_status_menu(anchor_widget=self.rail_frame)
            event.accept()
            return
        super().mousePressEvent(event)
