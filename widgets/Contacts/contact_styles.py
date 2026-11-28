"""Development prototype: the contacts of a record card drawn in six ways, to choose one.

The chosen idea replaces ContactsWidget on the cards; the others are then removed.
"""
from __future__ import annotations

from typing import Optional, Sequence

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.responses import ContactInfo
from ...ui.theme_manager import ThemeManager
from ..DataDisplayWidgets.ContactsWidget import ContactLook, ContactTiles, contact_avatar
from ..flow_layout import FlowLayout, wrapping as _wrapping


# Made-up people: long and short names, companies, a shared role and a missing one.
SAMPLE_CONTACTS = (
    ContactInfo("Mari Maasikas", "Liituja"),
    ContactInfo("OÜ Parim Notar", "Notar", company=True),
    ContactInfo("Vahva Kaevur AS", "Lepinguline ehitaja", company=True),
    ContactInfo("Peeter Projekt", "Projekteerija"),
    ContactInfo("Jaan Järelevalve", "Omanikujärelevalve"),
    ContactInfo("Anneli Allikas", "Liituja"),
    ContactInfo("Kindel Tugi kindlustusselts OÜ", "", company=True),
    ContactInfo("Olev Oja", "Ehitushanke võitja"),
)


class ContactView(QWidget):
    """Base: keeps the contacts and the look, and redraws when either changes or the theme does."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._contacts: tuple[ContactInfo, ...] = ()
        self._look = ContactLook()
        _wrapping(self)
        self._body: Optional[QWidget] = None
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)

    def show_contacts(self, contacts: Sequence[ContactInfo], look: ContactLook) -> None:
        self._contacts, self._look = tuple(contacts), look
        self.retheme()

    def retheme(self) -> None:
        self.setStyleSheet(self._style(ThemeManager.effective_theme() == "dark"))
        if self._body is not None:
            self._body.hide()
            self._body.deleteLater()
        self._body = QFrame(self)
        self._body.setObjectName("CBody")
        _wrapping(self._body)
        self._outer.addWidget(self._body)
        shown = self._contacts[: self._look.shown or len(self._contacts)]
        self._fill(self._body, shown, len(self._contacts) - len(shown))
        self.updateGeometry()

    def _fill(self, body: QWidget, shown: Sequence[ContactInfo], hidden: int) -> None:
        raise NotImplementedError

    def _flow(self, body: QWidget, spacing: Optional[int] = None) -> FlowLayout:
        return FlowLayout(body, spacing=self._look.gap if spacing is None else spacing)

    def _label(self, text: str, name: str, parent: QWidget) -> QLabel:
        label = QLabel(text, parent)
        label.setObjectName(name)
        label.setTextFormat(Qt.TextFormat.PlainText)
        return label

    def _avatar(self, contact: ContactInfo, parent: QWidget, size: int = 24) -> QLabel:
        return contact_avatar(contact, parent, radius=self._look.radius, size=size)

    def _more(self, hidden: int, parent: QWidget) -> QLabel:
        label = self._label(f"+{hidden}", "CMore", parent)
        label.setToolTip("\n".join(
            f"{c.name} – {c.notes}" if c.notes else c.name for c in self._contacts[len(self._contacts) - hidden:]))
        label.setMinimumHeight(20)
        return label

    def _style(self, dark: bool) -> str:
        accent = "9,144,143" if dark else "33,136,255"
        text = "#d4d4de" if dark else "#24292e"
        muted = "#9aa4b2" if dark else "#6a737d"
        line = "rgba(150,150,160,0.35)" if dark else "rgba(60,80,100,0.18)"
        soft = "rgba(150,150,160,0.12)" if dark else "rgba(60,80,100,0.06)"
        radius = self._look.radius
        corner = max(0, min(radius - 1, 9))
        return "\n".join((
            f"QLabel {{ background: transparent; color: {text}; font-size: 11px; border: none; }}",
            "QFrame#CBody, QFrame#CPlain { background: transparent; border: none; }",
            f"QLabel#CRole {{ color: {muted}; font-size: 10px; }}",
            "QLabel#CName { font-weight: 600; }",
            f"QFrame#CCapsule {{ border: 1px solid {line}; border-radius: {min(radius, 10)}px; background: transparent; }}",
            f"QLabel#CCap {{ background: rgba({accent},0.78); color: #ffffff; font-size: 10px; font-weight: bold;"
            f"padding: 1px 4px; border-top-left-radius: {corner}px; border-bottom-left-radius: {corner}px; }}",
            "QLabel#CCapNone { color: " + muted + "; font-size: 10px; padding: 1px 4px; }",
            f"QLabel#CItem {{ padding: 1px 4px; border-right: 1px solid {line}; }}",
            "QLabel#CItemLast { padding: 1px 4px; }",
            f"QFrame#CTile {{ background: {soft}; border: 1px solid {line}; border-radius: {radius}px; }}",
            f"QLabel#CMore {{ background: {soft}; color: {muted}; font-weight: bold; padding: 1px 7px;"
            f"border: 1px solid {line}; border-radius: {min(radius, 9)}px; }}",
            f"QPushButton#CToggle {{ background: transparent; color: rgb({accent}); border: none; font-size: 11px;"
            "padding: 0 4px; text-align: left; }",
        ))


class RoleCapsuleView(ContactView):
    """1: capsules like the tags: the role on the filled end, everyone in that role after it."""

    def _fill(self, body, shown, hidden) -> None:
        flow = self._flow(body)
        by_role: dict[str, list[ContactInfo]] = {}
        for contact in shown:
            by_role.setdefault(contact.notes if self._look.roles else "", []).append(contact)
        for role, people in by_role.items():
            capsule = QFrame(body)
            capsule.setObjectName("CCapsule")
            row = QHBoxLayout(capsule)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(0)
            if role:
                row.addWidget(self._label(role, "CCap", capsule))
            for index, contact in enumerate(people):
                name = "CItemLast" if index == len(people) - 1 else "CItem"
                item = self._label(contact.name, name, capsule)
                item.setMinimumHeight(18)
                row.addWidget(item)
            flow.addWidget(capsule)
        if hidden:
            flow.addWidget(self._more(hidden, body))


class RoleColumnsView(ContactView):
    """2: a small table, role before name, in two columns."""

    def _fill(self, body, shown, hidden) -> None:
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(max(0, self._look.gap // 3))
        for index, contact in enumerate(shown):
            row, side = index // 2, (index % 2) * 3
            if self._look.roles:
                role = self._label(contact.notes or "–", "CRole", body)
                role.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                grid.addWidget(role, row, side)
            grid.addWidget(self._label(contact.name, "CName", body), row, side + 1)
        grid.setColumnMinimumWidth(2, self._look.gap * 2)
        grid.setColumnStretch(5, 1)
        if hidden:
            grid.addWidget(self._more(hidden, body), (len(shown) + 1) // 2, 1, Qt.AlignmentFlag.AlignLeft)


class TileView(ContactView):
    """3, chosen: the tiles the record cards now use."""

    def _fill(self, body, shown, hidden) -> None:
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        tiles = ContactTiles(body)
        tiles.show_contacts(self._contacts, look=self._look)
        column.addWidget(tiles)


class TextView(ContactView):
    """4: plain text that wraps: the least height."""

    def _fill(self, body, shown, hidden) -> None:
        flow = self._flow(body)
        for contact in shown:
            pair = QFrame(body)
            pair.setObjectName("CPlain")
            row = QHBoxLayout(pair)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            if self._look.roles and contact.notes:
                row.addWidget(self._label(f"{contact.notes}:", "CRole", pair))
            row.addWidget(self._label(contact.name, "CName", pair))
            flow.addWidget(pair)
        if hidden:
            flow.addWidget(self._more(hidden, body))


class AvatarRowView(ContactView):
    """5: initials only; name and role in the tooltip. The first contact is also written out."""

    def _fill(self, body, shown, hidden) -> None:
        flow = self._flow(body, spacing=max(2, self._look.gap // 2))
        for contact in shown:
            flow.addWidget(self._avatar(contact, body))
        if hidden:
            flow.addWidget(self._more(hidden, body))
        if shown:
            first = shown[0]
            text = f"{first.name} · {first.notes}" if self._look.roles and first.notes else first.name
            label = self._label(text, "CName", body)
            label.setMinimumHeight(24)
            flow.addWidget(label)


class ExpandableView(ContactView):
    """6: two contacts in sight, the rest behind a button."""

    VISIBLE = 2

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._open = False

    def _fill(self, body, shown, hidden) -> None:
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(max(1, self._look.gap // 3))
        visible = shown if self._open else shown[: self.VISIBLE]
        for contact in visible:
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(self._avatar(contact, body, size=20))
            row.addWidget(self._label(contact.name, "CName", body))
            if self._look.roles and contact.notes:
                row.addWidget(self._label(contact.notes, "CRole", body))
            row.addStretch(1)
            column.addLayout(row)
        rest = len(self._contacts) - min(self.VISIBLE, len(shown))
        if rest <= 0:
            return
        key = TranslationKeys.CONTACT_PROTO_LESS if self._open else TranslationKeys.CONTACT_PROTO_MORE
        toggle = QPushButton(self._lang.translate(key).format(count=rest), body)
        toggle.setObjectName("CToggle")
        toggle.setAutoDefault(False)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.clicked.connect(self._toggle)
        column.addWidget(toggle, 0, Qt.AlignmentFlag.AlignLeft)
        if self._open and hidden:
            column.addWidget(self._more(hidden, body), 0, Qt.AlignmentFlag.AlignLeft)

    def _toggle(self, _checked: bool = False) -> None:
        self._open = not self._open
        self.retheme()


IDEAS = (
    (TranslationKeys.CONTACT_IDEA_CAPSULES, RoleCapsuleView),
    (TranslationKeys.CONTACT_IDEA_COLUMNS, RoleColumnsView),
    (TranslationKeys.CONTACT_IDEA_TILES, TileView),
    (TranslationKeys.CONTACT_IDEA_TEXT, TextView),
    (TranslationKeys.CONTACT_IDEA_AVATARS, AvatarRowView),
    (TranslationKeys.CONTACT_IDEA_EXPAND, ExpandableView),
)
