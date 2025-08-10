from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect
)
from .StatusWidget import StatusWidget
from .MembersView import MembersView
from .ExtraInfoWidget import ExtraInfoFrame



# Project imports (adjust paths if needed)
from ..theme_manager import ThemeManager
from ...constants.file_paths import QssPaths



# ================== Module Feed ==================
class ModuleFeedBuilder:
    @staticmethod
    def create_item_card(item):
        print("[ModuleFeedBuilder] Creating item card for:", item)
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        card.setProperty("compact", False)

        main = QHBoxLayout(card)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # Left content
        content = QFrame(); content.setObjectName("CardContent")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(6)

        header_row = QHBoxLayout(); header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(InfocardHeaderFrame(item), alignment=Qt.AlignTop)
        header_row.addStretch(1)
        header_row.addWidget(MembersView(item), alignment=Qt.AlignRight | Qt.AlignTop)
        cl.addLayout(header_row)

        cl.addWidget(ExtraInfoFrame(item))
        main.addWidget(content, 1)

        # Right status column
        status_col = QVBoxLayout(); status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(StatusWidget(item), alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main.addLayout(status_col)

        # Real drop shadow (subtle)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        return card

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
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            module_instance.feed_layout.addWidget(card)
        # Do not call adjustSize(), show(), or updateGeometry() on feed_content, scroll_area, or widget
        # Let Qt's layout system handle resizing and scrolling


# ================== Elided single-line label ==================
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setToolTip(self._full)
        self.setObjectName("ElidedLabel")

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        super().setText(self._full)
        self._elide()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()

    def _elide(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        super().setText(elided)


# ================== Header (name + number + client) ==================
class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, parent=None, compact=False):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setProperty("compact", compact)

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(8 if not compact else 6)

        # Left column
        left = QFrame(self); left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left); leftL.setContentsMargins(0, 0, 0, 0); leftL.setSpacing(2 if not compact else 1)

        name = item_data.get('name', 'No Name') or 'No Name'
        number = item_data.get('number', '-')
        client = (item_data.get('client') or {}).get('displayName')

        # Name row: elided name + pill badge number
        nameRow = QHBoxLayout(); nameRow.setContentsMargins(0,0,0,0); nameRow.setSpacing(8 if not compact else 6)

        self.nameLabel = ElidedLabel(name)
        self.nameLabel.setObjectName("ProjectNameLabel")
        self.nameLabel.setToolTip(name)
        nameRow.addWidget(self.nameLabel, 1, Qt.AlignVCenter)

        self.numberBadge = QLabel(str(number))
        self.numberBadge.setObjectName("ProjectNumberBadge")
        self.numberBadge.setAlignment(Qt.AlignCenter)
        self.numberBadge.setMinimumWidth(36)
        nameRow.addWidget(self.numberBadge, 0, Qt.AlignVCenter)

        leftL.addLayout(nameRow)

        # Client row (optional)
        if client:
            clientRow = QHBoxLayout(); clientRow.setContentsMargins(0,0,0,0); clientRow.setSpacing(6)
            self.clientIcon = QLabel("👤"); self.clientIcon.setObjectName("ClientIcon"); self.clientIcon.setFixedWidth(14)
            clientRow.addWidget(self.clientIcon, 0, Qt.AlignVCenter)

            self.clientLabel = ElidedLabel(client)
            self.clientLabel.setObjectName("ProjectClientLabel")
            self.clientLabel.setToolTip(client)
            clientRow.addWidget(self.clientLabel, 1, Qt.AlignVCenter)

            leftL.addLayout(clientRow)

        root.addWidget(left, 1, Qt.AlignVCenter)


