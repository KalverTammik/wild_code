"""The contacts of a record card as tiles: initials (round for a person, square for a company),
the name and the role under it, on one line: as many as fit, at least one; hovering the "+N" mark
lists the rest as the same tiles."""
from __future__ import annotations

import zlib
from dataclasses import replace
from typing import NamedTuple, Optional, Sequence

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.responses import ContactInfo, DataDisplayExtractors
from ...ui.theme_manager import ThemeManager
from ..overflow_row import OverflowRow

_AVATAR_COLORS = ("#3b7dd8", "#2f9e6e", "#c2702b", "#8a5cd1", "#c2497a", "#4c8c9c")
_COMPANY_FORMS = ("OÜ", "AS", "MTÜ", "TÜ", "FIE")
_LONGEST_TEXT = 40  # characters of a name or role on a tile; the tooltip has the whole text


class ContactLook(NamedTuple):
    """The measures of the tiles; the defaults are the user's choice (2026-11-28)."""

    shown: int = 0  # a cap on the tiles of the line; 0: only the width limits them
    roles: bool = True
    gap: int = 6  # between the tiles
    radius: int = 6


DEFAULT_LOOK = ContactLook()


def initials(name: str) -> str:
    """First letters of the first and last word, leaving out the company form."""
    words = [word for word in name.split() if word.upper() not in _COMPANY_FORMS]
    return "".join(word[0] for word in (words[:1] + words[1:][-1:])).upper() or "?"


def shortened(text: str) -> str:
    """A long name or note must not widen the card: the first tile of a line is never hidden."""
    return text if len(text) <= _LONGEST_TEXT else text[:_LONGEST_TEXT - 1].rstrip() + "…"


def contact_avatar(contact: ContactInfo, parent: QWidget, *, radius: int, size: int = 24) -> QLabel:
    """The colour follows the name, so a contact looks the same on every card."""
    avatar = QLabel(initials(contact.name), parent)
    avatar.setObjectName("ContactAvatar")
    avatar.setTextFormat(Qt.TextFormat.PlainText)
    avatar.setFixedSize(size, size)
    avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    color = _AVATAR_COLORS[zlib.crc32(contact.name.encode("utf-8")) % len(_AVATAR_COLORS)]
    corner = min(radius, size // 2) if contact.company else size // 2
    letters = 10 if size >= 24 else 8  # two letters must fit the small circle too
    avatar.setStyleSheet(
        f"background: {color}; color: #ffffff; font-size: {letters}px; font-weight: bold; border-radius: {corner}px;")
    avatar.setToolTip("\n".join(part for part in (contact.name, contact.notes) if part))
    return avatar


class ContactTiles(OverflowRow):
    """One line of contact tiles. It carries its own stylesheet."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._contacts: tuple[ContactInfo, ...] = ()
        self._total = 0
        self._look = DEFAULT_LOOK
        self._tiles: list[QFrame] = []

    def show_contacts(
        self, contacts: Sequence[ContactInfo], *, total: Optional[int] = None, look: ContactLook = DEFAULT_LOOK,
    ) -> None:
        """`total` counts also the contacts that were not read."""
        self._contacts = tuple(contacts)
        self._total = max(len(self._contacts), total or 0)
        self._look = look
        self.retheme()

    def retheme(self) -> None:
        self.setStyleSheet(self._style(ThemeManager.effective_theme() == "dark"))
        self.gap = self._look.gap
        for tile in self._tiles:
            tile.hide()
            tile.deleteLater()
        self._tiles = [self._tile(contact, self) for contact in self._contacts]
        self.reflow()

    def entry_count(self) -> int:
        return len(self._contacts)

    def most_visible(self) -> int:
        return self._look.shown or self.entry_count()

    def uncounted(self) -> int:
        return self._total - len(self._contacts)

    def _tile_width(self, tile: QFrame) -> int:
        tile.ensurePolished()
        for label in tile.findChildren(QLabel):
            label.ensurePolished()
        return tile.sizeHint().width()

    def line_width(self, count: int) -> int:
        return sum(self._tile_width(tile) for tile in self._tiles[:count]) + self.gap * max(0, count - 1)

    def line_height(self) -> int:
        heights = []
        for tile in self._tiles:
            tile.ensurePolished()
            heights.append(tile.sizeHint().height())
        return max(heights, default=20)

    def place(self, count: int) -> None:
        x = 0
        for index, tile in enumerate(self._tiles):
            if index >= count:
                tile.hide()
                continue
            width = self._tile_width(tile)
            tile.setGeometry(x, 0, width, self.line_height())
            tile.show()
            x += width + self.gap

    def popup_widgets(self, count: int, parent: QWidget) -> list[QWidget]:
        """The contacts that are not on the line, as the same tiles one under another."""
        widgets: list[QWidget] = [self._tile(contact, parent) for contact in self._contacts[count:]]
        if self.uncounted() > 0:
            text = self._lang.translate(TranslationKeys.CONTACTS_AND_MORE).format(count=self.uncounted())
            widgets.append(self._label(text, "ContactRole", parent))
        return widgets

    def _tile(self, contact: ContactInfo, parent: QWidget) -> QFrame:
        tile = QFrame(parent)
        tile.setObjectName("ContactTile")
        row = QHBoxLayout(tile)
        row.setContentsMargins(4, 3, 9, 3)
        row.setSpacing(6)
        row.addWidget(contact_avatar(contact, tile, radius=self._look.radius))
        column = QVBoxLayout()
        column.setSpacing(0)
        column.addWidget(self._label(shortened(contact.name), "ContactName", tile))
        if self._look.roles and contact.notes:
            column.addWidget(self._label(shortened(contact.notes), "ContactRole", tile))
        row.addLayout(column)
        tile.setToolTip("\n".join(part for part in (contact.name, contact.notes) if part))
        return tile

    @staticmethod
    def _label(text: str, name: str, parent: QWidget) -> QLabel:
        label = QLabel(text, parent)
        label.setObjectName(name)
        label.setTextFormat(Qt.TextFormat.PlainText)
        return label

    def _style(self, dark: bool) -> str:
        text = "#d4d4de" if dark else "#24292e"
        muted = "#9aa4b2" if dark else "#6a737d"
        line = "rgba(150,150,160,0.35)" if dark else "rgba(60,80,100,0.18)"
        soft = "rgba(150,150,160,0.12)" if dark else "rgba(60,80,100,0.06)"
        radius = self._look.radius
        return "\n".join([
            f"QLabel {{ background: transparent; color: {text}; font-size: 11px; border: none; }}",
            f"QFrame#ContactTile {{ background: {soft}; border: 1px solid {line}; border-radius: {radius}px; }}",
            "QLabel#ContactName { font-weight: 600; }",
            f"QLabel#ContactRole {{ color: {muted}; font-size: 10px; }}",
            *self.row_style(dark, radius),
        ])


class ContactsWidget(ContactTiles):
    """The contacts of one record; hidden when it has none."""

    def __init__(self, item_data, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        contacts = [c for c in (DataDisplayExtractors.extract_contacts(item_data) or []) if c.name]
        if not contacts:
            self.setVisible(False)
            return
        self.show_contacts(contacts, total=DataDisplayExtractors.extract_contact_total(item_data))


class ClientWidget(ContactTiles):
    """The record's client as one tile, its role saying what it is."""

    def __init__(self, client: ContactInfo, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        role = self._lang.translate(TranslationKeys.CONTACT_ROLE_CLIENT)
        self.show_contacts([replace(client, notes=role)])
