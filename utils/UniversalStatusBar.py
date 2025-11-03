from PyQt5.QtCore import Qt, QCoreApplication, QPoint
from PyQt5.QtWidgets import (
    QWidget, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
)
from PyQt5.QtGui import (
    QFont, QPalette, QColor, QPainter, QPixmap, QBrush, QPainterPath
)
from typing import Optional
import sys
import os

# Handle imports for both standalone and plugin usage
import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

try:
    from widgets.theme_manager import ThemeManager
    from constants.file_paths import QssPaths
except ImportError as e:
    print(f"Import error in UniversalStatusBar: {e}")
    # Re-raise to make the error visible
    raise



# --- FrostedGlassFrame -------------------------------------------------

class FrostedGlassFrame(QFrame):
    """Hägustatud (frosted) klaasi efektiga frame, mille allolev sisu paistab läbi."""
    def __init__(self, blur_radius=16,
                 tint=QColor(20, 22, 26, 120),
                 radius=7,
                 border_color=QColor(77,77,77,160),
                 parent=None):
        super().__init__(parent)
        self.blur_radius = blur_radius
        self.tint = tint
        self.radius = radius
        self.border_color = border_color
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def _grab_under(self) -> QPixmap:
        if not self.window() or not self.window().windowHandle():
            return QPixmap()
        scr = self.window().windowHandle().screen()
        gpos = self.mapToGlobal(QPoint(0, 0))
        dpr = scr.devicePixelRatio()
        px = scr.grabWindow(0, gpos.x(), gpos.y(), self.width(), self.height())
        px.setDevicePixelRatio(dpr)
        return px

    def _blur_pixmap(self, px: QPixmap) -> QPixmap:
        if px.isNull() or self.blur_radius <= 0:
            return px
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(px)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(self.blur_radius)
        item.setGraphicsEffect(blur)
        scene.addItem(item)
        out = QPixmap(px.size())
        out.fill(Qt.transparent)
        painter = QPainter(out)
        scene.render(painter)
        painter.end()
        return out

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform, True)

        rect = self.rect()
        path = QPainterPath()
        adjusted_rect = rect.adjusted(1,1,-1,-1)
        path.addRoundedRect(adjusted_rect.x(), adjusted_rect.y(), adjusted_rect.width(), adjusted_rect.height(), self.radius, self.radius)

        painter.setClipPath(path)

        base = self._grab_under()
        base = self._blur_pixmap(base)
        if not base.isNull():
            painter.drawPixmap(0, 0, base)

        painter.fillPath(path, QBrush(self.tint))

        pen = painter.pen()
        pen.setColor(self.border_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

        painter.end()


# --- UniversalStatusBar ------------------------------------------------

class UniversalStatusBar:
    """
    Klaasja taustaga universaalne staatusriba.
    Progress + teated, lohistatav päis. Light-teemas parem loetavus.
    """
    active_instances = set()

    def __init__(self,
                 title: str = "Processing...",
                 initial_value: int = 0,
                 maximum: int = 100,
                 stay_on_top: bool = True,
                 width: int = 400,
                 height: int = 130,
                 theme: str = None):
        self.title = title
        self.maximum = maximum
        self.stay_on_top = stay_on_top
        self.width = width
        self.height = height
        self.current_theme = theme if theme is not None else 'light'
        self.canceled = False  # Add cancellation flag
        
        self.widget = self._build_ui()
        self.progress_bar = self.widget.findChild(QProgressBar, "progressBar")
        self.title_label = self.widget.findChild(QLabel, "titleLabel")
        self.main_label = self.widget.findChild(QLabel, "mainLabel")
        self.text1_label = self.widget.findChild(QLabel, "text1Label")
        self.text2_label = self.widget.findChild(QLabel, "text2Label")

        self.progress_bar.setValue(initial_value)
        self.progress_bar.setMaximum(maximum)
        self.title_label.setText(title)

        self.main_label.hide()
        self.text1_label.hide()
        self.text2_label.hide()

        self.drag_pos = None
        # Simple drag functionality - just set cursor
        self.title_frame.setCursor(Qt.OpenHandCursor)

        flags = Qt.FramelessWindowHint | Qt.Tool
        if stay_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.widget.setWindowFlags(flags)

        self.widget.setAttribute(Qt.WA_TranslucentBackground)
        self.widget.setAttribute(Qt.WA_DeleteOnClose)

        # Enable mouse tracking for drag functionality
        self.widget.setMouseTracking(True)

        UniversalStatusBar.active_instances.add(self)
        self.widget.show()

    # ---------- helpers ----------
    @staticmethod
    def _add_text_shadow(label: QLabel, color=QColor(255, 255, 255, 200), blur=6):
        """Lisa kerge hele vari (kasulik light-teemas)."""
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(blur)
        sh.setOffset(0, 0)
        sh.setColor(color)
        label.setGraphicsEffect(sh)

    def _apply_theme_styling(self, widget: QWidget, theme: str = None):
        """Apply theme-aware styling using the centralized ThemeManager."""
        try:
            from ..constants.file_paths import StylePaths
            theme_dir = StylePaths.DARK if theme == 'dark' else StylePaths.LIGHT
            ThemeManager.apply_theme(widget, theme_dir, [QssPaths.UNIVERSAL_STATUS_BAR])
        except Exception as e:
            # Fallback if theming system is not available
            pass


    # ---------- build ----------
    def _build_ui(self) -> QWidget:
        widget = QWidget()
        widget.setFixedSize(self.width, self.height)
        widget.setObjectName("UniversalStatusBar")

        # Apply current theme styling
        self._apply_theme_styling(widget, self.current_theme)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(1)

        # Title bar
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_frame.setFrameStyle(QFrame.NoFrame)
        title_frame.setFixedHeight(30)  # Reduce title bar height
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(5, 1, 5, 1)

        title_label = QLabel(self.title)
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)

        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        layout.addWidget(title_frame)

        # Store reference to title_frame for drag functionality
        self.title_frame = title_frame

        # Frosted content area with theme-appropriate tint
        if self.current_theme == 'dark':
            tint = QColor(20, 22, 26, 120)      # Dark tint
            border = QColor(77, 77, 77, 160)
        else:
            tint = QColor(240, 240, 240, 210)   # Light tint for better contrast
            border = QColor(200, 200, 200, 200)

        content_frame = FrostedGlassFrame(
            blur_radius=16,
            tint=tint,
            radius=7,
            border_color=border
        )
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(8)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0,0,0,140) if self.current_theme=='dark' else QColor(0,0,0,90))
        content_frame.setGraphicsEffect(shadow)

        # Labels
        main_label = QLabel("")
        main_label.setObjectName("mainLabel")
        main_label.setWordWrap(True)
        content_layout.addWidget(main_label)

        progress_bar = QProgressBar()
        progress_bar.setObjectName("progressBar")
        progress_bar.setFixedHeight(15)
        content_layout.addWidget(progress_bar)

        text1_label = QLabel("")
        text1_label.setObjectName("text1Label")
        text1_label.setWordWrap(True)
        content_layout.addWidget(text1_label)

        text2_label = QLabel("")
        text2_label.setObjectName("text2Label")
        text2_label.setWordWrap(True)
        content_layout.addWidget(text2_label)

        layout.addWidget(content_frame)

        # Add text shadows for light theme readability
        if self.current_theme == 'light':
            self._add_text_shadow(main_label, QColor(255,255,255,220), blur=8)
            self._add_text_shadow(text1_label, QColor(255,255,255,200), blur=6)
            self._add_text_shadow(text2_label, QColor(255,255,255,200), blur=6)

        return widget

    # ---------- style ----------

    # ---------- API ----------
    def update(self, value: Optional[int] = None,
               maximum: Optional[int] = None,
               purpose: Optional[str] = None,
               text1: Optional[str] = None,
               text2: Optional[str] = None):
        if self.progress_bar:
            if value is not None:
                self.progress_bar.setValue(value)
            if maximum is not None:
                self.progress_bar.setMaximum(maximum)
        if purpose is not None and self.main_label:
            self.main_label.setText(purpose)
            self.main_label.show()
        if text1 is not None and self.text1_label:
            self.text1_label.setText(text1)
            self.text1_label.show()
        if text2 is not None and self.text2_label:
            self.text2_label.setText(text2)
            self.text2_label.show()
        QCoreApplication.processEvents()

    def close(self):
        self.canceled = True  # Set cancellation flag when closed
        if self.widget:
            self.widget.hide()
            UniversalStatusBar.active_instances.discard(self)
            self.widget.setParent(None)
            self.widget.deleteLater()
            self.widget = None
        QCoreApplication.processEvents()

    def wasCanceled(self):
        """Check if the progress dialog was canceled/closed by user (Qt-style naming)"""
        return self.canceled

    def mousePressEvent(self, event):
        """Simple drag start"""
        if self.title_frame and self.title_frame.geometry().contains(event.pos()) and event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.widget.frameGeometry().topLeft()
            self.title_frame.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Simple drag move"""
        if self.drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.widget.move(event.globalPos() - self.drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Simple drag end"""
        if event.button() == Qt.LeftButton and self.drag_pos is not None:
            self.drag_pos = None
            self.title_frame.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def get_current_theme(self) -> str:
        return self.current_theme

    @staticmethod
    def get_available_themes() -> list:
        return ['dark', 'light']

    @staticmethod
    def close_all():
        for instance in list(UniversalStatusBar.active_instances):
            instance.close()

    @classmethod
    def create_simple(cls, title: str = "Loading...", maximum: int = 100, theme: str = 'dark') -> 'UniversalStatusBar':
        return cls(title=title, maximum=maximum, theme=theme)

    @classmethod
    def create_with_message(cls, title: str, message: str, maximum: int = 100, theme: str = 'dark') -> 'UniversalStatusBar':
        instance = cls(title=title, maximum=maximum, theme=theme)
        instance.update(purpose=message)
        return instance
