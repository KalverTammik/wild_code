import hashlib
from functools import lru_cache
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
)
from ..theme_manager import ThemeManager, IntensityLevels, styleExtras, ThemeShadowColors
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.responses import DataDisplayExtractors
from ...ui.window_state.popup_helpers import PopupHelpers
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


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


class _MembersClickPopup(QFrame):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)


class AvatarBubble(QLabel):
    MAX_POPUP_PARTICIPANTS = 11

    def __init__(self, fullname: str, salt: str = "", popup_members=None, parent=None,
                 *, unassigned=False, responsible_members=None, lang_manager=None):
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self.setObjectName("MemberAvatarBubble")
        self._unassigned = unassigned
        self._responsible_members = list(responsible_members or [])
        self._click_popup = None
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
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        label = self._lang.translate(TranslationKeys.CARD_RESPONSIBLE_UNASSIGNED) if unassigned else self.fullname
        action = self._lang.translate(TranslationKeys.CARD_MEMBERS_OPEN)
        self.setAccessibleName(f"{label}. {action}")
        if unassigned:
            self.setText("")
            self.setToolTip(f"{label}\n{action}")
        self.setAlignment(Qt.AlignCenter)
        
        # Only set tooltip for non-assignee avatars to avoid duplicate info
        if not popup_members and not unassigned:
            self.setToolTip(self.fullname)
        self.setFixedSize(self.base_size, self.base_size)

        bg = QColor("#9ca3af") if unassigned else AvatarUtils.color_for_name(self.fullname, salt=salt)
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        self.setStyleSheet(
            "QLabel#MemberAvatarBubble {"
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
            "QLabel#MemberAvatarBubble:hover {"
            f" opacity: 0.1;"  # Subtle opacity change instead of scale
            "}"
            "QLabel#MemberAvatarBubble:focus { border: 2px solid #0078d4; }"
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
        if self._click_popup is not None and self._click_popup.isVisible():
            return super().eventFilter(obj, event)
        PopupHelpers.handle_popup_hover_event(
            obj,
            event,
            popup_widget=self._members_popup,
            timer=self._hide_timer,
            anchor_matcher=lambda widget: widget is self,
            on_anchor_enter=lambda _widget: None if self._unassigned else self._show_members_popup(),
            delay_ms=PopupHelpers.popup_delay("members"),
            close_on_deactivate=PopupHelpers.popup_close_on_deactivate("members"),
            on_popup_deactivate=lambda: PopupHelpers.hide_popup_attr(self, "_members_popup", self._hide_timer, self),
        )
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._unassigned:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(self.palette().text().color(), 1.3))
            painter.drawEllipse(9, 5, 8, 8)
            painter.drawArc(5, 14, 16, 12, 0, 180 * 16)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._open_members_list()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._open_members_list()
            event.accept()
            return
        super().keyPressEvent(event)

    def _open_members_list(self):
        if self._click_popup is not None and self._click_popup.isVisible():
            self._click_popup.hide()
            return
        PopupHelpers.hide_popup_attr(self, "_members_popup", self._hide_timer, self)
        if self._click_popup is None:
            popup = _MembersClickPopup(self, Qt.Popup)
            popup.setObjectName("PopupFrame")
            popup.setProperty("popupKind", "members")
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(8, 8, 8, 8)
            body = QWidget(popup)
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(0, 0, 0, 0)
            body_layout.setSpacing(6)
            names = []
            if self._unassigned:
                names.append((self._lang.translate(TranslationKeys.CARD_RESPONSIBLE_UNASSIGNED), "Value"))
            for node in self._responsible_members:
                names.append((f"★ {DataDisplayExtractors.extract_member_display_name(node)}", "Value"))
            for node in self._popup_members:
                names.append((DataDisplayExtractors.extract_member_display_name(node), "Label"))
            if not self._responsible_members and not self._popup_members:
                names.append((self._lang.translate(TranslationKeys.CARD_MEMBERS_EMPTY), "Label"))
            for text, role in names:
                label = QLabel(text, body)
                label.setTextFormat(Qt.PlainText)
                label.setObjectName(role)
                label.setWordWrap(True)
                body_layout.addWidget(label)
            scroll = QScrollArea(popup)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(body)
            scroll.setFixedSize(250, min(280, max(45, body.sizeHint().height() + 8)))
            layout.addWidget(scroll)
            self._click_popup = popup
        PopupHelpers.apply_popup_style(self._click_popup, "members")
        self._click_popup.show()
        PopupHelpers.position_popup(self._click_popup, self)
        self._click_popup.setFocus()

    def _show_members_popup(self):
        """Create and show a tooltip-like popup with member names in a vertical list."""
        try:
            if not self._popup_members:
                return
            # If popup already exists, keep it shown
            if self._members_popup and self._members_popup.isVisible():
                return


            popup = QFrame(self, Qt.ToolTip)
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

    def __init__(self, item_data: dict, parent=None, lang_manager=None):
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
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
                bubble = AvatarBubble(full, salt="responsible-v1", popup_members=participant_nodes,
                                      responsible_members=responsible_nodes, lang_manager=self._lang)
                resp_layout.addWidget(bubble)

            layout.addLayout(resp_layout)
            content_width = (
                avatar_count * self.AVATAR_SIZE
                + max(0, avatar_count - 1) * self.AVATAR_SPACING
                + self.SIDE_PADDING
            )
            self.setFixedWidth(content_width)
        else:
            bubble = AvatarBubble("", popup_members=participant_nodes, unassigned=True,
                                  lang_manager=self._lang, parent=self)
            layout.addWidget(bubble, 0, Qt.AlignRight | Qt.AlignTop)
            self.setFixedWidth(self.AVATAR_SIZE + self.SIDE_PADDING)

    def retheme(self):
        for bubble in self.findChildren(AvatarBubble):
            for popup in (bubble._click_popup, bubble._members_popup):
                if popup is not None:
                    PopupHelpers.apply_popup_style(popup, "members")
            bubble.update()
