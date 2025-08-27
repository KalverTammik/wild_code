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
    def __init__(self, fullname: str, size: int = 28, overlap_px: int = 8, first=False, salt: str = "", parent=None):
        super().__init__(parent)
        self.fullname = (fullname or "-").strip()
        self.base_size = size

        self.setText(AvatarUtils.initials(self.fullname))
        self.setAlignment(Qt.AlignCenter)
        f = QFont(); f.setBold(True); f.setPointSize(10 if size >= 28 else 9)
        self.setFont(f)
        self.setToolTip(self.fullname)
        self.setFixedSize(size, size)

        bg = AvatarUtils.color_for_name(self.fullname, salt=salt)
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        ml = 0 if first else -overlap_px
        self.setStyleSheet(
            "QLabel {"
            f" margin-left:{ml}px;"
            f" background-color: {AvatarUtils.rgb_css(bg)};"
            f" color: {fg_hex};"
            f" border: 1px solid {AvatarUtils.rgb_css(border)};"
            f" border-radius: {size//2}px;"
            "}"
            "QLabel:hover { border-width: 2px; }"
        )

        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(14); sh.setXOffset(0); sh.setYOffset(2)
        # Set theme-appropriate shadow color
        try:
            from ..theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
            shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)
        except Exception:
            shadow_color = QColor(0, 0, 0, 120)  # default to dark shadow
        sh.setColor(shadow_color)
        self.setGraphicsEffect(sh)

    def enterEvent(self, e):
        self.setFixedSize(self.base_size + 6, self.base_size + 6)
        self.raise_()
        eff = self.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setBlurRadius(18); eff.setYOffset(3)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setFixedSize(self.base_size, self.base_size)
        eff = self.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setBlurRadius(14); eff.setYOffset(2)
        super().leaveEvent(e)


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

        # Responsible (bold; strike if deleted)
        responsible_html = []
        plain_tooltip_names = []
        for m in members:
            node = (m or {}).get('node', {}) or {}
            if m.get('isResponsible'):
                name = html.escape((node.get('displayName') or "-").strip()).replace(" ", "\u00A0")
                plain_tooltip_names.append(name)
                if node.get('deletedAt'):
                    responsible_html.append(f"<span style='text-decoration:line-through;color:#9aa0a6;'>{name}</span>")
                else:
                    responsible_html.append(f"<span style='font-weight:600;'>{name}</span>")

        def collapse(html_list):
            if not html_list:
                return "-", None
            if len(html_list) <= self.MAX_NAMES_VISIBLE:
                return ", ".join(html_list), ", ".join(plain_tooltip_names)
            shown = ", ".join(html_list[: self.MAX_NAMES_VISIBLE])
            more = len(html_list) - self.MAX_NAMES_VISIBLE
            return f"{shown} <span style='opacity:.8'>(+{more} veel)</span>", ", ".join(plain_tooltip_names)

        resp_short, resp_tip = collapse(responsible_html)
        resp = QLabel(f"{resp_short}")
        resp.setTextFormat(Qt.RichText)
        resp.setObjectName("ProjectResponsibleLabel")
        resp.setWordWrap(False)
        resp.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if resp_tip:
            resp.setToolTip(resp_tip)
        layout.addWidget(resp)

        # Participants as overlapping avatar bubbles
        participant_nodes = [
            (m or {}).get('node', {}) or {}
            for m in members
            if not m.get('isResponsible') and ((m.get('node') or {}).get('active', True))
        ]
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)

        first = True
        orig_size = 28 if not compact else 24
        size = int(orig_size * 0.7)
        orig_overlap = 10 if not compact else 8
        overlap = int(orig_overlap * 1.2)
        text_point_size = 8 if size < 20 else 9

        for node in participant_nodes:
            full = (node.get('displayName') or "-").strip()
            bubble = AvatarBubble(full, size=size, overlap_px=overlap, first=first, salt="my-plugin-v1")
            font = bubble.font(); font.setPointSize(text_point_size); bubble.setFont(font)
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

        # Update shadow colors for all avatar bubbles
        shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)

        for bubble in self.findChildren(AvatarBubble):
            if bubble.graphicsEffect():
                bubble.graphicsEffect().setColor(shadow_color)

        # Update deleted member text color
        deleted_color = "#B0B0B0" if theme == 'dark' else "#9aa0a6"
        for label in self.findChildren(QLabel, "ProjectResponsibleLabel"):
            # Re-apply the HTML with updated color
            current_text = label.text()
            if "<span style='text-decoration:line-through;" in current_text:
                # Replace the old color with new color
                import re
                updated_text = re.sub(r'color:#[0-9a-fA-F]{6}', f'color:{deleted_color}', current_text)
                label.setText(updated_text)

    # Optional API for later updates
    def set_item(self, item_data: dict, *, compact: Optional[bool] = None):
        if compact is not None:
            self.setProperty("compact", compact)
        # rebuild
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            if w:
                w.setParent(None)
        self._build(item_data, bool(self.property("compact")))
