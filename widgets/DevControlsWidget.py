from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsColorizeEffect,
    QSizePolicy,
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
        self._dbg_glow_anim_group = None
        self._dbg_colorize = None
        self._dbg_colorize_anim_group = None
        self._frames_colorize = None
        self._frames_colorize_anim_group = None

        # Root layout (no container frame)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # DEV tag
        self.devTag = QLabel("DEV", self)
        self.devTag.setObjectName("headerDevTag")
        self.devTag.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        root.addWidget(self.devTag, 0, Qt.AlignVCenter)

        # Debug toggle
        self.debugBtn = QPushButton("DBG", self)
        self.debugBtn.setObjectName("headerDevToggleButton")
        self.debugBtn.setCheckable(True)
        # Prevent button from being triggered by Return key
        self.debugBtn.setAutoDefault(False)
        self.debugBtn.setDefault(False)
        if LanguageManager is not None:
            try:
                _lm = LanguageManager()
                self.debugBtn.setToolTip(_lm.translations.get("dev_dbg_tooltip", "dev_dbg_tooltip"))
            except Exception:
                self.debugBtn.setToolTip("dev_dbg_tooltip")
        else:
            self.debugBtn.setToolTip("dev_dbg_tooltip")
        self.debugBtn.setFixedHeight(13)
        self.debugBtn.setMinimumWidth(18)
        self.debugBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.debugBtn.toggled.connect(self.toggleDebugRequested.emit)
        root.addWidget(self.debugBtn, 0, Qt.AlignVCenter)

        # Frame labels toggle
        try:
            themed_eye = ThemeManager.get_qicon(ResourcePaths.EYE_ICON)
        except Exception:
            themed_eye = None
        eye_icon = themed_eye if themed_eye and not themed_eye.isNull() else QIcon(ResourcePaths.EYE_ICON)
        self.framesBtn = QPushButton(self)
        self.framesBtn.setObjectName("headerFrameLabelsButton")
        self.framesBtn.setCheckable(True)
        # Prevent button from being triggered by Return key
        self.framesBtn.setAutoDefault(False)
        self.framesBtn.setDefault(False)
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
        self.framesBtn.setFixedHeight(13)
        self.framesBtn.setMinimumWidth(18)
        self.framesBtn.setIconSize(QSize(12, 12))
        self.framesBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.framesBtn.toggled.connect(self.toggleFrameLabelsRequested.emit)
        self.framesBtn.toggled.connect(self._on_local_frames_toggled)
        root.addWidget(self.framesBtn, 0, Qt.AlignVCenter)
        root.addStretch(1)

        # Effects: both buttons use red colorize effect (blinking when active)
        self._dbg_colorize = QGraphicsColorizeEffect(self.debugBtn)
        self._dbg_colorize.setColor(QColor(255, 0, 0))
        self._dbg_colorize.setStrength(0.0)
        self.debugBtn.setGraphicsEffect(self._dbg_colorize)

        self._frames_colorize = QGraphicsColorizeEffect(self.framesBtn)
        self._frames_colorize.setColor(QColor(255, 0, 0))
        self._frames_colorize.setStrength(0.0)
        self.framesBtn.setGraphicsEffect(self._frames_colorize)

        # Controller for centralized animation state; red pulse on both when active
        self._anim = AnimationController(
            owner=self,
            glow_effect=None,
            dbg_effect=self._dbg_colorize,
            frames_effect=self._frames_colorize,
        )
        # Apply DevControls-specific QSS (theme manager resolves dark/light)
        ThemeManager.apply_module_style(self, [QssPaths.DEV_CONTROLS])
        self.debugBtn.toggled.connect(self._on_local_debug_toggled)

    def _on_local_debug_toggled(self, checked: bool):
        """Local handler to update animations when DBG is toggled."""
        try:
            if hasattr(self, "_anim") and self._anim is not None:
                self._anim.apply_state(debug_on=checked, frames_on=self.framesBtn.isChecked())
        except Exception:
            pass

    def _on_local_frames_toggled(self, checked: bool):
        """Local handler to update animations when Frame Labels is toggled."""
        try:
            if hasattr(self, "_anim") and self._anim is not None:
                self._anim.apply_state(debug_on=self.debugBtn.isChecked(), frames_on=checked)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            if hasattr(self, "_anim") and self._anim is not None:
                self._anim.stop_all()
        except Exception:
            pass
        super().closeEvent(event)
