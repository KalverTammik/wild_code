# PropertyManagement.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)

from .BaseCard import BaseCard
from ....utils.UniversalStatusBar import UniversalStatusBar
from ....widgets.theme_manager import ThemeManager


class PropertyManagement(BaseCard):
    """
    Property Management widget for quick actions:
      - Add SHP file
      - Add property
      - Remove property

    Signals:
      addShpClicked() -> emits when Add SHP file button is clicked
      addPropertyClicked() -> emits when Add property button is clicked
      removePropertyClicked() -> emits when Remove property button is clicked
    """
    addShpClicked = pyqtSignal()
    addPropertyClicked = pyqtSignal()
    removePropertyClicked = pyqtSignal()

    def __init__(self, lang_manager):
        super().__init__(lang_manager, lang_manager.translate("Property Management"), None)

        # Create the UI content
        self._create_content()

    def _create_content(self):
        """Create the widget content with buttons"""
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        # ---------- Action buttons row ----------
        buttons_title = QLabel(self.lang_manager.translate("Quick Actions"), cw)
        buttons_title.setObjectName("SetupCardSectionTitle")
        cl.addWidget(buttons_title)

        buttons_container = QFrame(cw)
        buttons_container.setObjectName("ActionButtons")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)

        # Add SHP file button
        self.btn_add_shp = QPushButton(self.lang_manager.translate("Add Shp file"), buttons_container)
        self.btn_add_shp.clicked.connect(self._on_add_shp_clicked)
        buttons_layout.addWidget(self.btn_add_shp)

        # Add property button
        self.btn_add_property = QPushButton(self.lang_manager.translate("Add property"), buttons_container)
        self.btn_add_property.clicked.connect(self._on_add_property_clicked)
        buttons_layout.addWidget(self.btn_add_property)

        # Remove property button
        self.btn_remove_property = QPushButton(self.lang_manager.translate("Remove property"), buttons_container)
        self.btn_remove_property.clicked.connect(self._on_remove_property_clicked)
        buttons_layout.addWidget(self.btn_remove_property)

        buttons_layout.addStretch(1)  # Push buttons to the left
        cl.addWidget(buttons_container)

    def hideEvent(self, event):
        """Clean up when widget is hidden"""
        super().hideEvent(event)

    # ---------- Button Handlers ----------
    def _on_add_shp_clicked(self):
        """Handle Add SHP file button click"""
        self.addShpClicked.emit()

    def _on_add_property_clicked(self):
        """Handle Add property button click"""
        self.addPropertyClicked.emit()

    def _on_remove_property_clicked(self):
        """Handle Remove property button click"""
        self.removePropertyClicked.emit()
