from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...python.responses import DataDisplayExtractors
from ...ui.window_state.popup_helpers import PopupHelpers
from ...utils.status_color_helper import StatusColorHelper
from ...widgets.theme_manager import ThemeManager, Theme, is_dark, styleExtras, ThemeShadowColors, IntensityLevels
try:
    from .StatusWidget import StatusWidget
except Exception:  # pragma: no cover - preview sandbox may not have full runtime deps
    StatusWidget = None


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

    def __init__(self, item_data, module_name: Optional[str] = None, parent: Optional[QWidget] = None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("MainStatusWidget")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(self.RAIL_WIDTH)
        self._module_name = str(module_name or "").strip().lower()
        self.hover_popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)

        status_info = DataDisplayExtractors.extract_status(item_data)
        self._status_name = str(status_info.name or "-").strip() or "-"
        bg, _fg, border = StatusColorHelper.upgrade_status_color(str(status_info.color or "cccccc"))
        self._status_delegate = None
        if StatusWidget is not None:
            self._status_delegate = StatusWidget(
                item_data,
                module_name=self._module_name,
                parent=self,
                lang_manager=lang_manager,
            )
            self._status_delegate.hide()

        theme_name = ThemeManager.effective_theme()
        dark_theme = is_dark(theme_name) if theme_name in (Theme.DARK, Theme.LIGHT, Theme.SYSTEM) else False
        shell_fill = "rgba(255,255,255,0.82)" if not dark_theme else "rgba(255,255,255,0.08)"
        shell_border = "rgba(25,35,45,0.12)" if not dark_theme else "rgba(255,255,255,0.10)"
        glow_alpha = 0.26 if not dark_theme else 0.32
        core_alpha = 0.56 if not dark_theme else 0.62
        shell_radius = max(2, min(10, self.RAIL_WIDTH))
        core_radius = max(2, min(8, self.RAIL_WIDTH - 1))
        glow_radius = max(1, min(6, self.RAIL_WIDTH - 2))
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
        self.rail_frame.setStyleSheet(
            f"background-color: {shell_fill};"
            f"border: 1px solid {shell_border};"
            f"border-right: 1px solid rgba({bg[0]},{bg[1]},{bg[2]}, 0.96);"
        )
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
        self.core_fill.setStyleSheet(
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, {core_alpha});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.30);"
        )
        core_layout = QVBoxLayout(self.core_fill)
        core_layout.setContentsMargins(0, self.CORE_TOP_BOTTOM_RIGHT_GAP, self.CORE_TOP_BOTTOM_RIGHT_GAP, self.CORE_TOP_BOTTOM_RIGHT_GAP)
        core_layout.setSpacing(0)

        self.inner_glow = QFrame(self.core_fill)
        self.inner_glow.setObjectName("MainStatusGlow")
        self.inner_glow.setMinimumWidth(inner_glow_width)
        self.inner_glow.setStyleSheet(
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, {glow_alpha});"
        )
        core_layout.addWidget(self.inner_glow, 1)

        rail_layout.addWidget(self.core_fill, 1)

        root.addWidget(self.rail_frame, 0, Qt.AlignLeft)

        PopupHelpers.bind_hide_timeout_attr_for(
            None,
            owner=self,
            attr_name="hover_popup",
            timer=self._hide_timer,
            anchor_getter=lambda: self.rail_frame,
            event_filter_owner=self,
        )

        if self._status_delegate is not None and self._status_delegate._can_edit_status():
            self.setCursor(Qt.PointingHandCursor)
            self.rail_frame.setCursor(Qt.PointingHandCursor)

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
        self._reposition_status_popup(global_pos)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if (
            event.button() == Qt.LeftButton
            and self._status_delegate is not None
            and self._status_delegate._can_edit_status()
        ):
            self._status_delegate._show_status_menu(anchor_widget=self.rail_frame)
            event.accept()
            return
        super().mousePressEvent(event)