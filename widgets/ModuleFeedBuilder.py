# ================== Imports ==================
import datetime
import html
import hashlib
from typing import Optional, Tuple
from functools import lru_cache

from PyQt5.QtCore import Qt, QLocale, QDateTime
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect
)

# Project imports (adjust paths if needed)
from ..widgets.DateHelpers import DateHelpers           # or: from ..utils.date_helpers import DateHelpers
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..constants.module_icons import ModuleIconPaths, DateIcons, MiscIcons
from .status_color_helper import StatusColorHelper
import os


# ================== Module Feed ==================
class ModuleFeedBuilder:
    @staticmethod
    def create_item_card(item):
        print("[ModuleFeedBuilder] Creating item card for:", item)
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        card.setProperty("compact", False)

        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # Left content
        content = QFrame(); content.setObjectName("CardContent")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(6)

        header_row = QHBoxLayout(); header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(InfocardHeaderFrame(item), alignment=Qt.AlignTop)
        header_row.addStretch(1)
        header_row.addWidget(MembersWidget(item), alignment=Qt.AlignRight | Qt.AlignTop)
        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout(); status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(StatusWidget(item), alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main.addLayout(status_col)

        # Real drop shadow (subtle)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        return card

    @staticmethod
    def add_items_to_feed(module_instance, items):
        """
        Adds item cards to the feed layout of the given module instance.
        Handles all UI updates after adding cards.
        Uses centralized ThemeManager.apply_module_style for card theming.
        """
        for item in items:
            card = ModuleFeedBuilder.create_item_card(item)
            # Centralized theming for card
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            module_instance.feed_layout.addWidget(card)
        # Do not call adjustSize(), show(), or updateGeometry() on feed_content, scroll_area, or widget
        # Let Qt's layout system handle resizing and scrolling


# ================== Elided single-line label ==================
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setToolTip(self._full)
        self.setObjectName("ElidedLabel")

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        super().setText(self._full)
        self._elide()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()

    def _elide(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        super().setText(elided)


# ================== Header (name + number + client) ==================
class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setProperty("compact", compact)

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(8 if not compact else 6)

        # Left column
        left = QFrame(self); left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left); leftL.setContentsMargins(0, 0, 0, 0); leftL.setSpacing(2 if not compact else 1)

        name = item_data.get('name', 'No Name') or 'No Name'
        number = item_data.get('number', '-')
        client = (item_data.get('client') or {}).get('displayName')

        # Name row: elided name + pill badge number
        nameRow = QHBoxLayout(); nameRow.setContentsMargins(0,0,0,0); nameRow.setSpacing(8 if not compact else 6)

        self.nameLabel = ElidedLabel(name)
        self.nameLabel.setObjectName("ProjectNameLabel")
        self.nameLabel.setToolTip(name)
        nameRow.addWidget(self.nameLabel, 1, Qt.AlignVCenter)

        self.numberBadge = QLabel(str(number))
        self.numberBadge.setObjectName("ProjectNumberBadge")
        self.numberBadge.setAlignment(Qt.AlignCenter)
        self.numberBadge.setMinimumWidth(36)
        nameRow.addWidget(self.numberBadge, 0, Qt.AlignVCenter)

        leftL.addLayout(nameRow)

        # Client row (optional)
        if client:
            clientRow = QHBoxLayout(); clientRow.setContentsMargins(0,0,0,0); clientRow.setSpacing(6)
            self.clientIcon = QLabel("👤"); self.clientIcon.setObjectName("ClientIcon"); self.clientIcon.setFixedWidth(14)
            clientRow.addWidget(self.clientIcon, 0, Qt.AlignVCenter)

            self.clientLabel = ElidedLabel(client)
            self.clientLabel.setObjectName("ProjectClientLabel")
            self.clientLabel.setToolTip(client)
            clientRow.addWidget(self.clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)


# ================== Extra info placeholder ==================
class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ExtraInfoWidget(item_data))


class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("<i>Lisaandmed tulevad siia...</i>")
        label.setTextFormat(Qt.RichText)
        layout.addWidget(label)


# ================== Status chip ==================
def apply_chip_shadow(label, theme: Optional[str] = None):
    """Visible but tasteful chip shadow; theme chooses light/dark glow."""
    eff = QGraphicsDropShadowEffect(label)
    eff.setBlurRadius(20)
    eff.setXOffset(0)
    eff.setYOffset(2)
    if (theme or "dark").lower() == "dark":
        eff.setColor(QColor(255, 255, 255, 90))
    else:
        eff.setColor(QColor(0, 0, 0, 120))
    label.setGraphicsEffect(eff)

class StatusWidget(QWidget):
    def __init__(self, item_data, theme=None, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)  # push everything right

        if not item_data.get('isPublic'):
            pub = QLabel()
            pub.setObjectName("ProjectPrivateIcon")
            pub.setToolTip("Privaatne")
            pub.setAlignment(Qt.AlignCenter)
            # themed private icon (using ICON_ADD as requested)
            icon_path = MiscIcons.ICON_IS_PRIVATE
            print(f"[StatusWidget] Using private icon: {icon_path}")
            pm = QPixmap(icon_path)
            if not pm.isNull():
                print("[StatusWidget] Setting private icon pixmap")
                pub.setPixmap(pm.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                print("[StatusWidget] Private icon pixmap is null, using default")
                pub.setText("P")
                
            pub.setFixedSize(16, 16)
            row.addWidget(pub, 0, Qt.AlignRight | Qt.AlignVCenter)

        status = item_data.get('status', {}) or {}
        name = status.get('name', '-') or '-'
        hex_color = status.get('color', 'cccccc')

        bg, fg, border = StatusColorHelper.upgrade_status_color(hex_color)

        self.status_label = QLabel(name)
        self.status_label.setObjectName("ProjectStatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedWidth(128)
        self.status_label.setStyleSheet(
            "QLabel#ProjectStatusLabel {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 0.95);"
            f"color: rgb({fg[0]},{fg[1]},{fg[2]});"
            f"border: 1px solid rgba({border[0]},{border[1]},{border[2]}, 0.85);"
            "border-radius: 10px;"
            "padding: 3px 10px;"
            "font-weight: 500;"
            "font-size: 11px;"
            "}"
            "QLabel#ProjectStatusLabel:hover {"
            f"background-color: rgba({bg[0]},{bg[1]},{bg[2]}, 1.0);"
            "}"
        )
        apply_chip_shadow(self.status_label, theme)

        row.addWidget(self.status_label, 0, Qt.AlignRight | Qt.AlignVCenter)
        main_layout.addLayout(row)
        main_layout.addWidget(DatesWidget(item_data))


# ================== Dates (simple states) ==================
class DatesWidget(QWidget):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setProperty("compact", compact)

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4 if not compact else 2)

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
            if not dt:
                return f"{prefix}: –"
            qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            weekday = locale.dayName(qdt.date().dayOfWeek())
            return f"{prefix}: {dt.strftime('%Y-%m-%d %H:%M:%S')} ({weekday})"

        start_lbl = QLabel(f"Algus: {short_date(start_dt)}")
        start_lbl.setObjectName("DateLine")
        start_lbl.setToolTip(full_tooltip("Algus", start_dt))
        lay.addWidget(start_lbl)

        due_lbl = QLabel(f"Tähtaeg: {short_date(due_dt)}")
        due_lbl.setObjectName("DateDueLine")
        st = "none" if not due_dt else DateHelpers.due_state(due_dt.date(), today)
        due_lbl.setProperty("dueState", st)
        due_lbl.setToolTip(full_tooltip("Tähtaeg", due_dt))
        due_lbl.style().unpolish(due_lbl); due_lbl.style().polish(due_lbl)
        lay.addWidget(due_lbl)

        created_lbl = QLabel(f"Loodud: {short_date(created_dt)}")
        created_lbl.setObjectName("DateMeta")
        created_lbl.setToolTip(full_tooltip("Loodud", created_dt))
        lay.addWidget(created_lbl)

        updated_lbl = QLabel(f"Muudetud: {short_date(updated_dt)}")
        updated_lbl.setObjectName("DateMeta")
        updated_lbl.setToolTip(full_tooltip("Muudetud", updated_dt))
        lay.addWidget(updated_lbl)

        lay.addStretch(1)


# ================== Avatar utils (modular) ==================
class AvatarUtils:
    """Utility methods for name-based avatars (deterministic colors + readable text)."""

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


# ================== Avatar bubble (participants) ==================
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
        sh.setBlurRadius(14); sh.setXOffset(0); sh.setYOffset(2); sh.setColor(QColor(0,0,0,80))
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


# ================== Members (responsible + avatars) ==================
class MembersWidget(QWidget):
    MAX_NAMES_VISIBLE = 6  # show first N responsible, then “+N veel”

    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setProperty("compact", compact)

        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 if compact else 4)

        members = (item_data.get('members', {}) or {}).get('edges', []) or []

        # Responsible (bold; strike if deleted), no label, no split
        responsible_html = []
        plain_tooltip_names = []
        for m in members:
            node = (m or {}).get('node', {}) or {}
            if m.get('isResponsible'):
                # Use non-breaking space to avoid splitting
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
        resp.setWordWrap(False)  # Do not allow split
        resp.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if resp_tip:
            resp.setToolTip(resp_tip)
        layout.addWidget(resp)

        # Participants as overlapping avatar bubbles, no label, only if active
        participant_nodes = [
            (m or {}).get('node', {}) or {}
            for m in members
            if not m.get('isResponsible') and ((m.get('node') or {}).get('active', True))
        ]
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)

        first = True
        # Reduce size by 30%, reduce text size, increase overlap
        orig_size = 28 if not compact else 24
        size = int(orig_size * 0.7)
        orig_overlap = 10 if not compact else 8
        overlap = int(orig_overlap * 1.2)  # more overlap
        text_point_size = 8 if size < 20 else 9

        for node in participant_nodes:
            full = (node.get('displayName') or "-").strip()
            bubble = AvatarBubble(full, size=size, overlap_px=overlap, first=first, salt="my-plugin-v1")
            # Reduce font size for participant bubble
            font = bubble.font()
            font.setPointSize(text_point_size)
            bubble.setFont(font)
            first = False
            row.addWidget(bubble, 0, Qt.AlignVCenter)

        if not participant_nodes:
            row.addWidget(QLabel("-"), 0, Qt.AlignVCenter)

        layout.addLayout(row)
