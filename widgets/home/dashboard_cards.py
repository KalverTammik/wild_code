"""The painted cards of the home page and of the module toolbars. Each card is one function that
paints it whole."""
from __future__ import annotations

from typing import Callable, NamedTuple, Optional

from qgis.PyQt.QtCore import QPointF, QRectF, QSize, Qt
from qgis.PyQt.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import QWidget

from ...constants.module_icons import ModuleIconPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from .dashboard_counts import ASBUILT, CONTRACT, COORDINATION, EASEMENT, PROJECT, SOURCES, WORKS, ModuleCounts

OK, SOON, LATE, BLUE = "#17b89f", "#f2b318", "#ff5757", "#5b8def"
LOADING_MARK, FAILED_MARK = "…", "–"

LEFT, RIGHT, CENTER = Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight, Qt.AlignmentFlag.AlignHCenter


class Snapshot:
    """What is known of every module: its counts, or that they are still coming or did not come."""

    def __init__(self) -> None:
        self.counts: dict[str, ModuleCounts] = {}
        self.failed: set[str] = set()

    def get(self, key: str) -> Optional[ModuleCounts]:
        return self.counts.get(key)

    def mark(self, key: str) -> str:
        return FAILED_MARK if key in self.failed else LOADING_MARK


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _by_urgency(b, item: ModuleCounts) -> tuple:
    # An overdue record may also fall in the coming days' window; the bar counts it once.
    return (item.late, b.late), (min(item.soon, item.total - item.late), b.soon), (item.fine, b.ok)


class Brush:
    """The few things the cards draw, in the colours of the theme."""

    def __init__(self, painter: QPainter, widget: QWidget, dark: bool) -> None:
        self.p = painter
        self.size = (widget.width(), widget.height())
        self.font = widget.font()
        self.text_color = "#e3e3ec" if dark else "#0f1833"
        self.muted = "#9aa4b2" if dark else "#6a7690"
        self.track = "#3a404d" if dark else "#e6ebf2"
        self.surface = "#262a33" if dark else "#ffffff"
        self.line = "#444a57" if dark else "#d9e0ea"
        self.late, self.soon, self.ok, self.blue = LATE, SOON, OK, BLUE
        self.lang = LanguageManager()

    def say(self, key: str, **values) -> str:
        return self.lang.translate(key).format(**values)

    def module(self, key: str) -> str:
        return self.lang.translate_module_name(key)

    def _use_font(self, size: int, bold: bool) -> None:
        font = QFont(self.font)
        font.setPixelSize(size)
        font.setBold(bold)
        self.p.setFont(font)

    def text(self, rect, value: str, size: int = 11, color: Optional[str] = None, bold: bool = False,
             align=LEFT) -> None:
        self._use_font(size, bold)
        self.p.setPen(QColor(color or self.text_color))
        self.p.drawText(QRectF(*rect), align | Qt.AlignmentFlag.AlignVCenter, value)

    def width(self, value: str, size: int, bold: bool = False) -> int:
        self._use_font(size, bold)
        return self.p.fontMetrics().horizontalAdvance(value)

    def box(self, rect, color: str, radius: float = 3.0, border: Optional[str] = None) -> None:
        self.p.setPen(QPen(QColor(border), 1) if border else Qt.PenStyle.NoPen)
        self.p.setBrush(QColor(color))
        self.p.drawRoundedRect(QRectF(*rect), radius, radius)

    def icon(self, key: str, x: int, y: int, size: int = 16) -> None:
        pixmap = QPixmap(ModuleIconPaths.get_module_icon(key) or "")
        if not pixmap.isNull():
            self.p.drawPixmap(x, y, pixmap.scaled(
                size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def title(self, key: str, label: str = "") -> None:
        self.icon(key, 12, 9)
        self.text((34, 8, 220, 18), label or self.module(key), 12, bold=True)

    def waiting(self, mark: str) -> None:
        """In place of a card's figures while there are none."""
        self.text((0, 0, self.size[0], self.size[1]), mark, 24, self.muted, True, CENTER)

    def stacked(self, rect, parts, radius: float = 4.0) -> None:
        """A bar divided by (count, colour) parts."""
        x, y, width, height = rect
        self.box(rect, self.track, radius)
        total = sum(count for count, _color in parts)
        if total <= 0:
            return
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(*rect), radius, radius)
        self.p.save()
        self.p.setClipPath(clip)
        at = float(x)
        for count, color in parts:
            part = width * count / total
            if count > 0:
                self.box((at, y, max(1.0, part - 1.0), height), color, 0)
            at += part
        self.p.restore()

    def arc(self, rect, parts, thickness: float, start: float, sweep: float) -> None:
        """A part of a ring, drawn clockwise from `start` degrees."""
        def draw(color: str, begin: float, length: float) -> None:
            self.p.setPen(QPen(QColor(color), thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            self.p.setBrush(Qt.BrushStyle.NoBrush)
            self.p.drawArc(QRectF(*rect), int(begin * 16), int(-length * 16))

        draw(self.track, start, sweep)
        total = sum(count for count, _color in parts)
        at = start
        for count, color in parts:
            if total > 0 and count > 0:
                length = sweep * count / total
                draw(color, at, length)
                at -= length

    def spark(self, rect, values, color: str) -> None:
        if len(values) < 2:
            return
        x, y, width, height = rect
        top = max(max(values), 1)
        points = [QPointF(x + width * index / (len(values) - 1), y + height - height * value / top)
                  for index, value in enumerate(values)]
        line = QPainterPath(points[0])
        for point in points[1:]:
            line.lineTo(point)
        area = QPainterPath(line)
        area.lineTo(x + width, y + height)
        area.lineTo(x, y + height)
        area.closeSubpath()
        fill = QColor(color)
        fill.setAlpha(45)
        self.p.fillPath(area, fill)
        self.p.setPen(QPen(QColor(color), 2))
        self.p.setBrush(Qt.BrushStyle.NoBrush)
        self.p.drawPath(line)
        self.p.setPen(Qt.PenStyle.NoPen)
        self.p.setBrush(QColor(color))
        self.p.drawEllipse(points[-1], 3.5, 3.5)


def summary_strip(b: Brush, data: Snapshot) -> None:
    """What is overdue, over all modules that have deadlines."""
    known = [item for item in map(data.get, SOURCES) if item is not None]
    late = sum(item.late for item in known)
    accent = b.late if late else b.ok if known else b.track
    figure = _number(late) if known else LOADING_MARK if not data.failed else FAILED_MARK
    b.box((0.5, 0.5, 6, b.size[1] - 1), accent, 3)
    b.text((22, 10, 130, 38), figure, 32, accent if known else b.muted, True)
    x = 30 + b.width(figure, 32, True)
    b.text((x, 14, 200, 18), b.say(TranslationKeys.HOME_OVERDUE_RECORDS), 13, bold=True)
    if data.failed:
        note = b.say(TranslationKeys.HOME_PARTLY_UNREAD)
    elif len(known) < len(SOURCES):
        note = b.say(TranslationKeys.LOADING)
    else:
        note = b.say(TranslationKeys.HOME_ALSO_DUE_SOON, count=_number(sum(item.soon for item in known)))
    b.text((x, 34, 200, 16), note, 11, b.muted)
    step = 84
    start = b.size[0] - step * len(SOURCES) - 8
    for index, key in enumerate(SOURCES):
        item = data.get(key)
        left = start + index * step
        b.icon(key, left + step // 2 - 9, 12, 18)
        value = _number(item.late) if item else data.mark(key)
        b.text((left, 34, step, 18), value, 14, b.late if item and item.late else b.muted, True, CENTER)
        b.text((left, 54, step, 14), b.module(key), 9, b.muted, align=CENTER)


def deadline_table(b: Brush, data: Snapshot) -> None:
    """Projects, contracts and coordinations compared."""
    b.text((14, 8, 200, 18), b.say(TranslationKeys.HOME_DEADLINES), 12, bold=True)
    for x, key, width in ((332, TranslationKeys.HOME_COLUMN_TOTAL, 50), (392, TranslationKeys.HOME_COLUMN_LATE, 60),
                          (458, TranslationKeys.HOME_COLUMN_SOON, 60)):
        b.text((x, 8, width, 18), b.say(key), 10, b.muted, align=RIGHT)
    for row, key in enumerate((PROJECT, CONTRACT, COORDINATION)):
        item = data.get(key)
        y = 44 + row * 34
        b.icon(key, 14, y + 2)
        b.text((36, y, 110, 20), b.module(key), 12)
        b.stacked((150, y + 6, 170, 9), _by_urgency(b, item) if item else ())
        b.text((332, y, 50, 20), _number(item.total) if item else data.mark(key), 13, bold=True, align=RIGHT)
        if item is None:
            continue
        for x, count, color, ink in ((404, item.late, b.late, "#ffffff"), (470, item.soon, b.soon, "#3a2c00")):
            if count:
                b.box((x, y + 1, 48, 18), color, 9)
                b.text((x, y + 1, 48, 18), str(count), 11, ink, True, CENTER)
            else:
                b.text((x, y, 48, 20), "–", 11, b.muted, align=CENTER)


def coordination_health(b: Brush, data: Snapshot) -> None:
    """How large a part of the coordinations is in time."""
    b.title(COORDINATION)
    item = data.get(COORDINATION)
    if item is None:
        b.waiting(data.mark(COORDINATION))
        return
    b.arc((60, 40, 140, 140), tuple(reversed(_by_urgency(b, item))), 14, 180, 180)
    # Rounded down: 100% only when nothing is overdue.
    share = f"{100 * (item.total - item.late) // item.total}%" if item.total else "–"
    b.text((60, 72, 140, 34), share, 28, bold=True, align=CENTER)
    b.text((60, 102, 140, 16), b.say(TranslationKeys.HOME_IN_TIME), 10, b.muted, align=CENTER)
    b.text((12, 126, 130, 18), b.say(TranslationKeys.HOME_COUNT_OVERDUE, count=_number(item.late)),
           11, b.late if item.late else b.muted, True)
    b.text((138, 126, 110, 18), b.say(TranslationKeys.HOME_COUNT_TOTAL, count=_number(item.total)),
           11, b.muted, align=RIGHT)


def contract_weeks(b: Brush, data: Snapshot) -> None:
    """Contracts whose deadline has passed or is coming, week by week."""
    b.title(CONTRACT, b.say(TranslationKeys.HOME_DEADLINES_AHEAD, module=b.module(CONTRACT)))
    item = data.get(CONTRACT)
    if item is None:
        b.waiting(data.mark(CONTRACT))
        return
    counts = (item.late, *item.weeks)
    top = max(max(counts), 1)
    for index, count in enumerate(counts):
        x = 16 + index * 39
        height = 76 * count / top
        color = b.late if index == 0 else b.soon if index == 1 else b.blue
        label = (b.say(TranslationKeys.HOME_WEEK_LATE) if index == 0
                 else b.say(TranslationKeys.HOME_WEEK_NUMBER, count=index))
        b.box((x, 122 - max(2, height), 28, max(2, height)), color if count else b.track, 4)
        b.text((x - 5, 104 - height, 38, 16), str(count), 10, bold=True, align=CENTER)
        b.text((x - 5, 126, 38, 16), label, 10, b.muted, align=CENTER)


def works_trend(b: Brush, data: Snapshot) -> None:
    """The number of works with the new ones over a year."""
    b.title(WORKS)
    item = data.get(WORKS)
    if item is None:
        b.waiting(data.mark(WORKS))
        return
    b.text((12, 34, 100, 34), _number(item.total), 28, bold=True)
    b.text((110, 34, 138, 16), b.say(TranslationKeys.HOME_NEW_IN_3_MONTHS, count=_number(sum(item.months[-3:]))),
           10, b.muted, align=RIGHT)
    b.text((110, 50, 138, 16), b.say(TranslationKeys.HOME_COUNT_OVERDUE, count=_number(item.late)),
           11, b.late if item.late else b.muted, True, RIGHT)
    b.spark((14, 78, 232, 46), item.months, b.ok)
    b.text((12, 128, 120, 14), b.say(TranslationKeys.HOME_YEAR_AGO), 9, b.muted)
    b.text((128, 128, 120, 14), b.say(TranslationKeys.HOME_THIS_MONTH), 9, b.muted, align=RIGHT)


def module_tile(key: str) -> Callable[[Brush, Snapshot], None]:
    """The module's number with a thin deadline bar."""
    def paint(b: Brush, data: Snapshot) -> None:
        item = data.get(key)
        soft = QColor(b.blue)
        soft.setAlpha(40)
        b.p.setPen(Qt.PenStyle.NoPen)
        b.p.setBrush(soft)
        b.p.drawRoundedRect(QRectF(10, 12, 38, 38), 10, 10)
        b.icon(key, 19, 21, 20)
        b.text((58, 6, 100, 28), _number(item.total) if item else data.mark(key), 22, bold=True)
        b.text((58, 33, 190, 16), b.module(key), 11, b.muted)
        if item and item.late:
            b.text((b.size[0] - 130, 12, 118, 18), b.say(TranslationKeys.HOME_COUNT_LATE, count=_number(item.late)),
                   10, b.late, True, RIGHT)
        b.stacked((58, 55, b.size[0] - 70, 5), _by_urgency(b, item) if item else (), 2.5)
    return paint


def coordination_health_strip(b: Brush, data: Snapshot) -> None:
    """The share of coordinations in time, as low as a toolbar."""
    b.title(COORDINATION)
    item = data.get(COORDINATION)
    if item is None:
        b.text((12, 32, 130, 28), data.mark(COORDINATION), 22, b.muted, True)
        return
    b.text((12, 30, 130, 16), b.say(TranslationKeys.HOME_COUNT_OVERDUE, count=_number(item.late)),
           11, b.late if item.late else b.muted, True)
    b.text((12, 46, 130, 16), b.say(TranslationKeys.HOME_COUNT_TOTAL, count=_number(item.total)), 10, b.muted)
    left = b.size[0] - 100
    b.arc((left, 10, 88, 88), tuple(reversed(_by_urgency(b, item))), 9, 180, 180)
    share = f"{100 * (item.total - item.late) // item.total}%" if item.total else "–"
    b.text((left, 30, 88, 20), share, 17, bold=True, align=CENTER)
    b.text((left, 49, 88, 14), b.say(TranslationKeys.HOME_IN_TIME), 9, b.muted, align=CENTER)


def contract_weeks_strip(b: Brush, data: Snapshot) -> None:
    """The coming contract deadlines, as low as a toolbar."""
    item = data.get(CONTRACT)
    b.text((10, 3, b.size[0] - 20, 14), b.say(TranslationKeys.HOME_DEADLINES_AHEAD, module=b.module(CONTRACT)),
           10, bold=True)
    if item is None:
        b.text((0, 18, b.size[0], 45), data.mark(CONTRACT), 22, b.muted, True, CENTER)
        return
    counts = (item.late, *item.weeks)
    top = max(max(counts), 1)
    step = (b.size[0] - 16) / len(counts)
    for index, count in enumerate(counts):
        x = 8 + index * step
        height = max(2.0, 22 * count / top)
        color = b.late if index == 0 else b.soon if index == 1 else b.blue
        label = (b.say(TranslationKeys.HOME_WEEK_LATE) if index == 0
                 else b.say(TranslationKeys.HOME_WEEK_NUMBER, count=index))
        b.box((x + step / 2 - 10, 54 - height, 20, height), color if count else b.track, 2)
        b.text((x, 41 - height, step, 13), str(count), 9, bold=True, align=CENTER)
        b.text((x, 54, step, 13), label, 9, b.muted, align=CENTER)


def works_trend_strip(b: Brush, data: Snapshot) -> None:
    """The works and their year, as low as a toolbar."""
    item = data.get(WORKS)
    if item is None:
        b.waiting(data.mark(WORKS))
        return
    b.text((12, 4, 120, 28), _number(item.total), 22, bold=True)
    b.text((12, 32, 130, 15), b.say(TranslationKeys.HOME_NEW_IN_3_MONTHS, count=_number(sum(item.months[-3:]))),
           10, b.muted)
    b.text((12, 47, 130, 15), b.say(TranslationKeys.HOME_COUNT_OVERDUE, count=_number(item.late)),
           10, b.late if item.late else b.muted, True)
    b.spark((145, 12, b.size[0] - 159, 44), item.months, b.ok)


class CardSpec(NamedTuple):
    modules: tuple[str, ...]  # whose numbers it shows
    size: tuple[int, int]
    paint: Callable[[Brush, Snapshot], None]
    min_width: int = 0  # narrower than this the card is left blank


# The page: rows of columns of cards. Three columns of 260 with gaps of 12 make 804.
PAGE: tuple = (
    ((CardSpec(tuple(SOURCES), (804, 76), summary_strip),),),
    ((CardSpec((PROJECT, CONTRACT, COORDINATION), (532, 150), deadline_table),),
     (CardSpec((COORDINATION,), (260, 150), coordination_health),)),
    ((CardSpec((CONTRACT,), (260, 150), contract_weeks),),
     (CardSpec((WORKS,), (260, 150), works_trend),),
     (CardSpec((EASEMENT,), (260, 69), module_tile(EASEMENT)),
      CardSpec((ASBUILT,), (260, 69), module_tile(ASBUILT)))),
)


_STRIP = (260, 69)
_STRIP_MIN_WIDTH = 220


def _strip(key: str, paint: Callable[[Brush, Snapshot], None]) -> CardSpec:
    return CardSpec((key,), _STRIP, paint, _STRIP_MIN_WIDTH)


# The modules that show a card of their own in the toolbar, beside the summary of their numbers.
TOOLBAR = {
    CONTRACT: _strip(CONTRACT, contract_weeks_strip),
    COORDINATION: _strip(COORDINATION, coordination_health_strip),
    WORKS: _strip(WORKS, works_trend_strip),
}

class HomeCard(QWidget):
    def __init__(self, spec: CardSpec, data: Snapshot, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.data = data
        self.dark = False
        self.colors: Optional[tuple[str, str, str, str]] = None  # late, soon, fine, total; None: the standard
        self.setFixedSize(*spec.size)

    def lang(self, key: str) -> str:
        return LanguageManager().translate(key)

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        return QSize(*self.spec.size)

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.width() < self.spec.min_width:
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            brush = Brush(painter, self, self.dark)
            if self.colors:
                brush.late, brush.soon, brush.ok, brush.blue = self.colors
            brush.box((0.5, 0.5, self.width() - 1, self.height() - 1), brush.surface, 10, brush.line)
            self.spec.paint(brush, self.data)
        finally:
            painter.end()  # an unfinished painter would break every later paint
