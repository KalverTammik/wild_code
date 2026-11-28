"""The tags of one record as capsules: the group name on a filled left end, its tags after it,
one capsule per group and a neutral one for the ungrouped.

They stand on one line: as many tags as fit, at least one; hovering the "+N" mark shows the rest."""
from __future__ import annotations

from typing import Iterable, NamedTuple, Optional, Sequence

from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.tag_catalog import Tag, TagCatalog
from ...ui.theme_manager import ThemeManager
from ..flow_layout import FlowLayout, wrapping
from ..overflow_row import OverflowRow

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


def _label(text: str, name: str, parent: QWidget, **properties: str) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName(name)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setMinimumHeight(18)
    for key, value in properties.items():
        label.setProperty(key, value)
    return label


class _Capsule(QFrame):
    """The name end and the tags; in the popup the tags wrap inside a capsule that is too wide."""

    def __init__(self, section: Section, look: Look, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("TagCapsule")
        wrapping(self)
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


def first_tags(found: Sequence[Section], count: int) -> list[Section]:
    """The first `count` tags of the sections, keeping their grouping."""
    result = []
    for section in found:
        if count <= 0:
            break
        result.append(section._replace(tags=section.tags[:count]))
        count -= len(section.tags)
    return result


def later_tags(found: Sequence[Section], count: int) -> list[Section]:
    """Everything after the first `count` tags."""
    result = []
    for section in found:
        rest = section.tags[max(0, count):]
        count -= len(section.tags)
        if rest:
            result.append(section._replace(tags=rest))
    return result


class TagChipsView(OverflowRow):
    """One line of capsules. It carries its own stylesheet, so it looks the same wherever it is put."""

    POPUP_WIDTH = 460

    def __init__(self, parent: Optional[QWidget] = None, *, look: Look = DEFAULT_LOOK) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._look = look
        self._shown: Optional[tuple] = None
        self._sections: list[Section] = []
        self._widths: Optional[tuple] = None  # measured per section: (name width, [tag widths])
        self._line: list[QWidget] = []  # what stands on the line, left to right
        self.retheme()

    def set_look(self, look: Look) -> None:
        self._look = look
        self.retheme()

    def show_tags(self, catalog: TagCatalog, selected_ids: Iterable[str], *, record_tags: Sequence[Tag] = ()) -> None:
        """The selected tags by group."""
        self._shown = (catalog, list(selected_ids), tuple(record_tags))
        self._rebuild()

    def _rebuild(self) -> None:
        catalog, selected, record_tags = self._shown
        ungrouped = self._lang.translate(TranslationKeys.TAG_PICKER_UNGROUPED)
        self._sections = sections(catalog, selected, ungrouped, record_tags)
        self.gap = self._look.capsule_gap
        self.reflow()

    def reflow(self) -> None:
        self._widths = None
        super().reflow()

    # ---- measures -----------------------------------------------------------------
    def _measure(self) -> tuple:
        """The widths of every name and tag, read once from throwaway capsules."""
        if self._widths is None:
            measured = []
            for section in self._sections:
                capsule = _Capsule(section, self._look, self)
                capsule.ensurePolished()
                labels = [*capsule.findChildren(QLabel)]
                for label in labels:
                    label.ensurePolished()
                name = next((item.sizeHint().width() for item in labels if item.objectName() == "TagCapsuleName"), 0)
                tags = [item.sizeHint().width() for item in labels if item.objectName() == "TagName"]
                measured.append((name, tags, capsule.sizeHint().height()))
                capsule.setParent(None)
                capsule.deleteLater()
            self._widths = tuple(measured)
        return self._widths

    def entry_count(self) -> int:
        return sum(len(section.tags) for section in self._sections)

    def line_width(self, count: int) -> int:
        if not self._sections:
            return self._empty_width()
        total, capsules = 0, 0
        for name, tags, _height in self._measure():
            if count <= 0:
                break
            part = tags[:count]
            count -= len(tags)
            # name, the body's side margins, the tags with their gaps, the two border pixels
            total += name + 8 + sum(part) + self._look.tag_gap * (len(part) - 1) + 2
            capsules += 1
        return total + self.gap * max(0, capsules - 1)

    def _empty_width(self) -> int:
        text = self._lang.translate(TranslationKeys.TAG_CHIPS_EMPTY)
        return self.fontMetrics().horizontalAdvance(text) + 8

    def line_height(self) -> int:
        return max((height for _name, _tags, height in self._measure()), default=20)

    # ---- the line and the popup ---------------------------------------------------
    def place(self, count: int) -> None:
        for widget in self._line:
            widget.hide()
            widget.deleteLater()
        self._line = []
        x = 0
        for section in first_tags(self._sections, count):
            capsule = _Capsule(section, self._look, self)
            capsule.ensurePolished()
            width = capsule.sizeHint().width()
            if not self._line:
                width = min(width, max(width if self.width() <= 0 else self.width(), 1))
            capsule.setGeometry(x, 0, width, self.line_height())
            capsule.show()
            self._line.append(capsule)
            x += width + self.gap
        if not self._sections and self._shown is not None:
            empty = _label(self._lang.translate(TranslationKeys.TAG_CHIPS_EMPTY), "TagsEmpty", self)
            empty.setGeometry(0, 0, self._empty_width(), self.line_height())
            empty.show()
            self._line.append(empty)

    def popup_widgets(self, count: int, parent: QWidget) -> list[QWidget]:
        widgets = []
        for section in later_tags(self._sections, count):
            capsule = _Capsule(section, self._look, parent)
            capsule.ensurePolished()
            width = min(self.POPUP_WIDTH, capsule.sizeHint().width())
            capsule.setFixedSize(width, capsule.heightForWidth(width))
            widgets.append(capsule)
        return widgets

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
        self.setStyleSheet("\n".join(rules + self.row_style(dark, look.radius)))
        if self._shown is not None:
            self._rebuild()
