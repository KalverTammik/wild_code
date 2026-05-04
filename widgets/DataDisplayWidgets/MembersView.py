import hashlib
from functools import lru_cache
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
)
from ..theme_manager import ThemeManager, IntensityLevels, styleExtras, ThemeShadowColors
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.responses import DataDisplayExtractors
from ...ui.window_state.popup_helpers import PopupHelpers


class AvatarUtils:
    """Helper functions for deterministic colors and text for avatars."""

    @staticmethod
    def initials(fullname: str) -> str:
        parts = [p for p in (fullname or "").strip().split() if p]
        if not parts:
            return "–"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @staticmethod
    @lru_cache(maxsize=2048)
    def color_for_name(fullname: str, *, salt: str = "", s: float = 0.55, l: float = 0.52) -> QColor:
        key = (fullname or "") + "|" + (salt or "")
        h = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % 360
        c = (1 - abs(2*l - 1)) * s
        x = c * (1 - abs(((h/60) % 2) - 1))
        m = l - c/2
        idx = int(h // 60) % 6
        rp, gp, bp = ((c,x,0), (x,c,0), (0,c,x), (0,x,c), (x,0,c), (c,0,x))[idx]
        r, g, b = int((rp+m)*255), int((gp+m)*255), int((bp+m)*255)
        return QColor(r, g, b)

    @staticmethod
    def fg_for_bg(bg: QColor) -> str:
        def lin(c):
            c = c/255.0
            return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055) ** 2.4
        L = 0.2126*lin(bg.red()) + 0.7152*lin(bg.green()) + 0.0722*lin(bg.blue())
        return "#000000" if L > 0.6 else "#ffffff"

    @staticmethod
    def border_for_bg(bg: QColor, delta: int = 28) -> QColor:
        return QColor(max(0, bg.red()-delta), max(0, bg.green()-delta), max(0, bg.blue()-delta))

    @staticmethod
    def rgb_css(c: QColor, alpha: float = 1.0) -> str:
        r,g,b = c.red(), c.green(), c.blue()
        if alpha >= 1:
            return f"rgb({r},{g},{b})"
        a = max(0.0, min(1.0, alpha))
        return f"rgba({r},{g},{b},{a})"


class AvatarBubble(QLabel):
    MAX_POPUP_PARTICIPANTS = 11

    def __init__(self, fullname: str, salt: str = "", popup_members=None, parent=None):
        super().__init__(parent)
        self.fullname = (fullname or "-").strip()
        self.base_size = 26
        # Optional list of member nodes to display on hover (for responsible avatars)
        self._popup_members = popup_members or []
        self._members_popup = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self.installEventFilter(self)
        PopupHelpers.bind_hide_timeout_attr_for(
            "members",
            owner=self,
            attr_name="_members_popup",
            timer=self._hide_timer,
            anchor_getter=self,
            event_filter_owner=self,
        )

        self.setText(AvatarUtils.initials(self.fullname))
        self.setAlignment(Qt.AlignCenter)
        
        # Only set tooltip for non-assignee avatars to avoid duplicate info
        if not popup_members:
            self.setToolTip(self.fullname)
        self.setFixedSize(self.base_size, self.base_size)

        bg = AvatarUtils.color_for_name(self.fullname, salt=salt)
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        self.setStyleSheet(
            "QLabel {"
            f" margin:0px;"  # No margins, overlap handled by layout
            f" background-color: {AvatarUtils.rgb_css(bg, alpha=0.6)};"  # Semi-transparent background
            f" color: {fg_hex};"
            f" border: 1px solid {AvatarUtils.rgb_css(border,alpha=0.8)};"
            f" border-radius: {self.base_size//2}px;"
            f" font-size: 10px;"  # Override theme font-size
            f" font-weight: 700;"  # Bolder font weight
            f" letter-spacing: -0.3px;"  # Slightly less tight spacing
            f" padding: 3px;"  # Responsive padding (increased slightly)
            "} "
            "QLabel:hover {"
            f" opacity: 0.1;"  # Subtle opacity change instead of scale
            "}"
        )

        # Add subtle drop shadow effect
        styleExtras.apply_chip_shadow(
            element=self,
            color=ThemeShadowColors.GRAY,
            blur_radius=self.base_size//2,
            x_offset=1,
            y_offset=2,
            alpha_level=IntensityLevels.EXTRA_HIGH
        )


    def eventFilter(self, obj, event):
        PopupHelpers.handle_popup_hover_event(
            obj,
            event,
            popup_widget=self._members_popup,
            timer=self._hide_timer,
            anchor_matcher=lambda widget: widget is self,
            on_anchor_enter=lambda _widget: self._show_members_popup(),
            delay_ms=PopupHelpers.popup_delay("members"),
            close_on_deactivate=PopupHelpers.popup_close_on_deactivate("members"),
            on_popup_deactivate=lambda: PopupHelpers.hide_popup_attr(self, "_members_popup", self._hide_timer, self),
        )
        return super().eventFilter(obj, event)

    def _show_members_popup(self):
        """Create and show a tooltip-like popup with member names in a vertical list."""
        try:
            if not self._popup_members:
                return
            # If popup already exists, keep it shown
            if self._members_popup and self._members_popup.isVisible():
                return


            popup = QFrame(None, Qt.ToolTip)
            popup.setObjectName('PopupFrame')
            popup.setProperty("popupKind", "members")
            popup.setWindowFlags(Qt.ToolTip)
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(4)

            # Apply theme-based styling to the popup
            PopupHelpers.apply_popup_style(popup, "members")

            # Create labels for each member name
            # First, add the responsible person (bold and distinguished)
            responsible_label = QLabel(f"★ {self.fullname}", popup)
            responsible_label.setObjectName("Value")
            layout.addWidget(responsible_label)

            # Then add participant members
            for node in self._popup_members[:self.MAX_POPUP_PARTICIPANTS]:  # Limit to 11 since responsible takes one spot
                full = DataDisplayExtractors.extract_member_display_name(node)
                label = QLabel(f"  {full}", popup)  # Indent with spaces for visual hierarchy
                label.setObjectName("Label")
                layout.addWidget(label)

            # Position popup near this avatar (below)
            self._members_popup = PopupHelpers.show_popup_for(
                "members",
                timer=self._hide_timer,
                current_popup=self._members_popup,
                anchor_widget=self,
                popup_factory=lambda: popup,
                event_filter_owner=self,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="members_popup_create_failed",
            )

class MembersView(QWidget):
    """Public widget to display responsible and participant members with avatar bubbles."""

    AVATAR_SIZE = 26
    AVATAR_SPACING = 2
    SIDE_PADDING = 10

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self._build(item_data)

    def _build(self, item_data: dict):
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        responsible_nodes, participant_nodes = DataDisplayExtractors.extract_members(item_data)

        if responsible_nodes:
            # Create horizontal layout for responsible avatars
            resp_layout = QHBoxLayout()
            resp_layout.setContentsMargins(0, 0, 0, 0)
            resp_layout.setSpacing(self.AVATAR_SPACING)
            resp_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)

            avatar_count = min(len(responsible_nodes), 3)

            for node in responsible_nodes[:3]:  # Limit to 3 responsible members
                full = DataDisplayExtractors.extract_member_display_name(node)
                # Attach participant nodes as popup members when hovering this responsible avatar
                bubble = AvatarBubble(full, salt="responsible-v1", popup_members=participant_nodes)
                resp_layout.addWidget(bubble)

            layout.addLayout(resp_layout)
            content_width = (
                avatar_count * self.AVATAR_SIZE
                + max(0, avatar_count - 1) * self.AVATAR_SPACING
                + self.SIDE_PADDING
            )
            self.setFixedWidth(content_width)

    # Participants are now shown only on hover of responsible avatars (popup_members passed above).

    def retheme(self):
        return None
