import math

from PyQt5.QtCore import QElapsedTimer, QPointF, QRectF, QSize, Qt, QTimer, pyqtProperty
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt5.QtWidgets import QProgressBar


class GlowProgressBar(QProgressBar):
    """Rounded progress bar with a gradient fill and a shimmer while work runs.

    Colours come from the theme QSS through ``qproperty-*`` so the shared
    retheme lifecycle recolours it; painting is fully custom because native
    QProgressBar styling blends into the light dialog background.
    """

    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"

    _HEIGHT = 22
    _FRAME_MS = 33
    _SHIMMER_MS = 1600
    _PULSE_MS = 1200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = self.IDLE
        self._track = QColor("#e7f1f0")
        self._border = QColor(15, 118, 110, 72)
        self._chunk = QColor("#0f766e")
        self._chunk_accent = QColor("#2dd4bf")
        self._error = QColor("#dc2626")
        self._text = QColor("#0f3d3a")
        self._chunk_text = QColor("#ffffff")
        self._clock = QElapsedTimer()
        self._clock.start()
        # Only the running state animates, and only while the bar is on screen.
        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(self._FRAME_MS)
        self._frame_timer.timeout.connect(self.update)
        self.setMinimumHeight(self._HEIGHT)
        self.setMaximumHeight(self._HEIGHT)

    def state(self) -> str:
        return self._state

    def setState(self, state: str) -> None:
        if state not in (self.RUNNING, self.IDLE, self.ERROR):
            raise ValueError(f"Unknown progress state: {state}")
        self._state = state
        self._sync_animation()
        self.update()

    def isAnimating(self) -> bool:
        return self._frame_timer.isActive()

    def _sync_animation(self) -> None:
        if self._state == self.RUNNING and self.isVisible():
            if not self._frame_timer.isActive():
                self._frame_timer.start()
        else:
            self._frame_timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._sync_animation()

    def sizeHint(self):
        return QSize(super().sizeHint().width(), self._HEIGHT)

    def minimumSizeHint(self):
        return QSize(super().minimumSizeHint().width(), self._HEIGHT)

    def _fraction(self) -> float:
        span = self.maximum() - self.minimum()
        if span <= 0:
            return 0.0
        return min(1.0, max(0.0, (self.value() - self.minimum()) / span))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = track.height() / 2

        track_path = QPainterPath()
        track_path.addRoundedRect(track, radius, radius)
        painter.fillPath(track_path, self._track)

        # The fill meets the border line; the border is stroked over it afterwards.
        fill_width = track.width() * self._fraction()
        fill_path = QPainterPath()
        if fill_width > 0:
            # Keep the rounded caps intact for tiny values.
            fill = QRectF(track.left(), track.top(), max(fill_width, track.height()), track.height())
            fill_path.addRoundedRect(fill, fill.height() / 2, fill.height() / 2)
            painter.setClipPath(track_path)
            self._paint_fill(painter, fill, fill_path)
            painter.setClipping(False)

        painter.setPen(QPen(self._border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(track_path)

        if self.isTextVisible() and self.text():
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(self._text)
            painter.drawText(track, Qt.AlignCenter, self.text())
            if not fill_path.isEmpty():
                # The part of the label that sits on the fill switches colour.
                painter.setClipPath(fill_path)
                painter.setPen(self._chunk_text)
                painter.drawText(track, Qt.AlignCenter, self.text())
        painter.end()

    def _paint_fill(self, painter, fill, fill_path):
        base = self._error if self._state == self.ERROR else self._chunk
        accent = self._error.lighter(135) if self._state == self.ERROR else self._chunk_accent
        gradient = QLinearGradient(fill.topLeft(), fill.topRight())
        gradient.setColorAt(0.0, base)
        gradient.setColorAt(1.0, accent)
        painter.fillPath(fill_path, gradient)

        gloss = QLinearGradient(fill.topLeft(), fill.bottomLeft())
        gloss.setColorAt(0.0, QColor(255, 255, 255, 70))
        gloss.setColorAt(0.5, QColor(255, 255, 255, 12))
        gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillPath(fill_path, gloss)

        if self._state != self.RUNNING:
            return
        elapsed = self._clock.elapsed()
        painter.save()
        painter.setClipPath(fill_path)
        band = max(48.0, fill.height() * 4)
        phase = (elapsed % self._SHIMMER_MS) / self._SHIMMER_MS
        left = fill.left() - band + phase * (fill.width() + band)
        shimmer = QLinearGradient(QPointF(left, 0), QPointF(left + band, 0))
        shimmer.setColorAt(0.0, QColor(255, 255, 255, 0))
        shimmer.setColorAt(0.5, QColor(255, 255, 255, 110))
        shimmer.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(QRectF(left, fill.top(), band, fill.height()), shimmer)
        painter.restore()

        # A soft pulse on the leading edge shows the batch is alive between steps.
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * (elapsed % self._PULSE_MS) / self._PULSE_MS)
        head = QPointF(fill.right() - fill.height() / 2, fill.center().y())
        glow = QRadialGradient(head, fill.height() * 1.1)
        glow_color = QColor(accent)
        glow_color.setAlpha(int(90 + 110 * pulse))
        glow.setColorAt(0.0, glow_color)
        glow_color.setAlpha(0)
        glow.setColorAt(1.0, glow_color)
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(head, fill.height() * 1.1, fill.height() * 1.1)

    def _color_property(name):
        def getter(self):
            return QColor(getattr(self, name))

        def setter(self, color):
            setattr(self, name, QColor(color))
            self.update()

        return pyqtProperty(QColor, getter, setter)

    trackColor = _color_property("_track")
    borderColor = _color_property("_border")
    chunkColor = _color_property("_chunk")
    chunkAccentColor = _color_property("_chunk_accent")
    errorColor = _color_property("_error")
    textColor = _color_property("_text")
    chunkTextColor = _color_property("_chunk_text")
    del _color_property
