import html
import hashlib
from functools import lru_cache
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect
)


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
    def __init__(self, fullname: str, size: int = 28, overlap_px: int = 8, first=False, salt: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self.fullname = (fullname or "-").strip()
        self.base_size = size
        self.icon_type = icon

        self.setText(AvatarUtils.initials(self.fullname))
        self.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setBold(True); f.setPointSize(9 if size >= 28 else 8)
        self.setFont(f)
        self.setToolTip(self.fullname)
        self.setFixedSize(size, size)

        bg = AvatarUtils.color_for_name(self.fullname, salt=salt)
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        # Use the provided overlap_px parameter for precise card stacking
        # Note: overlap is now handled by QWidget contents margins in the layout
        overlap_margin = 0  # No CSS margin needed when using QWidget margins

        self.setStyleSheet(
            "QLabel {"
            f" margin:0px;"  # No margins, overlap handled by layout
            f" background-color: {AvatarUtils.rgb_css(bg)};"
            f" color: {fg_hex};"
            f" border: 1.5px solid {AvatarUtils.rgb_css(border)};"
            f" border-radius: {size//2}px;"
            f" font-weight: 700;"  # Bolder font weight
            f" letter-spacing: -0.3px;"  # Slightly less tight spacing
            f" padding: 3px;"  # Increased padding for better letter spacing
            "} "
            "QLabel:hover {"
            f" border-width: 2px;"
            f" border-color: {AvatarUtils.rgb_css(border)};"
            f" z-index: 999;"  # Bring to front on hover
            f" position: relative;"  # Enable z-index
            f" transform: scale(1.08);"  # Enhanced scale effect for card stacking
            "}"
        )

        # Add icon overlay if specified
        if icon:
            self._add_icon_overlay(icon, size, bg)

        # Enhanced shadow effect for card stacking depth
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(16); sh.setXOffset(0); sh.setYOffset(4)
        # Set theme-appropriate shadow color with more depth
        try:
            from ..theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
            shadow_color = QColor(255, 255, 255, 70) if theme == 'dark' else QColor(0, 0, 0, 90)
        except Exception:
            shadow_color = QColor(0, 0, 0, 90)  # default to dark shadow
        sh.setColor(shadow_color)
        self.setGraphicsEffect(sh)

    def enterEvent(self, e):
        # Bring to front with enhanced shadow effect for stacked cards
        self.raise_()
        eff = self.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setBlurRadius(20); eff.setYOffset(6)
        # Add subtle scale animation through stylesheet for card effect
        current_style = self.styleSheet()
        if "transform: scale(1.08)" not in current_style:
            self.setStyleSheet(current_style.replace("}", " transform: scale(1.08); }"))
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Return to normal shadow and remove scale effect
        eff = self.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setBlurRadius(16); eff.setYOffset(4)
        # Remove scale effect
        current_style = self.styleSheet()
        if "transform: scale(1.08);" in current_style:
            self.setStyleSheet(current_style.replace(" transform: scale(1.08);", ""))
        super().leaveEvent(e)

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
            f" font-size: {icon_size-2}px;"
            f" font-weight: bold;"
            f" background: transparent;"
            f" text-shadow: 1px 1px 2px rgba(0,0,0,0.5);"
            f"}}"
        )

        # Store reference to prevent garbage collection
        self.icon_overlay = icon_label


class MembersView(QWidget):
    """Public widget to display responsible and participant members with avatar bubbles."""
    MAX_NAMES_VISIBLE = 6

    def __init__(self, item_data: dict, parent=None, compact: bool = False):
        super().__init__(parent)
        self.setProperty("compact", compact)
        self._build(item_data, compact)

    def _build(self, item_data: dict, compact: bool):
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 if compact else 4)

        members = (item_data.get('members', {}) or {}).get('edges', []) or []

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
            resp_layout.setSpacing(4)  # Small spacing between responsible avatars
            resp_layout.addStretch()  # Left stretch for centering

            resp_size = 32 if not compact else 28  # Match participant avatar size

            for node in responsible_nodes[:3]:  # Limit to 3 responsible members
                full = (node.get('displayName') or "-").strip()
                bubble = AvatarBubble(full, size=resp_size, overlap_px=0, first=True, salt="responsible-v1", icon="star")

                resp_layout.addWidget(bubble)

            resp_layout.addStretch()  # Right stretch for centering
            layout.addLayout(resp_layout)

        # Participants as overlapping avatar bubbles with card stacked effect
        participant_nodes = [
            (m or {}).get('node', {}) or {}
            for m in members
            if not m.get('isResponsible') and ((m.get('node') or {}).get('active', True))
        ]
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)  # No spacing for tight stacking

        first = True
        orig_size = 32 if not compact else 28  # Slightly larger base size
        size = int(orig_size * 0.75)  # Better proportion
        # Calculate overlap for card stacking effect - increased for better coverage
        overlap_px = int(size * 0.8)  # 80% overlap for more pronounced stacking
        text_point_size = 8 if size < 22 else 9

        for node in participant_nodes:
            full = (node.get('displayName') or "-").strip()
            bubble = AvatarBubble(full, size=size, overlap_px=overlap_px, first=first, salt="my-plugin-v1")
            font = bubble.font(); font.setPointSize(text_point_size); bubble.setFont(font)

            # Ensure no extra margins from layout
            if not first:
                # For non-first bubbles, set negative left margin for overlap
                bubble.setContentsMargins(-overlap_px, 0, 0, 0)

            first = False
            row.addWidget(bubble, 0, Qt.AlignVCenter)

        if not participant_nodes:
            row.addWidget(QLabel("-"), 0, Qt.AlignVCenter)

        layout.addLayout(row)

    def retheme(self):
        """Update shadow colors and text colors based on current theme."""
        try:
            from ..theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
        except Exception:
            theme = 'light'

        # Update shadow colors for all avatar bubbles (both responsible and participants)
        shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)

        for bubble in self.findChildren(AvatarBubble):
            if bubble.graphicsEffect():
                bubble.graphicsEffect().setColor(shadow_color)

        # Note: No need to update HTML text colors since responsible members now use AvatarBubble widgets

    # Optional API for later updates
    def set_item(self, item_data: dict, *, compact: Optional[bool] = None):
        if compact is not None:
            self.setProperty("compact", compact)
        # rebuild
        for i in reversed(range(self.layout().count())):
            w = self.layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._build(item_data, bool(self.property("compact")))
