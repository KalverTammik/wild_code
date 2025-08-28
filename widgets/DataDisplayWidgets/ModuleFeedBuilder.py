from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame
from .InfoCardHeader import InfocardHeaderFrame
"""ModuleFeedBuilder

Responsibility: build card widgets only.
Insertion, theming, counter updates handled elsewhere (e.g., ModuleBaseUI).
"""


# ================== Module Feed ==================
class ModuleFeedBuilder:
    @staticmethod
    def _item_has_tags(item_data: dict) -> bool:
        try:
            names = ModuleFeedBuilder._extract_tag_names(item_data)
            return len(names) > 0
        except Exception:
            return False

    @staticmethod
    def _extract_tag_names(item_data: dict):
        tags_edges = ((item_data or {}).get('tags') or {}).get('edges') or []
        names = [((e or {}).get('node') or {}).get('name') for e in tags_edges]
        names = [n.strip() for n in names if isinstance(n, str) and n.strip()]
        return names

    @staticmethod
    def create_item_card(item, module_name=None):
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        card.setProperty("compact", False)

        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # Left content
        content = QFrame()
        content.setObjectName("CardContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        # Header takes available space, members view stays compact on right
        header_frame = InfocardHeaderFrame(item, module_name=module_name)
        header_row.addWidget(header_frame, 1)  # Header expands

        # Members view with fixed width to prevent layout shifts
        members_view = MembersView(item)
        members_view.setFixedWidth(120)  # Fixed width for consistent alignment
        header_row.addWidget(members_view, 0, Qt.AlignRight | Qt.AlignTop)

        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(8)  # Consistent spacing

        # Status widget at top
        status_widget = StatusWidget(item, show_private_icon=False)
        status_col.addWidget(status_widget, 0, Qt.AlignTop | Qt.AlignRight)

        # Add stretch to push status to top
        status_col.addStretch(1)

        main.addLayout(status_col)

        # Real drop shadow (subtle)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        # Set theme-appropriate shadow color
        try:
            from ..theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting() if hasattr(ThemeManager, 'load_theme_setting') else 'light'
            shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)
        except Exception:
            shadow_color = QColor(0, 0, 0, 120)  # default to dark shadow
        shadow.setColor(shadow_color)
        card.setGraphicsEffect(shadow)

        return card

    # Legacy add_items_to_feed shim removed (use progressive insertion at UI level)


