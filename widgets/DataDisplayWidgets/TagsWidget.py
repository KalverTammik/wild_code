from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor, QFont, QFontMetrics
from typing import Dict
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths

# Import AvatarUtils for consistent coloring
from .MembersView import AvatarUtils


class TagsWidget(QWidget):
    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.setObjectName("TagsWidget")

        # Vertical layout for tags
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)  # Smaller spacing
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
        names = [n.strip() for n in names if isinstance(n, str) and n.strip()]

        if not names:
            # Instead of hiding, show empty widget
            self.setVisible(True)
            return

        # Limit to reasonable number
        max_tags = 5
        visible_tags = names[:max_tags]
        overflow_count = len(names) - max_tags

        for n in visible_tags:
            bubble = self._create_tag_bubble(n)
            layout.addWidget(bubble)

        # Add overflow if needed
        if overflow_count > 0:
            overflow_bubble = self._create_overflow_bubble(f"+{overflow_count}")
            layout.addWidget(overflow_bubble)

        # Apply styling
        ThemeManager.apply_module_style(self, [QssPaths.PILLS])
        self.setVisible(True)

    def _create_tag_bubble(self, tag_name: str):
        """Create a tag bubble similar to AvatarBubble."""
        # Use AvatarBubble-like styling
        size = 18  # Smaller than members
        bg = AvatarUtils.color_for_name(tag_name, salt="tag")
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        bubble = QLabel(self)
        bubble.setText(tag_name)  # Show full name for readability
        bubble.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        f = QFont()
        f.setBold(True)
        f.setPixelSize(11)
        bubble.setFont(f)
        bubble.setToolTip(tag_name)

        # Calculate width based on actual text length
        metrics = QFontMetrics(f)
        text_width = metrics.width(tag_name)
        padding = 6
        bubble.setFixedSize(text_width + 2 * padding, size)

        bubble.setStyleSheet(
            f"background-color: {AvatarUtils.rgb_css(bg)};"
            f"color: {fg_hex};"
            f"border: 1px solid {AvatarUtils.rgb_css(border)};"
            f"border-radius: {size//2}px;"
            f"font-weight: bold;"
            f"font-size: 11px;"
            f"padding: 0px {padding}px;"
        )

        return bubble

    def _create_overflow_bubble(self, overflow_text: str):
        """Create overflow bubble."""
        size = 18
        bg = QColor(150, 150, 150)  # Gray for overflow
        fg_hex = AvatarUtils.fg_for_bg(bg)
        border = AvatarUtils.border_for_bg(bg)

        bubble = QLabel(self)
        bubble.setText(overflow_text)
        bubble.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        f = QFont()
        f.setBold(True)
        f.setPixelSize(11)
        bubble.setFont(f)
        bubble.setToolTip("More tags")

        # Calculate width based on actual text length
        metrics = QFontMetrics(f)
        text_width = metrics.width(overflow_text)
        padding = 6
        bubble.setFixedSize(text_width + 2 * padding, size)

        bubble.setStyleSheet(
            f"background-color: {AvatarUtils.rgb_css(bg)};"
            f"color: {fg_hex};"
            f"border: 1px solid {AvatarUtils.rgb_css(border)};"
            f"border-radius: {size//2}px;"
            f"font-weight: bold;"
            f"font-size: 11px;"
            f"padding: 0px {padding}px;"
        )

        return bubble

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

        # Since we use inline styles, no need to update shadows
        pass
