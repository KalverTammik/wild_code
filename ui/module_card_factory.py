from __future__ import annotations

from ..utils.url_manager import Module


class ModuleCardFactory:
    @staticmethod
    def create_item_card(item, module_name=None, lang_manager=None):
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QGridLayout

        from ..widgets.DataDisplayWidgets.ContactsWidget import ContactsWidget
        from ..widgets.DataDisplayWidgets.PriorityWidget import PriorityWidget
        from ..widgets.DataDisplayWidgets.StatusWidget import StatusWidget
        from ..widgets.DataDisplayWidgets.MembersView import MembersView
        from ..widgets.DataDisplayWidgets.ExtraInfoWidget import ExtraInfoFrame
        from ..widgets.DataDisplayWidgets.InfoCardHeader import InfocardHeaderFrame
        from ..widgets.DataDisplayWidgets.DatesWidget import DatesWidget
        from ..widgets.DataDisplayWidgets.ModuleConnectionActions import ModuleConnectionActions
        from ..widgets.theme_manager import IntensityLevels, styleExtras, ThemeShadowColors
        from ..widgets.theme_manager import ThemeManager
        from ..constants.file_paths import QssPaths

        item_data = dict(item or {})
        card = QFrame()
        card.setObjectName("ModuleInfoCard")

        shadow_color = ThemeShadowColors.GRAY
        styleExtras.apply_chip_shadow(
            element=card,
            color=shadow_color,
            blur_radius=15,
            x_offset=1,
            y_offset=2,
            alpha_level=IntensityLevels.EXTRA_HIGH,
        )

        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(6)

        content = QFrame()
        content.setObjectName("CardContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        header_row = QGridLayout()
        header_row.setContentsMargins(0, 2, 0, 2)
        header_row.setHorizontalSpacing(2)
        header_row.setColumnStretch(0, 1)

        item_id = item_data.get("id")
        if item_id is None:
            raise ValueError("Module feed items must include an 'id' field")
        pos = 0

        header_frame = InfocardHeaderFrame(item_data, module_name=module_name, lang_manager=lang_manager)
        header_row.addWidget(header_frame, 0, pos, Qt.AlignVCenter)

        pos_next = pos + 1

        dates_widget = DatesWidget(
            item_data,
            parent=card,
            lang_manager=lang_manager,
        )
        header_row.addWidget(dates_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next += 1

        actions_widget = ModuleConnectionActions(
            module_name,
            item_id,
            item_data,
            lang_manager=lang_manager,
        )
        header_row.addWidget(actions_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)
        header_row.setColumnStretch(pos_next, 0)
        header_row.setColumnMinimumWidth(pos_next, actions_widget.sizeHint().width())

        pos_next += 1

        members_view = MembersView(item_data)
        if members_view:
            members_view.setFixedWidth(100)
            header_row.addWidget(members_view, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next += 1

        priority_widget = PriorityWidget(item_data, parent=card, lang_manager=lang_manager)
        if not priority_widget.isHidden():
            header_row.addWidget(priority_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)
            pos_next += 1

        status_widget_header = StatusWidget(item_data)
        if status_widget_header:
            header_row.addWidget(status_widget_header, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        cl.addLayout(header_row)

        contacts_widget = ContactsWidget(item_data, parent=content)
        if not contacts_widget.isHidden():
            cl.addWidget(contacts_widget, 0, Qt.AlignLeft)

        show_extra_info = module_name not in (Module.WORKS.value, Module.ASBUILT.value)
        if show_extra_info:
            cl.addWidget(ExtraInfoFrame(item_id, module_name, lang_manager=lang_manager))
        main.addWidget(content, 1)

        ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
        return card

    @staticmethod
    def create_card(item, lang_manager):
        from ..module_manager import ModuleManager

        module_manager = ModuleManager()
        module_name = module_manager.getActiveModuleName()
        return ModuleCardFactory.create_item_card(
            item,
            module_name=module_name,
            lang_manager=lang_manager,
        )
