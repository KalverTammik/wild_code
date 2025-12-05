from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy
)
from ...widgets.theme_manager import ThemeManager
from ...constants.module_icons import MiscIcons
from .TagsWidget import TagsWidget


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setObjectName("ElidedLabel")
        self.setMinimumHeight(12)

    def setText(self, text):
        self._full = text or ""
        super().setText(self._full)
        self._elide()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()

    def _elide(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        super().setText(elided)


class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None, module_name=None):
        super().__init__(parent)
        
        #print("InfocardHeaderFrame item_data:", item_data)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(0)
        self.module_name = module_name or "default"

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # Left column
        left = QFrame(self)
        left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left)
        leftL.setContentsMargins(0, 0, 0, 0)
        leftL.setSpacing(4)

        
        # Name row: conditional layout based on number display setting
        nameRow = QHBoxLayout()
        nameRow.setContentsMargins(0,0,0,0) 
        nameRow.setSpacing(6)

        if item_data.get('isPublic'):
            privateIcon = QLabel(); privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip("Privaatne")
            icon = ThemeManager.get_qicon(MiscIcons.ICON_IS_PRIVATE)
            privateIcon.setPixmap(icon.pixmap(12, 12))
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)
        
        number = item_data.get('number', '-')
        if number and number != '-':
            numberBadge = QLabel(str(number))
            numberBadge.setObjectName("ProjectNumberBadge")
            numberBadge.setAlignment(Qt.AlignCenter)
            numberBadge.setMinimumWidth(24)
            nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        name = item_data.get('name') or item_data.get('jobName') 
        #print("InfocardHeaderFrame name:", name)
        nameLabel = ElidedLabel(name); 
        nameLabel.setObjectName("ProjectNameLabel")  # Eemaldatud tooltip
        nameRow.addWidget(nameLabel, 1, Qt.AlignVCenter)

        tags = TagsWidget._extract_tag_names(item_data)
        if tags:
            nameRow.addWidget(TagsWidget(tags), 0, Qt.AlignVCenter)
        leftL.addLayout(nameRow)

        # Client row (optional)
        client = (item_data.get('client') or {}).get('displayName')
        if client:
            clientRow = QHBoxLayout()
            clientRow.setContentsMargins(0,0,0,0); 
            icon = ThemeManager.get_qicon(MiscIcons.ICON_IS_CLIENT)
            clientRow.setSpacing(6) 
            clientIcon = QLabel(); clientIcon.setPixmap(icon.pixmap(12, 12))
            clientIcon.setObjectName("ClientIcon")
            clientRow.addWidget(clientIcon, 0, Qt.AlignVCenter)

            clientLabel = QLabel(client) 
            clientLabel.setObjectName("ProjectClientLabel")  
            clientRow.addWidget(clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)
