from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QTimer
from PyQt5.QtGui import QColor, QPainter, QConicalGradient, QPen, QFont
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


class GradientSpinner(QWidget):
    """
    Donut-style rotating gradient spinner with optional center text
    and animated trailing dots.
    """

    def __init__(self, parent=None, diameter=80,
                 border_color=QColor(63, 249, 220),
                 border_thickness=8,
                 text="",
                 text_color=None,
                 font=None,
                 sub_text="",
                 sub_text_color=None,
                 sub_text_font=None,
                 dots_enabled=True,
                 dots_interval_ms=300):
        super().__init__(parent)

        self._angle = 0.0
        self._diameter = diameter
        self._border_color = QColor(border_color)
        self._border_thickness = border_thickness

        self._base_text = text or ""
        self._dots_enabled = dots_enabled
        self._dots_interval_ms = dots_interval_ms
        self._dot_count = 0  # 0..3

        self._text_color = text_color or QColor(34, 36, 48)
        self._font = font
        self._sub_text = sub_text or ""
        self._sub_text_color = sub_text_color or QColor(90, 94, 110)
        self._sub_text_font = sub_text_font

        self.setFixedSize(diameter, diameter)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Spinner rotation animation
        self._anim = QPropertyAnimation(self, b"angle", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(360.0)
        self._anim.setDuration(900)
        self._anim.setLoopCount(-1)

        # Dots animation
        self._dots_timer = QTimer(self)
        self._dots_timer.setInterval(self._dots_interval_ms)
        self._dots_timer.timeout.connect(self._advanceDots)

    # --- property used by QPropertyAnimation ---
    def getAngle(self):
        return self._angle

    def setAngle(self, value):
        self._angle = float(value)
        self.update()

    angle = pyqtProperty(float, fget=getAngle, fset=setAngle)

    # --- public API ---
    def start(self):
        if self._anim.state() != QPropertyAnimation.Running:
            self._anim.start()
        if self._dots_enabled and not self._dots_timer.isActive():
            self._dots_timer.start()

    def stop(self):
        self._anim.stop()
        self._dots_timer.stop()

    def setText(self, text: str):
        self._base_text = text or ""
        self.update()

    def text(self) -> str:
        return self._base_text

    def setTextColor(self, color: QColor):
        self._text_color = QColor(color)
        self.update()

    def setSpinnerFont(self, font: QFont):
        self._font = font
        self.update()

    def setSubText(self, text: str):
        self._sub_text = text or ""
        self.update()

    def setSubTextColor(self, color: QColor):
        self._sub_text_color = QColor(color)
        self.update()

    def setSubTextFont(self, font: QFont):
        self._sub_text_font = font
        self.update()

    def setDotsEnabled(self, enabled: bool):
        self._dots_enabled = bool(enabled)
        if not self._dots_enabled:
            self._dots_timer.stop()
            self._dot_count = 0
            self.update()
        elif self._anim.state() == QPropertyAnimation.Running and not self._dots_timer.isActive():
            self._dots_timer.start()

    def setDotsInterval(self, ms: int):
        self._dots_interval_ms = int(ms)
        self._dots_timer.setInterval(self._dots_interval_ms)

    # --- internal ---
    def _advanceDots(self):
        # cycle through 0..3 dots
        self._dot_count = (self._dot_count + 1) % 4
        self.update()

    # --- painting ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ring rect
        margin = self._border_thickness // 2 + 1
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Conical gradient rotated by current angle
        grad = QConicalGradient(rect.center(), -self._angle)
        c = self._border_color

        grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 40))
        grad.setColorAt(0.25, QColor(c.red(), c.green(), c.blue(), 255))
        grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), 80))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 40))

        pen = QPen()
        pen.setWidth(self._border_thickness)
        pen.setBrush(grad)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        if self._base_text or self._dots_enabled or self._sub_text:
            main_font = self._font or painter.font()
            painter.setFont(main_font)
            metrics_main = painter.fontMetrics()

            def advance(metrics, text: str) -> int:
                try:
                    return metrics.horizontalAdvance(text)
                except AttributeError:
                    return metrics.width(text)

            main_height = metrics_main.height() if (self._base_text or self._dots_enabled) else 0

            sub_metrics = None
            sub_height = 0
            if self._sub_text:
                if self._sub_text_font is not None:
                    painter.setFont(self._sub_text_font)
                sub_metrics = painter.fontMetrics()
                sub_height = sub_metrics.height()
                painter.setFont(main_font)

            line_spacing = 4 if (self._base_text or self._dots_enabled) and self._sub_text else 0
            content_height = main_height + line_spacing + sub_height
            top_y = (self.height() - content_height) / 2

            if self._base_text or self._dots_enabled:
                painter.setFont(main_font)
                metrics = metrics_main
                text_width = advance(metrics, self._base_text) if self._base_text else 0

                dot_slots = 3
                dot_char = "."
                dot_width = advance(metrics, dot_char)
                dot_gap = max(2, dot_width // 2)
                dots_width = dot_slots * dot_width + (dot_slots - 1) * dot_gap if dot_slots else 0

                text_dot_gap = dot_gap * 2 if self._base_text and self._dots_enabled else 0
                group_width = text_width + text_dot_gap + (dots_width if self._dots_enabled else 0)
                start_x = int(round((self.width() - group_width) / 2))
                baseline_y = int(round(top_y + metrics.ascent()))

                painter.setPen(self._text_color)
                if self._base_text:
                    painter.drawText(start_x, baseline_y, self._base_text)

                if self._dots_enabled:
                    dots_x = int(start_x + text_width + text_dot_gap)
                    active_color = QColor(self._text_color)
                    inactive_color = QColor(self._text_color)
                    inactive_color.setAlpha(40)
                    for slot in range(dot_slots):
                        painter.setPen(active_color if slot < self._dot_count else inactive_color)
                        painter.drawText(dots_x, baseline_y, dot_char)
                        dots_x += dot_width + dot_gap

            if self._sub_text:
                if self._sub_text_font is not None:
                    painter.setFont(self._sub_text_font)
                    metrics = painter.fontMetrics()
                else:
                    painter.setFont(main_font)
                    metrics = sub_metrics or painter.fontMetrics()

                sub_width = advance(metrics, self._sub_text)
                sub_start_x = int(round((self.width() - sub_width) / 2))
                sub_baseline_y = int(round(top_y + main_height + line_spacing + metrics.ascent()))
                painter.setPen(self._sub_text_color)
                painter.drawText(sub_start_x, sub_baseline_y, self._sub_text)

        painter.end()

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle(LanguageManager().translate(TranslationKeys.DELAY_HELPERS_LOADINGSPINNER_TITLE))
    layout = QVBoxLayout(window)
    layout.setContentsMargins(32, 32, 32, 32)
    layout.setSpacing(16)

    label = QLabel("Spinner preview – animated dots in the center")
    label.setWordWrap(True)
    layout.addWidget(label)

    spinner = GradientSpinner(
        diameter=120,
        text="Laen",     # base text, dots will be added
        sub_text="Palun oota",  # second line
        border_thickness=10,
        border_color=QColor(63, 249, 220),
        dots_enabled=True,
        dots_interval_ms=350,
    )
    layout.addWidget(spinner, alignment=Qt.AlignCenter)
    spinner.start()

    window.resize(300, 300)
    window.show()

    sys.exit(app.exec_())