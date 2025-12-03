from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame
from .InfoCardHeader import InfocardHeaderFrame
from .DatesWidget import DatesWidget
from .ModuleConnectionActions import ModuleConnectionActions
from ..theme_manager import IntensityLevels, styleExtras, ThemeShadowColors

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
            blur_radius=15, 
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
        header_row.setHorizontalSpacing(2)
        header_row.setColumnStretch(0, 1)

        item_id = item.get('id')
        if item_id is None:
            raise ValueError("Module feed items must include an 'id' field")
        pos = 0

        # Header takes available space, other widgets align to the right
        header_frame = InfocardHeaderFrame(item, module_name=module_name)
        header_row.addWidget(header_frame, 0, pos, Qt.AlignVCenter)

        pos_next = pos + 1

        dates_widget = DatesWidget(
            item,
            parent=card,
            compact=False,
            lang_manager=lang_manager,
        )
        header_row.addWidget(dates_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next += 1

        file_path = item.get('filesPath', '')
        properties_conn = item.get('properties') or {}
        page_info = properties_conn.get('pageInfo') or {}
        properties_count = page_info.get('count') or page_info.get('total', 0)

        actions_widget = ModuleConnectionActions(
            module_name,
            item_id,
            file_path,
            bool(properties_count),
            lang_manager=lang_manager,
        )
        header_row.addWidget(actions_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next += 1

        members_view = MembersView(item)
        if members_view:
            members_view.setFixedWidth(100)
            header_row.addWidget(members_view, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next += 1

        status_widget_header = StatusWidget(item)
        if status_widget_header:
            header_row.addWidget(status_widget_header, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item_id, module_name))
        main.addWidget(content, 1)

        # Right status column removed in favour of inline header placement
        return card

