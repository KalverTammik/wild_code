from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QGraphicsColorizeEffect,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QColor

from .theme_manager import ThemeManager
from ..constants.file_paths import ResourcePaths, QssPaths
from ..utils.animation import AnimationController

# Optional i18n manager at module top
try:
    from wild_code.languages.language_manager import LanguageManager
except Exception:  # pragma: no cover
    LanguageManager = None


class DevControlsWidget(QWidget):
    """Compact Dev controls cluster for the header.

    Emits:
      - toggleDebugRequested(bool)
      - toggleFrameLabelsRequested(bool)
    """

    toggleDebugRequested = pyqtSignal(bool)
    toggleFrameLabelsRequested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Effect and animation handles
        self._glow = None
        self._dbg_glow_anim_group = None
        self._dbg_colorize = None
        self._dbg_colorize_anim_group = None
        self._frames_colorize = None
        self._frames_colorize_anim_group = None

        # Internal frame for styling hooks
        self._frame = QFrame(self)
        self._frame.setObjectName("headerDevFrame")
        layout = QHBoxLayout(self._frame)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)
        self._frame.setMinimumSize(QSize(90, 30))

        # DEV tag
        self.devTag = QLabel("DEV", self._frame)
        self.devTag.setObjectName("headerDevTag")
        layout.addWidget(self.devTag, 0, Qt.AlignVCenter)

        # Debug toggle
        self.debugBtn = QPushButton("DBG", self._frame)
        self.debugBtn.setObjectName("headerDevToggleButton")
        self.debugBtn.setCheckable(True)
        # i18n tooltips
        if LanguageManager is not None:
            try:
                _lm = LanguageManager()
                self.debugBtn.setToolTip(_lm.translations.get("dev_dbg_tooltip", "dev_dbg_tooltip"))
            except Exception:
                self.debugBtn.setToolTip("dev_dbg_tooltip")
        else:
            self.debugBtn.setToolTip("dev_dbg_tooltip")
        self.debugBtn.setFixedHeight(26)
        self.debugBtn.setMinimumWidth(36)
        self.debugBtn.toggled.connect(self.toggleDebugRequested.emit)
        layout.addWidget(self.debugBtn, 0, Qt.AlignVCenter)

        # Frame labels toggle
        # Themed icon (fallback to resource eye icon)
        try:
            themed_eye = ThemeManager.get_qicon(ResourcePaths.EYE_ICON)
        except Exception:
            themed_eye = None
        eye_icon = themed_eye if themed_eye and not themed_eye.isNull() else QIcon(ResourcePaths.EYE_ICON)
        self.framesBtn = QPushButton(self._frame)
        self.framesBtn.setObjectName("headerFrameLabelsButton")
        self.framesBtn.setCheckable(True)
        if not eye_icon.isNull():
            self.framesBtn.setIcon(eye_icon)
        if LanguageManager is not None:
            try:
                _lm2 = LanguageManager()
                self.framesBtn.setToolTip(_lm2.translations.get("dev_frames_tooltip", "dev_frames_tooltip"))
            except Exception:
                self.framesBtn.setToolTip("dev_frames_tooltip")
        else:
            self.framesBtn.setToolTip("dev_frames_tooltip")
        self.framesBtn.setFixedHeight(26)
        self.framesBtn.setMinimumWidth(36)
        self.framesBtn.setIconSize(QSize(16, 16))
        self.framesBtn.toggled.connect(self.toggleFrameLabelsRequested.emit)
        self.framesBtn.toggled.connect(self._on_local_frames_toggled)
        layout.addWidget(self.framesBtn, 0, Qt.AlignVCenter)

        # Root layout
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._frame, 0, Qt.AlignVCenter)

        # Glow effect
        self._glow = QGraphicsDropShadowEffect(self._frame)
        self._glow.setBlurRadius(16)
        self._glow.setXOffset(0)
        self._glow.setYOffset(0)
        self._glow.setColor(QColor(255, 140, 0, 150))
        self._frame.setGraphicsEffect(self._glow)

        # Colorize effects
        self._dbg_colorize = QGraphicsColorizeEffect(self.debugBtn)
        self._dbg_colorize.setColor(QColor(255, 94, 0))
        self._dbg_colorize.setStrength(0.0)
        self.debugBtn.setGraphicsEffect(self._dbg_colorize)

        self._frames_colorize = QGraphicsColorizeEffect(self.framesBtn)
        self._frames_colorize.setColor(QColor(0, 200, 255))
        self._frames_colorize.setStrength(0.0)
        self.framesBtn.setGraphicsEffect(self._frames_colorize)

        # Controller for centralized animation state
        self._anim = AnimationController(
            owner=self,
            glow_effect=self._glow,
            dbg_effect=self._dbg_colorize,
            frames_effect=self._frames_colorize,
        )

        ThemeManager.apply_module_style(self, [QssPaths.DEV_CONTROLS])
        self.debugBtn.toggled.connect(self._on_local_debug_toggled)

    def _on_local_debug_toggled(self, checked: bool):
        # Centralized animation control
        self._anim.apply_state(bool(checked), self.framesBtn.isChecked())

    # Legacy local animation methods removed; controller handles visuals

    def _on_local_frames_toggled(self, checked: bool):
        # Centralized animation control
        self._anim.apply_state(self.debugBtn.isChecked(), bool(checked))

    # Legacy animation implementations removed in favor of AnimationController

    def set_states(self, debug_enabled: bool, frames_enabled: bool):
        """Initialize/update the checked states without re-emitting side-effects."""
        try:
            prev = self.debugBtn.blockSignals(True)
            self.debugBtn.setChecked(bool(debug_enabled))
            self.debugBtn.blockSignals(prev)

            prev2 = self.framesBtn.blockSignals(True)
            self.framesBtn.setChecked(bool(frames_enabled))
            self.framesBtn.blockSignals(prev2)

            # Apply visuals via centralized controller
            self._anim.apply_state(bool(debug_enabled), bool(frames_enabled))
        except Exception:
            pass

    def retheme(self):
        try:
            ThemeManager.apply_module_style(self, [QssPaths.DEV_CONTROLS])
            # Refresh themed icon in case theme changed
            try:
                # Use the eye icon; ThemeManager will resolve a themed variant if available
                themed_eye = ThemeManager.get_qicon(ResourcePaths.EYE_ICON)
                if themed_eye and not themed_eye.isNull():
                    self.framesBtn.setIcon(themed_eye)
            except Exception:
                pass
        except Exception:
            pass

    def closeEvent(self, event):
        """Ensure animations/effects are stopped and cleaned up on close."""
        try:
            # Centralized stop/cleanup
            if hasattr(self, "_anim") and self._anim is not None:
                self._anim.stop_all()
        finally:
            try:
                super().closeEvent(event)
            except Exception:
                pass
