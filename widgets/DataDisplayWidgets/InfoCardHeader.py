from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy
)

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
        self.setMinimumHeight(16)

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
    def __init__(self, item_data, parent=None, compact=False, module_name=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setProperty("compact", compact)
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

        if not item_data.get('isPublic'):
            privateIcon = QLabel(); privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip("Privaatne")
            try:
                pm = QPixmap(MiscIcons.ICON_IS_PRIVATE)
                if not pm.isNull():
                    privateIcon.setPixmap(pm.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    privateIcon.setText("P")
            except Exception:
                privateIcon.setText("P")
            privateIcon.setFixedSize(14, 14)
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)
        
        number = item_data.get('number', '-')
        if number and number != '-':
            numberBadge = QLabel(str(number))
            numberBadge.setObjectName("ProjectNumberBadge")
            numberBadge.setAlignment(Qt.AlignCenter); 
            numberBadge.setMinimumWidth(24 if not compact else 20)
            numberBadge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        name = item_data.get('name', 'No Name') or 'No Name'
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
            clientRow.setSpacing(6) 
            clientIcon = QLabel("👤")
            clientIcon.setObjectName("ClientIcon")
            clientIcon.setFixedWidth(16 if not compact else 14) 
            clientRow.addWidget(clientIcon, 0, Qt.AlignVCenter)

            clientLabel = QLabel(client) 
            clientLabel.setObjectName("ProjectClientLabel")  
            clientRow.addWidget(clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)

