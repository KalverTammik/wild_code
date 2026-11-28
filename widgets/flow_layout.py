"""A left-to-right layout that wraps, used where tags and contacts are listed."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QPoint, QRect, QSize
from qgis.PyQt.QtWidgets import QLayout, QSizePolicy, QWidget


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


def wrapping(widget: QWidget) -> None:
    """Lets a layout give the widget the height its width needs."""
    policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    policy.setHeightForWidth(True)
    widget.setSizePolicy(policy)
