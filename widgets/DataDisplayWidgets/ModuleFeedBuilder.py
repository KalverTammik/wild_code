from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QPushButton
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame
from .InfoCardHeader import InfocardHeaderFrame
from ..theme_manager import ThemeManager, Theme, is_dark, IntensityLevels, styleExtras, ThemeShadowColors


"""ModuleFeedBuilder

Responsibility: build card widgets only.
Insertion, theming, counter updates handled elsewhere (e.g., ModuleBaseUI).
"""


# ================== Module Feed ==================
class ModuleFeedBuilder:

    @staticmethod
    def create_item_card(item, module_name=None, lang_manager=None):
        card = QFrame()
        card.setObjectName("ModuleInfoCard")

        # Real drop shadow (subtle)
        shadow_color = ThemeShadowColors.GRAY
        styleExtras.apply_chip_shadow(
            element=card, 
            color=shadow_color, 
            blur_radius=10, 
            x_offset=1, 
            y_offset=2,
            alpha_level=IntensityLevels.EXTRA_HIGH
            )


        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(6)

        # Left content
        content = QFrame()
        content.setObjectName("CardContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        header_row = QGridLayout()
        header_row.setContentsMargins(0, 2, 0, 2)
        header_row.setHorizontalSpacing(6)
        header_row.setVerticalSpacing(2)

        # Header takes available space, members view stays compact on right
        header_frame = InfocardHeaderFrame(item, module_name=module_name)
        header_row.addWidget(header_frame, 0, 0, 2, 1)
        header_row.setColumnStretch(0, 1)
        header_row.setRowStretch(1, 1)

        # Add three smaller buttons between header and members view
        button1 = QPushButton("")
        button1.setObjectName("ActionButton1")
        # Prevent button from being triggered by Return key
        button1.setAutoDefault(False)
        button1.setDefault(False)
        button1.setFixedSize(20, 18)
        button1.setToolTip("Action Button 1")
        header_row.addWidget(button1, 0, 1, Qt.AlignTop)

        button2 = QPushButton("")
        button2.setObjectName("ActionButton2")
        # Prevent button from being triggered by Return key
        button2.setAutoDefault(False)
        button2.setDefault(False)
        button2.setFixedSize(20, 18)
        button2.setToolTip("Action Button 2")
        header_row.addWidget(button2, 0, 2, Qt.AlignTop)

        button3 = QPushButton("")
        button3.setObjectName("ActionButton3")
        # Prevent button from being triggered by Return key
        button3.setAutoDefault(False)
        button3.setDefault(False)
        button3.setFixedSize(20, 18)
        button3.setToolTip("Action Button 3")
        header_row.addWidget(button3, 0, 3, Qt.AlignTop)

        # Members view with optimized width for responsible avatars + card stacking
        members_view = MembersView(item)
        members_view.setFixedWidth(100)  # Increased width for responsible avatars
        header_row.addWidget(members_view, 0, 4, 2, 1, Qt.AlignRight | Qt.AlignTop)

        cl.addLayout(header_row)

        item_id = item['id']
        cl.addWidget(ExtraInfoFrame(item_id, module_name))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.setSpacing(8)  # Consistent spacing

        # Status widget at top
        status_widget = StatusWidget(item, show_private_icon=False, lang_manager=lang_manager)
        status_col.addWidget(status_widget, 0, Qt.AlignTop | Qt.AlignRight)

        # Add stretch to push status to top
        status_col.addStretch(1)

        main.addLayout(status_col)
        return card

