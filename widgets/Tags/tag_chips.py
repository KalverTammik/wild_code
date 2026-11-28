"""The tags of one record as capsules: the group name on a filled left end, its tags after it,
one capsule per group and a neutral one for the ungrouped."""
from __future__ import annotations

from typing import Iterable, NamedTuple, Optional, Sequence

from qgis.PyQt.QtCore import QPoint, QRect, QSize, Qt
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QSizePolicy, QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.tag_catalog import Tag, TagCatalog
from ...ui.theme_manager import ThemeManager

GROUP_TONES = 5  # groups take the strengths of the one accent colour in list order
UNGROUPED_TONE = "none"
_STRENGTHS = (0.70, 0.77, 0.84, 0.91, 0.98)

# separator -> (text written after a tag, whether a vertical line is drawn instead)
SEPARATORS = {"dot": ("  ·", False), "comma": (",", False), "bar": ("", True), "slash": ("  /", False), "none": ("", False)}
SEPARATOR_KEYS = {
    "dot": TranslationKeys.TAG_SEPARATOR_DOT, "comma": TranslationKeys.TAG_SEPARATOR_COMMA,
    "bar": TranslationKeys.TAG_SEPARATOR_BAR, "slash": TranslationKeys.TAG_SEPARATOR_SLASH,
    "none": TranslationKeys.TAG_SEPARATOR_NONE,
}


class Look(NamedTuple):
    """The measures of a capsule; the defaults are the user's choice (2026-11-28)."""

    radius: int = 6  # outer roundness
    height: int = 0  # extra space above and below, inside the capsule
    tag_gap: int = 3  # between the tags
    capsule_gap: int = 6  # between the capsules
    separator: str = "bar"
    tag_pad: int = 2  # left and right of a tag's text
    name_pad: int = 2  # left and right of the group name


DEFAULT_LOOK = Look()


class Section(NamedTuple):
    name: str  # empty while the catalog is not known
    tone: str  # "0".."4" or UNGROUPED_TONE
    tags: tuple[Tag, ...]


def sections(
    catalog: TagCatalog, selected_ids: Iterable[str], ungrouped_name: str, record_tags: Sequence[Tag] = (),
) -> list[Section]:
    """The groups that hold a selected tag, in list order, with the ungrouped last.

    `record_tags` names tags the catalog does not hold (yet); without a catalog nothing is known about
    grouping, so they come in one unnamed section.
    """
    selected = set(selected_ids)
    result = []
    known: set[str] = set()
    for index, (group, tags) in enumerate(catalog.groups):
        known.update(tag.id for tag in tags)
        chosen = tuple(tag for tag in tags if tag.id in selected)
        if chosen:
            result.append(Section(group.name, str(index % GROUP_TONES), chosen))
    known.update(tag.id for tag in catalog.ungrouped)
    rest = [tag for tag in catalog.ungrouped if tag.id in selected]
    rest += [tag for tag in record_tags if tag.id in selected and tag.id not in known]
    if rest:
        result.append(Section(ungrouped_name if len(catalog) else "", UNGROUPED_TONE, tuple(rest)))
    return result


class FlowLayout(QLayout):
    """Left to right, breaking onto the next line when the width runs out.

    An item wider than the whole line that can wrap itself (a holder) gets the line width and the height it needs.
    """

    def __init__(self, parent: Optional[QWidget] = None, *, spacing: int = 6) -> None:
        super().__init__(parent)
        self._items: list = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(spacing)

    def addItem(self, item) -> None:  # noqa: N802 - Qt override
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):  # noqa: N802
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int):  # noqa: N802
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._arrange(QRect(0, 0, width, 0), move=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._arrange(rect, move=True)

    def sizeHint(self) -> QSize:  # noqa: N802
        """Everything on one line, so that a holder asks for the width it would like."""
        hints = [item.sizeHint() for item in self._items]
        margins = self.contentsMargins()
        width = sum(hint.width() for hint in hints) + self.spacing() * max(0, len(hints) - 1)
        height = max((hint.height() for hint in hints), default=0)
        return QSize(width + margins.left() + margins.right(), height + margins.top() + margins.bottom())

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _arrange(self, rect: QRect, *, move: bool) -> int:
        margins = self.contentsMargins()
        inner = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, line_height = inner.x(), inner.y(), 0
        for item in self._items:
            size = item.sizeHint()
            if size.width() > inner.width() and item.hasHeightForWidth():
                size = QSize(inner.width(), item.heightForWidth(inner.width()))
            if x > inner.x() and x + size.width() > inner.x() + inner.width():
                x, y, line_height = inner.x(), y + line_height + self.spacing(), 0
            if move:
                item.setGeometry(QRect(QPoint(x, y), size))
            x += size.width() + self.spacing()
            line_height = max(line_height, size.height())
        return y + line_height - rect.y() + margins.bottom()


def _wrapping(widget: QWidget) -> None:
    policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    policy.setHeightForWidth(True)
    widget.setSizePolicy(policy)


def _wrapping(widget: QWidget) -> None:
    policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    policy.setHeightForWidth(True)
    widget.setSizePolicy(policy)


def _label(text: str, name: str, parent: QWidget, **properties: str) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName(name)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setMinimumHeight(18)
    for key, value in properties.items():
        label.setProperty(key, value)
    return label


class _Capsule(QFrame):
    """The name end and the tags; the tags wrap inside when the capsule is wider than the card."""

    def __init__(self, section: Section, look: Look, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("TagCapsule")
        _wrapping(self)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)  # the filled name end reaches the border
        row.setSpacing(0)
        self._name: Optional[QLabel] = None
        if section.name:
            self._name = _label(section.name, "TagCapsuleName", self, tone=section.tone)
            self._name.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            row.addWidget(self._name)
        body = QFrame(self)
        body.setObjectName("TagCapsuleBody")
        self.tags = FlowLayout(body, spacing=look.tag_gap)
        self.tags.setContentsMargins(4, 1 + look.height, 4, 1 + look.height)
        row.addWidget(body, 1)
        suffix, _line = SEPARATORS[look.separator]
        for position, tag in enumerate(section.tags):
            last = position == len(section.tags) - 1
            self.tags.addWidget(_label(
                tag.name + ("" if last else suffix), "TagName", body, place="last" if last else "inner"))

    def hasHeightForWidth(self) -> bool:  # noqa: N802 - Qt override
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        frame = 2 * self.frameWidth()
        name = self._name.sizeHint() if self._name is not None else QSize(0, 0)
        return max(name.height(), self.tags.heightForWidth(width - name.width() - frame)) + frame


class TagChipsView(QWidget):
    """A wrapping row of capsules. It carries its own stylesheet, so it looks the same wherever it is put."""

    def __init__(self, parent: Optional[QWidget] = None, *, look: Look = DEFAULT_LOOK) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._look = look
        _wrapping(self)
        self._flow = FlowLayout(self, spacing=look.capsule_gap)
        self._shown: Optional[tuple] = None
        self.retheme()

    def set_look(self, look: Look) -> None:
        self._look = look
        self._flow.setSpacing(look.capsule_gap)
        self.retheme()

    def show_tags(self, catalog: TagCatalog, selected_ids: Iterable[str], *, record_tags: Sequence[Tag] = ()) -> None:
        """The selected tags by group."""
        self._shown = (catalog, list(selected_ids), tuple(record_tags))
        self._rebuild()

    def _rebuild(self) -> None:
        catalog, selected, record_tags = self._shown
        while self._flow.count():
            widget = self._flow.takeAt(0).widget()
            widget.hide()
            widget.deleteLater()
        ungrouped = self._lang.translate(TranslationKeys.TAG_PICKER_UNGROUPED)
        for section in sections(catalog, selected, ungrouped, record_tags):
            self._flow.addWidget(_Capsule(section, self._look, self))
        if not self._flow.count():
            self._flow.addWidget(_label(self._lang.translate(TranslationKeys.TAG_CHIPS_EMPTY), "TagsEmpty", self))
        for index in range(self._flow.count()):
            self._flow.itemAt(index).widget().show()
        self.updateGeometry()

    def retheme(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        accent = "9,144,143" if dark else "33,136,255"
        text = "#d4d4de" if dark else "#24292e"
        muted = "#9aa4b2" if dark else "#6a737d"
        line = "rgba(150,150,160,0.35)" if dark else "rgba(60,80,100,0.18)"
        look = self._look
        # Qt draws square corners when the radius exceeds half the height, so it is kept within it.
        outer = max(0, min(look.radius, 10 + look.height))
        corner = max(0, min(outer - 1, 9))
        _suffix, bar = SEPARATORS[look.separator]
        rules = [
            f"QLabel {{ background: transparent; color: {text}; font-size: 11px; border: none; }}",
            f"QLabel#TagsEmpty {{ color: {muted}; }}",
            "QFrame#TagCapsuleBody { background: transparent; border: none; }",
            f"QFrame#TagCapsule {{ background: transparent; border: 1px solid {line}; border-radius: {outer}px; }}",
            f"QLabel#TagName {{ padding: 1px {look.tag_pad}px;"
            + (f" border-right: 1px solid {line};" if bar else "") + " }",
            'QLabel#TagName[place="last"] { border-right: none; }',
        ]
        fills = [(str(index), f"rgba({accent},{strength})") for index, strength in enumerate(_STRENGTHS)]
        for tone, fill in fills + [(UNGROUPED_TONE, "#8b949e")]:
            rules.append(
                f'QLabel#TagCapsuleName[tone="{tone}"] {{ background: {fill}; color: #ffffff; font-size: 10px;'
                f"font-weight: bold; padding: 1px {look.name_pad}px;"
                f"border-top-left-radius: {corner}px; border-bottom-left-radius: {corner}px; }}")
        self.setStyleSheet("\n".join(rules))
        if self._shown is not None:
            self._rebuild()
