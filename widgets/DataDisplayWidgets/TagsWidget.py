from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor
from typing import Dict
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths

class CompactTagsWidget(QWidget):
    """Compact tag display showing limited tags with overflow indicator."""

    def __init__(self, item_data: Dict, parent=None, max_visible=3):
        super().__init__(parent)
        self.setObjectName("CompactTagsWidget")
        self.item_data = item_data
        self.max_visible = max_visible

        row = QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)  # no spacing between tags
        row.setMargin(0)  # no margin

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

        # Show limited number of tags
        visible_tags = names[:max_visible]
        overflow_count = len(names) - max_visible

        for n in visible_tags:
            pill = self._create_tag_pill(n, is_dark)
            row.addWidget(pill, 0, Qt.AlignVCenter | Qt.AlignTop)

        # Add overflow indicator if needed
        if overflow_count > 0:
            overflow_pill = self._create_overflow_pill(f"+{overflow_count}", is_dark)
            row.addWidget(overflow_pill, 0, Qt.AlignVCenter | Qt.AlignTop)

        # Apply styling
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])
        self.setVisible(True)

    def _create_tag_pill(self, tag_name: str, is_dark: bool):
        """Create a compact tag pill."""
        # Outer holder for shadow
        holder = QFrame(self)
        holder.setObjectName("CompactTagHolder")
        holder.setFrameShape(QFrame.NoFrame)
        holder.setAttribute(Qt.WA_StyledBackground, False)
        holder.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        holder.setContentsMargins(0, 0, 0, 0)

        hL = QHBoxLayout(holder)
        hL.setContentsMargins(0, 0, 0, 0)  # no margins
        hL.setSpacing(0)
        hL.setMargin(0)

        # Inner colored pill
        pill = QFrame(holder)
        pill.setObjectName("CompactTagPill")
        pill.setProperty("role", "compact_tag")
        pill.setFrameShape(QFrame.NoFrame)
        pill.setAttribute(Qt.WA_StyledBackground, True)
        pill.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        pill.setContentsMargins(0, 0, 0, 0)

        pl = QHBoxLayout(pill)
        pl.setContentsMargins(2, 1, 2, 1)  # minimal padding
        pl.setSpacing(0)
        pl.setMargin(0)

        lbl = QLabel(tag_name, pill)
        lbl.setObjectName("CompactTagLabel")
        lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        lbl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(lbl, 0, Qt.AlignVCenter | Qt.AlignLeft)

        hL.addWidget(pill, 0, Qt.AlignVCenter | Qt.AlignLeft)

        # Shadow effect
        eff = QGraphicsDropShadowEffect(holder)
        eff.setBlurRadius(4)  # minimal blur
        eff.setOffset(0, 1)
        eff.setColor(QColor(255,255,255,50) if is_dark else QColor(0,0,0,50))
        holder.setGraphicsEffect(eff)

        return holder

    def _create_overflow_pill(self, overflow_text: str, is_dark: bool):
        """Create overflow indicator pill."""
        holder = QFrame(self)
        holder.setObjectName("OverflowTagHolder")
        holder.setFrameShape(QFrame.NoFrame)
        holder.setAttribute(Qt.WA_StyledBackground, False)
        holder.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        holder.setContentsMargins(0, 0, 0, 0)

        hL = QHBoxLayout(holder)
        hL.setContentsMargins(0, 0, 0, 0)
        hL.setSpacing(0)
        hL.setMargin(0)

        pill = QFrame(holder)
        pill.setObjectName("OverflowTagPill")
        pill.setProperty("role", "overflow_tag")
        pill.setFrameShape(QFrame.NoFrame)
        pill.setAttribute(Qt.WA_StyledBackground, True)
        pill.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        pill.setContentsMargins(0, 0, 0, 0)

        pl = QHBoxLayout(pill)
        pl.setContentsMargins(1, 1, 1, 1)
        pl.setSpacing(0)
        pl.setMargin(0)

        lbl = QLabel(overflow_text, pill)
        lbl.setObjectName("OverflowTagLabel")
        lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        lbl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(lbl, 0, Qt.AlignVCenter | Qt.AlignLeft)

        hL.addWidget(pill, 0, Qt.AlignVCenter | Qt.AlignLeft)

        # Shadow effect
        eff = QGraphicsDropShadowEffect(holder)
        eff.setBlurRadius(2)
        eff.setOffset(0, 1)
        eff.setColor(QColor(255,255,255,40) if is_dark else QColor(0,0,0,40))
        holder.setGraphicsEffect(eff)

        return holder

    def retheme(self):
        """Re-apply QSS and update shadow colors according to current theme."""
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])
        try:
            theme = ThemeManager.load_theme_setting()
        except Exception:
            theme = 'light'
        is_dark = (theme == 'dark')
        new_color = QColor(255,255,255,50) if is_dark else QColor(0,0,0,50)
        overflow_color = QColor(255,255,255,40) if is_dark else QColor(0,0,0,40)

        for holder in self.findChildren(QFrame, "CompactTagHolder"):
            eff = holder.graphicsEffect()
            if isinstance(eff, QGraphicsDropShadowEffect):
                eff.setColor(new_color)

        for holder in self.findChildren(QFrame, "OverflowTagHolder"):
            eff = holder.graphicsEffect()
            if isinstance(eff, QGraphicsDropShadowEffect):
                eff.setColor(overflow_color)


class TagsWidget(QWidget):
    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.setObjectName("TagsWidget")

        row = QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)  # no spacing between tags
        row.setMargin(0)  # no margin

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
            holder.setContentsMargins(0, 0, 0, 0)
            hL = QHBoxLayout(holder)
            # Margins create space INSIDE holder where blur can appear
            shadow_pad = 0  # no margins
            hL.setContentsMargins(shadow_pad, shadow_pad, shadow_pad, shadow_pad)
            hL.setSpacing(0)
            hL.setMargin(0)

            # Inner colored pill (styled via QSS)
            pill = QFrame(holder)
            pill.setObjectName("TagPill")
            pill.setProperty("role", "tag")
            pill.setFrameShape(QFrame.NoFrame)
            pill.setAttribute(Qt.WA_StyledBackground, True)
            pill.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            pill.setContentsMargins(0, 0, 0, 0)

            pl = QHBoxLayout(pill)
            pl.setContentsMargins(2, 1, 2, 1)               # minimal inner padding
            pl.setSpacing(0)
            pl.setMargin(0)

            lbl = QLabel(n, pill)
            lbl.setObjectName("TagPillLabel")
            lbl.setTextInteractionFlags(Qt.NoTextInteraction)
            lbl.setContentsMargins(0, 0, 0, 0)
            # rely on QSS for visuals (no inline stylesheet)
            pl.addWidget(lbl, 0, Qt.AlignVCenter | Qt.AlignLeft)

            hL.addWidget(pill, 0, Qt.AlignVCenter | Qt.AlignLeft)

            # Shadow/glow on the holder, so it can render around the pill
            eff = QGraphicsDropShadowEffect(holder)
            eff.setBlurRadius(6)
            eff.setOffset(0, 1)
            eff.setColor(QColor(255,255,255,70) if is_dark else QColor(0,0,0,70))
            holder.setGraphicsEffect(eff)

            row.addWidget(holder, 0, Qt.AlignVCenter | Qt.AlignTop)

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
