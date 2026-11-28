"""The designs and colour sets of the toolbar summary ("shown" beside "all"), chosen by the user.

Every design paints the same numbers and marks the clickable ones: (whole data, overdue) -> place.
"""
from __future__ import annotations

from typing import Callable, NamedTuple, Optional

from qgis.PyQt.QtCore import QRectF, Qt
from qgis.PyQt.QtGui import QColor, QPainterPath

from ...languages.translation_keys import TranslationKeys as K
from .dashboard_cards import BLUE, CENTER, LATE, OK, RIGHT, SOON, Brush

# The measures, the user's choice (2026-11-28).
WIDTH = 260
_ROW = 21  # height of a row
_PILL_WIDTH = 38
_PILL_HEIGHT = 16
_PILL_RADIUS = 6
_NUMBER = 12  # font of the totals
_LABEL = 11  # font of the row names
_BAR = 5  # thickness of the bars
_STRENGTH = 0.62  # how solid the coloured fills are
_THICK = max(_PILL_HEIGHT, _BAR)


class Palette(NamedTuple):
    name_key: str
    late: str
    soon: str
    fine: str
    total: str


PALETTES = {
    "standard": Palette(K.INDICATOR_PALETTE_STANDARD, LATE, SOON, OK, BLUE),
    "pastel": Palette(K.INDICATOR_PALETTE_PASTEL, "#f28b8b", "#f6cf7a", "#8fd3c4", "#9db8ee"),
    "strong": Palette(K.INDICATOR_PALETTE_STRONG, "#d92d20", "#f79009", "#079455", "#1570ef"),
    "teal": Palette(K.INDICATOR_PALETTE_TEAL, "#e4685d", "#e0a84a", "#09908f", "#2b6f8f"),
    "colorblind": Palette(K.INDICATOR_PALETTE_COLORBLIND, "#d55e00", "#f0c000", "#0072b2", "#56b4e9"),
    "grey": Palette(K.INDICATOR_PALETTE_GREY, "#e5484d", "#8b949e", "#c3cad3", "#6a737d"),
}
DEFAULT_PALETTE = "standard"


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _ink(color: str) -> str:
    """The text colour that reads on a fill."""
    c = QColor(color)
    return "#26210f" if 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue() > 160 else "#ffffff"


class Paint:
    """One painting of the summary. `data`: (what the filters leave, the whole module) as ModuleCounts;
    the brush carries the colour set."""

    def __init__(self, brush: Brush, data: tuple, active, cells: dict) -> None:
        self.b, self.data, self.active, self.cells = brush, data, active, cells

    def rows(self):
        return ((False, self.b.say(K.HOME_ROW_SHOWN), self.data[0]), (True, self.b.say(K.HOME_ROW_ALL), self.data[1]))

    def measures(self):
        """(name, colour, field of the counts, overdue or None for the total)."""
        b = self.b
        return ((b.say(K.HOME_COLUMN_TOTAL).capitalize(), b.blue, "total", None),
                (b.say(K.HOME_COLUMN_LATE).capitalize(), b.late, "late", True),
                (b.say(K.HOME_COLUMN_SOON).capitalize(), b.soon, "soon", False))

    @staticmethod
    def tone(color: str, share: float = 1.0) -> str:
        """The colour at the fills' strength, as #AARRGGBB."""
        c = QColor(color)
        c.setAlpha(round(255 * share * _STRENGTH))
        return c.name(QColor.NameFormat.HexArgb)

    def parts(self, item) -> tuple:
        # An overdue record may also fall in the coming days' window; a bar counts it once.
        return ((item.late, self.tone(self.b.late)), (min(item.soon, item.total - item.late), self.tone(self.b.soon)),
                (item.fine, self.tone(self.b.ok)))

    def box(self, rect: tuple, color: str, radius: float) -> None:
        self.b.box(rect, color, max(0.0, min(radius, rect[3] / 2)))

    def clipped(self, rect: tuple, radius: float, paint: Callable[[], None]) -> None:
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(*rect), radius, radius)
        self.b.p.save()
        self.b.p.setClipPath(clip)
        paint()
        self.b.p.restore()

    def outline(self, rect: tuple, radius: float, color: str) -> None:
        self.b.p.setBrush(Qt.BrushStyle.NoBrush)
        self.b.p.setPen(QColor(color))
        self.b.p.drawRoundedRect(QRectF(*rect), radius, radius)

    def mark(self, rect: tuple, key: tuple) -> None:
        """Makes a place clickable and outlines it while the list shows it."""
        self.cells[key] = QRectF(*rect)
        if self.active == key:
            self.outline((rect[0] - 2.5, rect[1] - 2, rect[2] + 5, rect[3] + 4),
                         min(_PILL_RADIUS + 2, (rect[3] + 4) / 2), self.b.text_color)

    def pill(self, rect: tuple, count: int, color: str, key: tuple) -> None:
        """A clickable number; a dash for zero, which leads nowhere unless the list shows it."""
        if not count:
            self.b.text(rect, "–", _LABEL, self.b.muted, align=CENTER)
            if self.active == key:
                self.mark(rect, key)
            return
        self.box(rect, self.tone(color), _PILL_RADIUS)
        self.b.text(rect, _number(count), _LABEL, _ink(color), True, CENTER)
        self.mark(rect, key)

    def number(self, rect: tuple, count: int, size: int, color: str, key: Optional[tuple]) -> None:
        self.b.text(rect, _number(count), size, color, True, CENTER)
        if key is not None and (count or self.active == key):
            self.mark(rect, key)


# ---- a row for the selection and a row for the whole ------------------------------
_SOON_X = WIDTH - _PILL_WIDTH - 8
_LATE_X = WIDTH - 2 * _PILL_WIDTH - 16
_TOTAL_X = _LATE_X - 66


def _header(p: Paint, with_total: bool = True, shift: int = 0) -> None:
    b = p.b
    if with_total:
        b.text((_TOTAL_X - 6, 4, 64, 14), b.say(K.HOME_COLUMN_TOTAL), 9, b.muted, align=RIGHT)
    for x, key in ((_LATE_X, K.HOME_COLUMN_LATE), (_SOON_X, K.HOME_COLUMN_SOON)):
        b.text((x + shift - 8, 4, _PILL_WIDTH + 16, 14), b.say(key), 9, b.muted, align=CENTER)


def _row_pills(p: Paint, y: float, height: float, whole: bool, item, shift: int) -> None:
    py = y + (height - _PILL_HEIGHT) / 2
    p.pill((_LATE_X + shift, py, _PILL_WIDTH, _PILL_HEIGHT), item.late, p.b.late, (whole, True))
    p.pill((_SOON_X + shift, py, _PILL_WIDTH, _PILL_HEIGHT), item.soon, p.b.soon, (whole, False))


def table_bands(p: Paint, width: int, height: int) -> None:
    b = p.b
    _header(p)
    band = _ROW + _BAR
    for index, (whole, name, item) in enumerate(p.rows()):
        y = 20 + index * (band + 4)
        accent = b.muted if whole else b.blue
        tint = QColor(accent)
        tint.setAlpha(22 if whole else 34)
        p.box((5, y, width - 10, band), tint.name(QColor.NameFormat.HexArgb), 7)
        p.box((5, y, 3, band), accent, 1.5)
        text_height = band - _BAR - 3
        b.text((16, y, 60, text_height), name, _LABEL, bold=True)
        b.text((_TOTAL_X, y, 58, text_height), _number(item.total), _NUMBER, bold=True, align=RIGHT)
        b.stacked((16, y + band - _BAR - 3, _TOTAL_X + 42, _BAR), p.parts(item), _BAR / 2)
        _row_pills(p, y, band, whole, item, -3)


def table_filled(p: Paint, width: int, height: int) -> None:
    """The band itself is the bar."""
    b = p.b
    _header(p)
    for index, (whole, name, item) in enumerate(p.rows()):
        y = 20 + index * (_ROW + 4)
        rect = (6, y, _TOTAL_X + 56, _ROW)
        p.box(rect, b.track, 7)
        if item.total:
            def fill(y: float = y, item=item, room: float = rect[2]) -> None:
                x = 6.0
                for count, color in ((item.late, b.late), (min(item.soon, item.total - item.late), b.soon),
                                     (item.fine, b.ok)):
                    part = room * count / item.total
                    if count > 0:
                        b.box((x, y, part, _ROW), p.tone(color, 0.6), 0)
                    x += part

            p.clipped(rect, 7, fill)
        b.text((14, y, 60, _ROW), name, _LABEL, bold=True)
        b.text((_TOTAL_X - 4, y, 58, _ROW), _number(item.total), _NUMBER, bold=True, align=RIGHT)
        _row_pills(p, y, _ROW, whole, item, -1)


def table_capsules(p: Paint, width: int, height: int) -> None:
    """Capsules like the tags: the row's name on a filled left end."""
    b = p.b
    _header(p)
    name_width = max(46, max(b.width(name, _LABEL, True) for _whole, name, _item in p.rows()) + 18)
    for index, (whole, name, item) in enumerate(p.rows()):
        y = 20 + index * (_ROW + 5)
        color = b.muted if whole else b.blue
        radius = min(_PILL_RADIUS + 1, _ROW / 2)
        p.outline((6.5, y + 0.5, width - 13, _ROW - 1), radius, b.line)
        p.clipped((6, y, width - 12, _ROW), radius,
                  lambda y=y, whole=whole, color=color: b.box((6, y, name_width, _ROW),
                                                              color if whole else p.tone(color), 0))
        b.text((6, y, name_width, _ROW), name, _LABEL, _ink(color), True, CENTER)
        left = 6 + name_width + 8
        room = _TOTAL_X - left + 4
        if room >= 24:
            b.stacked((left, y + (_ROW - _BAR) / 2, room, _BAR), p.parts(item), _BAR / 2)
        b.text((_TOTAL_X - 4, y, 58, _ROW), _number(item.total), _NUMBER, bold=True, align=RIGHT)
        _row_pills(p, y, _ROW, whole, item, -3)


def table_big_totals(p: Paint, width: int, height: int) -> None:
    """The total large in front, the name small above the row's bar."""
    b = p.b
    _header(p, with_total=False)
    big = _NUMBER + 6
    band = max(big + 8, 15 + _BAR + 8)
    front = max(b.width(_number(item.total), big, True) for item in p.data) + 4
    for index, (whole, name, item) in enumerate(p.rows()):
        y = 18 + index * (band + 3)
        if not whole:
            p.box((5, y, width - 10, band), p.tone(b.blue, 0.2), 8)
        b.text((12, y, front, band), _number(item.total), big, b.muted if whole else b.text_color, True, RIGHT)
        left = 12 + front + 10
        room = _LATE_X - 14 - left
        b.text((left, y + 2, room, 15), name, _LABEL - 1, b.muted, True)
        b.stacked((left, y + 18, room, _BAR), p.parts(item), _BAR / 2)
        _row_pills(p, y, band, whole, item, -3)


# ---- a part for each measure -------------------------------------------------------
def _sides(p: Paint, x_shown: float, x_all: float, y: float, width: float, align_all=RIGHT) -> None:
    b = p.b
    b.text((x_shown, y, width, 14), b.say(K.HOME_ROW_SHOWN).lower(), 9, b.muted)
    b.text((x_all, y, width, 14), b.say(K.HOME_ROW_ALL).lower(), 9, b.muted, align=align_all)


def share_bars(p: Paint, width: int, height: int) -> None:
    """One wide bar for each measure; the selection's number at its start, the whole at its end."""
    b = p.b
    left = 78
    room = width - left - 10
    shown, everything = p.data
    for index, (name, color, field, overdue) in enumerate(p.measures()):
        y = 8 + index * (_THICK + 5)
        part, whole = getattr(shown, field), getattr(everything, field)
        b.text((10, y, 66, _THICK), name, _LABEL, bold=True)
        p.box((left, y, room, _THICK), p.tone(color, 0.2) if whole else b.track, _PILL_RADIUS)
        # The filled part is the selection's share, never narrower than its figures.
        figures = b.width(_number(part), _LABEL, True) + 18
        filled = max(figures, room * min(1.0, part / whole)) if part and whole else 0
        if filled:
            p.box((left, y, filled, _THICK), p.tone(color), _PILL_RADIUS)
            b.text((left, y, figures, _THICK), _number(part), _LABEL, _ink(color), True, CENTER)
        elif not whole:
            b.text((left, y, room, _THICK), "–", _LABEL, b.muted, align=CENTER)
        if whole:
            end = b.width(_number(whole), _LABEL, True) + 18
            b.text((left + room - end, y, end, _THICK), _number(whole), _LABEL, b.text_color, True, CENTER)
            if overdue is not None:
                p.mark((left + room - end, y, end, _THICK), (True, overdue))
        if filled and overdue is not None:
            p.mark((left, y, filled, _THICK), (False, overdue))
        # A number the list shows stays clickable also when it has meanwhile dropped to zero.
        for whole_side, gone, x in ((False, not filled, left), (True, not whole, left + room - 30)):
            if gone and p.active == (whole_side, overdue):
                p.mark((x, y, 30, _THICK), (whole_side, overdue))
    _sides(p, left, left + room - 80, height - 15, 80)


def share_lines(p: Paint, width: int, height: int) -> None:
    """A thin share line under each measure, the two numbers at the right."""
    b = p.b
    shown, everything = p.data
    first, second = width - 2 * _PILL_WIDTH - 18, width - _PILL_WIDTH - 8
    for x, key in ((first, K.HOME_ROW_SHOWN), (second, K.HOME_ROW_ALL)):
        b.text((x, 3, _PILL_WIDTH, 14), b.say(key).lower(), 9, b.muted, align=CENTER)
    step = max(_ROW, 15 + _BAR)
    for index, (name, color, field, overdue) in enumerate(p.measures()):
        y = 18 + index * step
        part, whole = getattr(shown, field), getattr(everything, field)
        room = first - 20
        b.text((10, y, room, 14), name, _LABEL, bold=True)
        line = y + step - _BAR - 2
        p.box((10, line, room, _BAR), p.tone(color, 0.28) if whole else b.track, _BAR / 2)
        if part and whole:
            p.box((10, line, max(_BAR, room * min(1.0, part / whole)), _BAR), p.tone(color), _BAR / 2)
        for x, count, everything_side in ((first, part, False), (second, whole, True)):
            rect = (x, y + (step - _PILL_HEIGHT) / 2, _PILL_WIDTH, _PILL_HEIGHT)
            if overdue is None:
                p.number(rect, count, _NUMBER, b.muted if everything_side else b.text_color, None)
            else:
                p.pill(rect, count, color, (everything_side, overdue))


def columns(p: Paint, width: int, height: int) -> None:
    """The three measures side by side, each with its share bar."""
    b = p.b
    shown, everything = p.data
    step = (width - 12) / 3
    big = _NUMBER + 7
    for index, (name, color, field, overdue) in enumerate(p.measures()):
        x = 6 + index * step
        part, whole = getattr(shown, field), getattr(everything, field)
        p.box((x + 3, 6, step - 6, height - 12), p.tone(color, 0.18), _PILL_RADIUS + 2)
        b.text((x, 9, step, 14), name, _LABEL - 1, b.muted, True, CENTER)
        over = f"/ {_number(whole)}"
        left_width = max(26, b.width(_number(part), big, True) + 10)
        right_width = b.width(over, _LABEL) + 8
        start = x + (step - left_width - right_width) / 2
        p.number((start, 24, left_width, big + 4), part, big, b.text_color,
                 None if overdue is None else (False, overdue))
        rect = (start + left_width, 28, right_width, big)
        b.text(rect, over, _LABEL, b.muted, align=CENTER)
        if overdue is not None and (whole or p.active == (True, overdue)):
            p.mark(rect, (True, overdue))
        line = height - _BAR - 11
        room = step - 22
        p.box((x + 11, line, room, _BAR), b.track, _BAR / 2)
        if part and whole:
            p.box((x + 11, line, max(_BAR, room * min(1.0, part / whole)), _BAR), p.tone(color), _BAR / 2)


def measure_capsules(p: Paint, width: int, height: int) -> None:
    """Capsules like the tags: the measure on a filled left end, its share filling the body."""
    b = p.b
    shown, everything = p.data
    thick = max(_PILL_HEIGHT + 2, 18)
    name_width = max(b.width(name, _LABEL, True) for name, _c, _f, _o in p.measures()) + 18
    left = 8 + name_width
    room = width - left - 8
    _sides(p, left + 6, left + room - 66, 2, 60)
    for index, (name, color, field, overdue) in enumerate(p.measures()):
        y = 17 + index * (thick + 4)
        part, whole = getattr(shown, field), getattr(everything, field)
        radius = min(_PILL_RADIUS + 1, thick / 2)

        def fill(y: float = y, color: str = color, part: int = part, whole: int = whole) -> None:
            b.box((8, y, name_width, thick), p.tone(color), 0)
            if part and whole:
                b.box((left, y, max(3.0, room * min(1.0, part / whole)), thick), p.tone(color, 0.35), 0)

        p.clipped((8, y, width - 16, thick), radius, fill)
        p.outline((8.5, y + 0.5, width - 17, thick - 1), radius, b.line)
        b.text((8, y, name_width, thick), name, _LABEL, _ink(color), True, CENTER)
        first = b.width(_number(part), _NUMBER, True) + 14
        p.number((left + 2, y + 1, first, thick - 2), part, _NUMBER, b.text_color,
                 None if overdue is None else (False, overdue))
        last = b.width(_number(whole), _NUMBER, True) + 14
        p.number((left + room - last - 2, y + 1, last, thick - 2), whole, _NUMBER, b.text_color,
                 None if overdue is None else (True, overdue))


class Design(NamedTuple):
    name_key: str
    height: int
    paint: Callable[[Paint, int, int], None]


DESIGNS = {
    "columns": Design(K.INDICATOR_DESIGN_COLUMNS, max(66, _NUMBER + 43 + _BAR), columns),
    "bands": Design(K.INDICATOR_DESIGN_BANDS, 20 + 2 * (_ROW + _BAR) + 10, table_bands),
    "filled": Design(K.INDICATOR_DESIGN_FILLED, 20 + 2 * _ROW + 10, table_filled),
    "table_capsules": Design(K.INDICATOR_DESIGN_TABLE_CAPSULES, 20 + 2 * _ROW + 11, table_capsules),
    "big_totals": Design(K.INDICATOR_DESIGN_BIG_TOTALS, 18 + 2 * max(_NUMBER + 14, 23 + _BAR) + 7, table_big_totals),
    "share_bars": Design(K.INDICATOR_DESIGN_SHARE_BARS, 3 * _THICK + 42, share_bars),
    "share_lines": Design(K.INDICATOR_DESIGN_SHARE_LINES, 18 + 3 * max(_ROW, 15 + _BAR) + 4, share_lines),
    "capsules": Design(K.INDICATOR_DESIGN_CAPSULES, 17 + 3 * (max(_PILL_HEIGHT + 2, 18) + 4) + 3, measure_capsules),
}
DEFAULT_DESIGN = "columns"
