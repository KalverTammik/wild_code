from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor
from typing import Dict
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths

class TagsWidget(QWidget):
    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.setObjectName("TagsWidget")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)                     # room between pills

        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
        names = [n.strip() for n in names if isinstance(n, str) and n.strip()]

        if not names:
            self.setVisible(False)
            return

        # Determine current theme for shadow color selection
        try:
            _theme = ThemeManager.load_theme_setting()
        except Exception:
            _theme = 'light'
        is_dark = (_theme == 'dark')

        for n in names:
            # Outer holder (transparent) to host the shadow
            holder = QFrame(self)
            holder.setObjectName("TagPillHolder")
            holder.setFrameShape(QFrame.NoFrame)
            holder.setAttribute(Qt.WA_StyledBackground, False)  # keep transparent
            holder.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            hL = QHBoxLayout(holder)
            # Margins create space INSIDE holder where blur can appear
            shadow_pad = 4
            hL.setContentsMargins(shadow_pad, shadow_pad, shadow_pad, shadow_pad)
            hL.setSpacing(0)

            # Inner colored pill (styled via QSS)
            pill = QFrame(holder)
            pill.setObjectName("TagPill")
            pill.setProperty("role", "tag")
            pill.setFrameShape(QFrame.NoFrame)
            pill.setAttribute(Qt.WA_StyledBackground, True)
            pill.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            pl = QHBoxLayout(pill)
            pl.setContentsMargins(6, 2, 6, 2)               # inner padding of the capsule
            pl.setSpacing(0)

            lbl = QLabel(n, pill)
            lbl.setObjectName("TagPillLabel")
            lbl.setTextInteractionFlags(Qt.NoTextInteraction)
            # rely on QSS for visuals (no inline stylesheet)
            pl.addWidget(lbl, 0, Qt.AlignVCenter)

            hL.addWidget(pill, 0, Qt.AlignVCenter)

            # Shadow/glow on the holder, so it can render around the pill
            eff = QGraphicsDropShadowEffect(holder)
            eff.setBlurRadius(14)
            eff.setOffset(0, 2)
            eff.setColor(QColor(255,255,255,70) if is_dark else QColor(0,0,0,70))
            holder.setGraphicsEffect(eff)

            row.addWidget(holder, 0, Qt.AlignVCenter)

        # Apply Light/Dark pills QSS via ThemeManager (affects TagPill + label)
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])
        self.setVisible(True)

    def retheme(self):
        """Re-apply QSS and update shadow colors according to current theme."""
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])
        try:
            theme = ThemeManager.load_theme_setting()
        except Exception:
            theme = 'light'
        is_dark = (theme == 'dark')
        new_color = QColor(255,255,255,70) if is_dark else QColor(0,0,0,70)
        for holder in self.findChildren(QFrame, "TagPillHolder"):
            eff = holder.graphicsEffect()
            if isinstance(eff, QGraphicsDropShadowEffect):
                eff.setColor(new_color)

    @staticmethod
    def retheme_in(container: QWidget):
        for w in container.findChildren(TagsWidget):
            w.retheme()
