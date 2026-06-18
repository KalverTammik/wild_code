from __future__ import annotations

from PyQt5.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor
from qgis.utils import iface

from ..utils.messagesHelper import ModernMessageDialog


class MapCanvasGlassActionBar(QWidget):
    """Small fixed-position test toolbar over the QGIS map canvas."""

    _active_instance = None

    TARGET_OFFSET = QPoint(18, 18)
    START_OFFSET = QPoint(18, -144)
    SIZE = (102, 132)

    def __init__(self, *, parent=None) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        parent = parent or canvas
        super().__init__(parent)
        self._canvas = canvas
        self._animation = None

        self.setObjectName("MapCanvasGlassActionBar")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if parent is None:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setFixedSize(*self.SIZE)

        self._build_ui()
        self._position_at(self.START_OFFSET)
        if self._canvas is not None:
            self._canvas.installEventFilter(self)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        frame = QFrame(self)
        frame.setObjectName("MapCanvasGlassActionBarFrame")
        frame.setStyleSheet(
            """
            QFrame#MapCanvasGlassActionBarFrame {
                background: rgba(248, 252, 255, 164);
                border: 1px solid rgba(30, 126, 180, 120);
                border-radius: 8px;
            }
            QPushButton#MapCanvasGlassActionButton {
                min-width: 76px;
                height: 26px;
                padding: 0 10px;
                border-radius: 6px;
                border: 1px solid rgba(22, 111, 151, 90);
                background: rgba(255, 255, 255, 118);
                color: #12394a;
                font-weight: 600;
            }
            QPushButton#MapCanvasGlassActionButton:hover {
                background: rgba(255, 255, 255, 190);
                border-color: rgba(22, 111, 151, 170);
            }
            QPushButton#MapCanvasGlassActionButton:pressed {
                background: rgba(203, 235, 247, 210);
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 60, 80, 78))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        for label in ("Vali", "Joonista", "Kinnita"):
            button = QPushButton(label, frame)
            button.setObjectName("MapCanvasGlassActionButton")
            button.setAutoDefault(False)
            button.setDefault(False)
            button.clicked.connect(lambda _checked=False, text=label: self._show_test_dialog(text))
            layout.addWidget(button)

        root.addWidget(frame)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._canvas and event.type() in (QEvent.Resize, QEvent.Show):
            self._position_at(self.TARGET_OFFSET if self.isVisible() else self.START_OFFSET)
        return super().eventFilter(watched, event)

    def _position_at(self, offset: QPoint) -> None:
        if self._canvas is not None:
            self.move(offset)
            return

        screen = self.screen()
        if screen is None:
            self.move(offset)
            return
        geometry = screen.availableGeometry()
        self.move(geometry.left() + offset.x(), geometry.top() + offset.y())

    def _show_test_dialog(self, action: str) -> None:
        ModernMessageDialog.show_info(
            "Glass action bar",
            f"Testnupp: {action}",
            parent=self,
        )

    def show_animated(self) -> None:
        self._position_at(self.START_OFFSET)
        self.show()
        self.raise_()

        self._animation = QPropertyAnimation(self, b"pos", self)
        self._animation.setDuration(240)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self.TARGET_OFFSET)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    @classmethod
    def show_for_session(cls) -> None:
        if cls._active_instance is not None:
            try:
                cls._active_instance.raise_()
                cls._active_instance._position_at(cls.TARGET_OFFSET)
                return
            except Exception:
                cls._active_instance = None

        bar = cls()
        cls._active_instance = bar
        bar.destroyed.connect(lambda *_: setattr(cls, "_active_instance", None))
        bar.show_animated()

    @classmethod
    def close_active(cls) -> None:
        if cls._active_instance is None:
            return
        try:
            cls._active_instance.close()
        except Exception:
            pass
        cls._active_instance = None
