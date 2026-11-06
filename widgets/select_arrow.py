from __future__ import annotations

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget


class SelectArrow(QWidget):
    """Down arrow of select controls built from frames, in the combo box arrow's shape and colour."""

    COLOR = "#b2b2b2"
    DISABLED_ALPHA = 110

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(7, 7)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt override
        color = QColor(self.COLOR)
        if not self.isEnabled():
            color.setAlpha(self.DISABLED_ALPHA)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([QPointF(0.5, 0.5), QPointF(6.5, 0.5), QPointF(3.5, 6.5)]))
