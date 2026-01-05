import hashlib
from functools import lru_cache
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from ..theme_manager import ThemeManager, IntensityLevels, styleExtras, ThemeShadowColors
from ...constants.file_paths import QssPaths


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
    def __init__(self, fullname: str,  overlap_px: int = 8, first=False, salt: str = "", icon: str = "", popup_members=None, parent=None):
        super().__init__(parent)
        self.fullname = (fullname or "-").strip()
        self.base_size = 26
        self.icon_type = icon
        # Optional list of member nodes to display on hover (for responsible avatars)
        self._popup_members = popup_members or []
        self._members_popup = None

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

        # Add icon overlay if specified (responsible avatars won't pass icon anymore)
        if icon:
            self._add_icon_overlay(icon, self.base_size, bg)


    def enterEvent(self, e):
        # Simple hover behavior - just show popup for members
        super().enterEvent(e)
        # Show members popup if present (responsible avatar hover behavior)
        try:
            if self._popup_members:
                self._show_members_popup()
        except Exception:
            pass

    def leaveEvent(self, e):
        # Simple leave behavior - just hide popup
        super().leaveEvent(e)
        # Hide popup when leaving avatar
        try:
            if self._members_popup:
                self._hide_members_popup()
        except Exception:
            pass

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
            popup.setWindowFlags(Qt.ToolTip)
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(4)

            # Apply theme-based styling to the popup
            
            ThemeManager.apply_module_style(popup, [QssPaths.POPUP])

            # Create labels for each member name
            # First, add the responsible person (bold and distinguished)
            responsible_label = QLabel(f"★ {self.fullname}", popup)
            responsible_label.setStyleSheet(" font-size: 11px; font-weight: bold; padding: 2px 0px;")
            layout.addWidget(responsible_label)

            # Then add participant members
            for node in self._popup_members[:11]:  # Limit to 11 since responsible takes one spot
                full = (node.get('displayName') or "-").strip() if isinstance(node, dict) else str(node)
                label = QLabel(f"  {full}", popup)  # Indent with spaces for visual hierarchy
                label.setStyleSheet("font-size: 11px; padding: 2px 0px;")
                layout.addWidget(label)

            # Position popup near this avatar (below)
            gp = self.mapToGlobal(self.rect().bottomLeft())
            popup.move(gp.x(), gp.y() + 6)
            popup.show()
            self._members_popup = popup
        except Exception:
            pass

    def _hide_members_popup(self):
        try:
            if self._members_popup:
                try:
                    self._members_popup.hide()
                    self._members_popup.deleteLater()
                except Exception:
                    pass
                self._members_popup = None
        except Exception:
            pass

    def _add_icon_overlay(self, icon_type: str, size: int, bg_color: QColor):
        """Add an icon overlay to the avatar bubble."""
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtGui import QFont

        # Create icon label
        icon_label = QLabel("★", self)  # Star icon placeholder
        icon_label.setAlignment(Qt.AlignCenter)

        # Calculate icon size (about 40% of avatar size)
        icon_size = max(10, int(size * 0.4))
        icon_label.setFixedSize(icon_size, icon_size)

        # Position at bottom right corner
        icon_x = size - icon_size - 2  # 2px padding from edge
        icon_y = size - icon_size - 2
        icon_label.move(icon_x, icon_y)

        # Style the icon
        fg_color = AvatarUtils.fg_for_bg(bg_color)
        icon_label.setStyleSheet(
            f"QLabel {{"
            f" color: {fg_color};"
            f" font-size: {icon_size-6}px;"
            f" font-weight: bold;"
            f" background: transparent;"
            f"}}"
        )

        # Store reference to prevent garbage collection
        self.icon_overlay = icon_label

class MembersView(QWidget):
    """Public widget to display responsible and participant members with avatar bubbles."""
    MAX_NAMES_VISIBLE = 6

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.avatar_size = 26
        self._build(item_data)

    def _build(self, item_data: dict):
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        members = (item_data.get('members', {}) or {}).get('edges', []) or []
        # Participants extracted for potential popup display
        participant_nodes = [
            (m or {}).get('node', {}) or {}
            for m in members
            if not m.get('isResponsible') and ((m.get('node') or {}).get('active', True))
        ]

        # Responsible members as avatar bubbles (centered at top)
        responsible_nodes = [
            (m or {}).get('node', {}) or {}
            for m in members
            if m.get('isResponsible') and ((m.get('node') or {}).get('active', True))
        ]

        if responsible_nodes:
            # Create horizontal layout for responsible avatars
            resp_layout = QHBoxLayout()
            resp_layout.setContentsMargins(0, 0, 0, 0)
            resp_layout.addStretch()  # Left stretch for centering


            for node in responsible_nodes[:3]:  # Limit to 3 responsible members
                full = (node.get('displayName') or "-").strip()
                # Attach participant nodes as popup members when hovering this responsible avatar
                bubble = AvatarBubble(full,  overlap_px=0, first=True, salt="responsible-v1", icon="", popup_members=participant_nodes)
                # Do not add icon overlay badge for responsible
                resp_layout.addWidget(bubble)

            resp_layout.addStretch()  # Right stretch for centering
            layout.addLayout(resp_layout)

    # Participants are now shown only on hover of responsible avatars (popup_members passed above).

    def retheme(self):

        ThemeManager.apply_module_style(self)
