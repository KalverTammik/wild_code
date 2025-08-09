
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt
import datetime
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import StylePaths, QssPaths


class ModuleFeedBuilder:
    @staticmethod
    def add_items_to_feed(module_instance, items):
        """
        Adds item cards to the feed layout of the given module instance.
        Handles all UI updates after adding cards.
        Uses centralized ThemeManager.apply_module_style for card theming.
        """
        for item in items:
            card = ModuleFeedBuilder.create_item_card(item)
            # Centralized theming for card
            from ..widgets.theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            module_instance.feed_layout.addWidget(card)
        module_instance.feed_content.updateGeometry()
        module_instance.feed_content.adjustSize()
        module_instance.feed_content.show()
        module_instance.scroll_area.updateGeometry()
        module_instance.scroll_area.adjustSize()
        module_instance.scroll_area.show()
        module_instance.widget.updateGeometry()
        module_instance.widget.adjustSize()
        module_instance.widget.show()

    @staticmethod
    def retheme_cards_in_layout(layout):
        """
        Re-applies the universal card theme to all ModuleInfoCard widgets in the given layout using centralized theming.
        """
        from PyQt5.QtWidgets import QFrame
        from ..widgets.theme_manager import ThemeManager
        from ..constants.file_paths import QssPaths
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QFrame) and widget.objectName() == "ModuleInfoCard":
                widget.setStyleSheet("")
                ThemeManager.apply_module_style(widget, [QssPaths.MODULE_CARD])
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()

    @staticmethod
    def create_item_card(item):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("ModuleInfoCard")
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_frame = InfocardHeaderFrame(item)
        header_row.addWidget(header_frame, alignment=Qt.AlignTop)
        header_row.addStretch(1)
        members_widget = MembersWidget(item)
        header_row.addWidget(members_widget, alignment=Qt.AlignRight | Qt.AlignTop)
        content_layout.addLayout(header_row)
        extra_info_frame = ExtraInfoFrame(item)
        content_layout.addWidget(extra_info_frame)
        main_layout.addWidget(content_frame)
        status_widget = StatusWidget(item, None)
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(status_widget, alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main_layout.addLayout(status_col)
        return card
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_frame = InfocardHeaderFrame(item)
        header_row.addWidget(header_frame, alignment=Qt.AlignTop)
        header_row.addStretch(1)
        members_widget = MembersWidget(item)
        header_row.addWidget(members_widget, alignment=Qt.AlignRight | Qt.AlignTop)
        content_layout.addLayout(header_row)
        extra_info_frame = ExtraInfoFrame(item)
        content_layout.addWidget(extra_info_frame)
        main_layout.addWidget(content_frame)
        status_widget = StatusWidget(item, None)
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(status_widget, alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main_layout.addLayout(status_col)
        return card

class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        name_client_frame = QFrame()
        name_client_layout = QVBoxLayout(name_client_frame)
        name_client_layout.setContentsMargins(0, 0, 0, 0)
        name = item_data.get('name', 'No Name')
        number = item_data.get('number', '-')
        name_label = QLabel(f"<b>{name}</b> <span class='project-number'>#{number}</span>")
        name_label.setTextFormat(Qt.RichText)
        name_label.setObjectName("ProjectNameLabel")
        name_client_layout.addWidget(name_label)
        client = item_data.get('client')
        if client:
            client_label = QLabel(f"<b>Klient:</b> <span class='client-name'>{client['displayName']}</span>")
            client_label.setTextFormat(Qt.RichText)
            client_label.setObjectName("ProjectClientLabel")
            name_client_layout.addWidget(client_label)
        name_client_frame.setLayout(name_client_layout)
        layout.addWidget(name_client_frame)

class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        extra_info_widget = ExtraInfoWidget(item_data)
        layout.addWidget(extra_info_widget)

class MembersWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        members = item_data.get('members', {}).get('edges', [])
        responsible_list = []
        participants_list = []
        for m in members:
            node = m.get('node', {})
            name = node.get('displayName', '-')
            responsible = m.get('isResponsible')
            deleted = node.get('deletedAt')
            classes = []
            if responsible:
                classes.append('responsible')
            if deleted:
                classes.append('deleted')
            class_str = ' '.join(classes)
            if responsible:
                responsible_list.append(f"<span class='{class_str}'>{name}</span>")
            else:
                participants_list.append(f"<span class='{class_str}'>{name}</span>")
        resp_label = QLabel(f"<b>Vastutaja:</b> {', '.join(responsible_list) if responsible_list else '-'}")
        resp_label.setTextFormat(Qt.RichText)
        resp_label.setObjectName("ProjectResponsibleLabel")
        part_label = QLabel(f"<b>Osalejad:</b> {', '.join(participants_list) if participants_list else '-'}")
        part_label.setTextFormat(Qt.RichText)
        part_label.setObjectName("ProjectParticipantsLabel")
        layout.addWidget(resp_label)
        layout.addWidget(part_label)

class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("<i>Lisaandmed tulevad siia...</i>")
        label.setTextFormat(Qt.RichText)
        layout.addWidget(label)

class StatusWidget(QWidget):
    def __init__(self, item_data, theme=None, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if not item_data.get('isPublic'):
            pub_label = QLabel("!")
            pub_label.setObjectName("ProjectPrivateIcon")
            row.addWidget(pub_label)
        status = item_data.get('status', {})
        status_name = status.get('name', '-')
        status_color = status.get('color', 'cccccc')
        status_label = QLabel(status_name)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setFixedWidth(100)
        status_label.setObjectName("ProjectStatusLabel")
        status_label.setProperty("statusColor", status_color)
        row.addWidget(status_label)
        row.addStretch(1)
        main_layout.addLayout(row)
        dates_widget = DatesWidget(item_data)
        main_layout.addWidget(dates_widget)

class DatesWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        def format_date(label, value, due=False):
            if not value:
                return f"<b>{label}:</b> -"
            try:
                dt = datetime.datetime.fromisoformat(value)
                today = datetime.datetime.now().date()
                date_str = dt.strftime('%d.%m.%Y')
                style = ""
                if due:
                    days_left = (dt.date() - today).days
                    if days_left < 0:
                        style = "color:#e53935;font-weight:bold;"  # Red for overdue
                    elif days_left <= 3:
                        style = "color:#ff9800;font-weight:bold;"  # Orange for due soon
                return f"<b>{label}:</b> <span style='{style}'>{date_str}</span>"
            except Exception:
                return f"<b>{label}:</b> {value}"
        date_items = [
            ("Algus", item_data.get('startAt'), False),
            ("Tähtaeg", item_data.get('dueAt'), True),
            ("Loodud", item_data.get('createdAt'), False),
            ("Muudetud", item_data.get('updatedAt'), False),
        ]
        for label, value, due in date_items:
            lbl = QLabel(format_date(label, value, due))
            lbl.setTextFormat(Qt.RichText)
            layout.addWidget(lbl)
        layout.addStretch(1)
