from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy
)
from ...widgets.theme_manager import ThemeManager
from ...constants.module_icons import MiscIcons
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.responses import DataDisplayExtractors
from .TagsWidget import TagsWidget


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self._is_eliding = False
        self._pending_elide = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setObjectName("ElidedLabel")
        self.setMinimumHeight(12)

    def setText(self, text):
        self._full = text or ""
        super().setText(self._full)
        self._schedule_elide()

    def resizeEvent(self, e):
        if self._is_eliding:
            super().resizeEvent(e)
            return
        super().resizeEvent(e)
        self._schedule_elide()

    def _schedule_elide(self):
        if self._pending_elide:
            return
        self._pending_elide = True
        try:
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(0, self._elide)
        except Exception:
            self._pending_elide = False
            self._elide()

    def _elide(self):
        if self._pending_elide:
            self._pending_elide = False
        if self._is_eliding:
            return
        if self.width() <= 0:
            return
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        if elided == self.text():
            return
        self._is_eliding = True
        try:
            super().setText(elided)
        finally:
            self._is_eliding = False


class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None, module_name=None):
        super().__init__(parent)
        
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

        if DataDisplayExtractors.extract_is_public(item_data):
            privateIcon = QLabel(); privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip(LanguageManager().translate(TranslationKeys.DATA_DISPLAY_WIDGETS_INFOCARDHEADER_TOOLTIP))
            icon = ThemeManager.get_qicon(MiscIcons.ICON_IS_PRIVATE)
            privateIcon.setPixmap(icon.pixmap(12, 12))
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)
        
        number = DataDisplayExtractors.extract_item_number(item_data) or '-'
        if number and number != '-':
            numberBadge = QLabel(str(number))
            numberBadge.setObjectName("ProjectNumberBadge")
            numberBadge.setAlignment(Qt.AlignCenter)
            numberBadge.setMinimumWidth(24)
            nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        name = DataDisplayExtractors.extract_item_name(item_data)
        nameLabel = ElidedLabel(name); 
        nameLabel.setObjectName("ProjectNameLabel")  # Eemaldatud tooltip
        nameRow.addWidget(nameLabel, 1, Qt.AlignVCenter)

        tags = DataDisplayExtractors.extract_tag_names(item_data)
        if tags:
            nameRow.addWidget(TagsWidget(tags), 0, Qt.AlignVCenter)
        leftL.addLayout(nameRow)

        # Client row (optional)
        client = DataDisplayExtractors.extract_client_display_name(item_data)
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
