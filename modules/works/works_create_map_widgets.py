"""Map-side helpers of the works create flow: the point capture tool and the small
progress bubble shown next to a map toolbar button."""
from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool


class WorksPointCaptureTool(QgsMapTool):
    def __init__(self, canvas, on_selected: Callable[[QgsPointXY], None], on_cancel: Callable[[], None]):
        super().__init__(canvas)
        self.canvas = canvas
        self._on_selected = on_selected
        self._on_cancel = on_cancel
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self._on_selected(point)
            return
        if event.button() == Qt.RightButton:
            self._on_cancel()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._on_cancel()


class MapButtonProgressBubble(QFrame):
    WIDTH = 286
    HEIGHT = 44
    GAP = 8

    def __init__(self, *, text: str, anchor, parent=None) -> None:
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self._anchor = anchor
        self.setObjectName("MapButtonProgressBubble")
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            """
            QFrame#MapButtonProgressBubble {
                background: rgba(248, 252, 255, 220);
                border: 1px solid rgba(30, 126, 180, 150);
                border-radius: 8px;
            }
            QLabel#MapButtonProgressLabel {
                color: #12394a;
                font-weight: 600;
            }
            QProgressBar#MapButtonProgressBar {
                min-width: 74px;
                max-width: 74px;
                height: 8px;
                border: 1px solid rgba(22, 111, 151, 90);
                border-radius: 4px;
                background: rgba(255, 255, 255, 120);
                text-align: center;
            }
            QProgressBar#MapButtonProgressBar::chunk {
                border-radius: 3px;
                background: rgba(15, 118, 110, 160);
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        label = QLabel(text, self)
        label.setObjectName("MapButtonProgressLabel")
        label.setWordWrap(False)
        layout.addWidget(label, 1)

        progress = QProgressBar(self)
        progress.setObjectName("MapButtonProgressBar")
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        layout.addWidget(progress)

    def show_near_anchor(self) -> None:
        anchor = self._anchor
        if anchor is not None:
            try:
                top_left = anchor.mapToGlobal(QPoint(0, 0))
                y_pos = top_left.y() + max(0, (anchor.height() - self.HEIGHT) // 2)
                self.move(max(0, top_left.x() - self.WIDTH - self.GAP), max(0, y_pos))
            except RuntimeError:
                pass
        self.show()
        self.raise_()
