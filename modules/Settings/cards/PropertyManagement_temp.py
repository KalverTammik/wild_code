# PropertyManagement.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
)

from .BaseCard import BaseCard
from ....utils.UniversalStatusBar import UniversalStatusBar
from ....widgets.theme_manager import ThemeManager
from ....constants import PROPERTY_TAG


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
        try:
            # Check if any layer has the property tag
            has_property_tag = self._check_for_property_layer_tag()

            if not has_property_tag:
                # Show choice dialog for import vs load
                choice = self._show_import_or_load_choice()
                if choice == "cancel":
                    return  # User cancelled
                elif choice == "import":
                    # Open file import dialog
                    self._handle_file_import()
                    return
                elif choice == "load":
                    # Open webpage for loading (placeholder)
                    self._handle_webpage_load()
                    return

            # If we have property layers or user chose to proceed, open the add property dialog
            # Import the dialog
            from ....widgets.AddPropertyDialog import AddPropertyDialog

            # Create and show the dialog
            dialog = AddPropertyDialog(self)

            # Connect to the property added signal
            dialog.propertyAdded.connect(self._on_property_added)

            # Show the dialog
            dialog.exec_()

        except Exception as e:
            print(f"Error opening add property dialog: {e}")
            # Fallback: emit the original signal
            self.addPropertyClicked.emit()

    def _on_property_added(self, property_data):
        """Handle when a property is successfully added"""
        print(f"Property added: {property_data}")
        # Here you can add logic to save the property data
        # For now, just emit the original signal
        self.addPropertyClicked.emit()

    def _on_remove_property_clicked(self):
        """Handle Remove property button click"""
        self.removePropertyClicked.emit()

    def _check_for_property_layer_tag(self):
        """Check if any layer has the property tag in layer properties"""
        try:
            from qgis.core import QgsProject
            from qgis.PyQt.QtCore import Qt

            project = QgsProject.instance()
            layers = project.mapLayers().values()

            for layer in layers:
                # Check layer custom properties for the tag
                if layer.customProperty(PROPERTY_TAG):
                    return True

            return False

        except Exception as e:
            print(f"Error checking for property layer tag: {e}")
            return False

    def _show_import_or_load_choice(self):
        """Show dialog asking user to choose between import or load"""
        from PyQt5.QtWidgets import QMessageBox

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.lang_manager.translate("No Property Layer Found"))
        msg_box.setText(self.lang_manager.translate("No property layer found with the required tag."))
        msg_box.setInformativeText(self.lang_manager.translate("Would you like to import an existing file or load from the web?"))

        import_button = msg_box.addButton(self.lang_manager.translate("Import File"), QMessageBox.ActionRole)
        load_button = msg_box.addButton(self.lang_manager.translate("Load from Web"), QMessageBox.ActionRole)
        cancel_button = msg_box.addButton(self.lang_manager.translate("Cancel"), QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == import_button:
            return "import"
        elif msg_box.clickedButton() == load_button:
            return "load"
        else:
            return "cancel"

    def _handle_file_import(self):
        """Handle file import for property data using existing SHPLayerLoader"""
        try:
            # Use the existing SHPLayerLoader for proper import functionality
            from ....utils.SHPLayerLoader import SHPLayerLoader

            loader = SHPLayerLoader(self)
            success = loader.load_shp_layer()

            if success:
                # Property tag is already set by SHPLayerLoader
                # Success message is already shown by SHPLayerLoader
                pass
                            QMessageBox.warning(
                    self,
                    self.lang_manager.translate("Import Failed") or "Import ebaõnnestus",
                    self.lang_manager.translate("Failed to import property file.") or
                    "Kinnistute faili import ebaõnnestus."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                self.lang_manager.translate("Error") or "Viga",
                self.lang_manager.translate("File import failed") or f"Faili import ebaõnnestus: {str(e)}"
            )

    def _handle_webpage_load(self):
        """Handle webpage loading for property data"""
        try:
            from PyQt5.QtWidgets import QMessageBox

            # Show information about webpage loading
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.lang_manager.translate("Load from Web") or "Laadi veebist")
            msg_box.setText(self.lang_manager.translate("Web loading functionality is under development.") or
                           "Veebilaadimise funktsionaalsus on arendamisel.")
            msg_box.setInformativeText(
                self.lang_manager.translate("This will open a webpage to download property data from official sources.") or
                "See avab veebilehe kinnistute andmete allalaadimiseks ametlikest allikatest."
            )

            # Add buttons
            open_web_button = msg_box.addButton(
                self.lang_manager.translate("Open Webpage") or "Ava veebileht",
                            QMessageBox.ActionRole
            )
            cancel_button = msg_box.addButton(
                self.lang_manager.translate("Cancel") or "Tühista",
                            QMessageBox.RejectRole
            )

            msg_box.exec_()

            if msg_box.clickedButton() == open_web_button:
                # TODO: Implement actual webpage opening
                # For now, show a placeholder message
                            QMessageBox.information(
                    self,
                    self.lang_manager.translate("Webpage Opening") or "Veebilehe avamine",
                    self.lang_manager.translate("Webpage opening functionality will be implemented here.") or
                    "Veebilehe avamise funktsionaalsus lisatakse siia."
                )

                # Placeholder for future implementation:
                # - Open browser to Maa-Amet website
                # - Provide download instructions
                # - Handle downloaded file import

        except Exception as e:
            QMessageBox.critical(
                self,
                self.lang_manager.translate("Error") or "Viga",
                self.lang_manager.translate("Web loading failed") or f"Veebilaadimine ebaõnnestus: {str(e)}"
            )

    def get_selected_property_layer(self):
        """Get the currently selected property layer for the AddPropertyDialog"""
        try:
            from qgis.core import QgsProject

            project = QgsProject.instance()
            layers = project.mapLayers().values()

            for layer in layers:
                # Check layer custom properties for the tag
                if layer.customProperty(PROPERTY_TAG):
                    return layer

            return None

        except Exception as e:
            print(f"Error getting selected property layer: {e}")
            return None
