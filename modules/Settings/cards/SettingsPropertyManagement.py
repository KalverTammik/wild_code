# PropertyManagement.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
)
from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt

from .SettingsBaseCard import SettingsBaseCard
from ....utils.SHPLayerLoader import SHPLayerLoader
from ....widgets.theme_manager import ThemeManager
from ....widgets.AddUpdatePropertyDialog import AddPropertyDialog
from ....constants.layer_constants import PROPERTY_TAG, IMPORT_PROPERTY_TAG
from ....constants.file_paths import QssPaths


class PropertyManagement(SettingsBaseCard):
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

        # Create the UI content first to have the buttons
        self._create_content()
        
        # Initialize modular checker with list of button configs
        self.layer_checker = LayerChecker([
            (self.btn_add_shp, "tag_with_data", (IMPORT_PROPERTY_TAG, 1)),
            (self.btn_add_property, "tag_not_exists", (IMPORT_PROPERTY_TAG,)),
            (self.btn_remove_property, "tag_not_exists", (PROPERTY_TAG,))
        ], self.lang_manager)
        self.layer_checker._connect_project_signals(self)
        # Note: Button states will be updated when the settings panel becomes visible


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

    def showEvent(self, event):
        """Update button states when widget becomes visible"""
        super().showEvent(event)
        self.layer_checker._update_button_states()

    def _on_project_layers_changed(self, layers):
        """Update button states when layers change"""
        self.layer_checker._update_button_states()

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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.lang_manager.translate("No Property Layer Found"))
        msg_box.setText(self.lang_manager.translate("No property layer found with the required tag."))
        msg_box.setInformativeText(self.lang_manager.translate("Would you like to import an existing file or load from the web?"))

        import_button = msg_box.addButton(self.lang_manager.translate("Import File"), QMessageBox.ActionRole)
        load_button = msg_box.addButton(self.lang_manager.translate("Load from Web"), QMessageBox.ActionRole)
        cancel_button = msg_box.addButton(self.lang_manager.translate("Cancel"), QMessageBox.RejectRole)

        # Apply theme to QMessageBox to match parent dialog styling
        ThemeManager.apply_module_style(msg_box, [QssPaths.MAIN])

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
            loader = SHPLayerLoader(self)
            success = loader.load_shp_layer()

            if success:
                # Property tag is already set by SHPLayerLoader
                # Success message is already shown by SHPLayerLoader
                pass
            else:
                msg_box = QMessageBox(QMessageBox.Warning,
                                    self.lang_manager.translate("Import Failed") or "Import ebaõnnestus",
                                    self.lang_manager.translate("Failed to import property file.") or
                                    "Kinnistute faili import ebaõnnestus.",
                                    QMessageBox.Ok,
                                    self)
                ThemeManager.apply_module_style(msg_box, [QssPaths.MAIN])
                msg_box.exec_()

        except Exception as e:
            msg_box = QMessageBox(QMessageBox.Critical,
                                self.lang_manager.translate("Error") or "Viga",
                                self.lang_manager.translate("File import failed") or f"Faili import ebaõnnestus: {str(e)}",
                                QMessageBox.Ok,
                                self)
            ThemeManager.apply_module_style(msg_box, [QssPaths.MAIN])
            msg_box.exec_()

    def _handle_webpage_load(self):
        """Handle webpage loading for property data"""
        try:
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

            # Apply theme to QMessageBox to match parent dialog styling
            ThemeManager.apply_module_style(msg_box, [QssPaths.MAIN])

            msg_box.exec_()

            if msg_box.clickedButton() == open_web_button:
                # TODO: Implement actual webpage opening
                # For now, show a placeholder message
                info_msg = QMessageBox(QMessageBox.Information,
                                     self.lang_manager.translate("Webpage Opening") or "Veebilehe avamine",
                                     self.lang_manager.translate("Webpage opening functionality will be implemented here.") or
                                     "Veebilehe avamise funktsionaalsus lisatakse siia.",
                                     QMessageBox.Ok,
                                     self)
                ThemeManager.apply_module_style(info_msg, [QssPaths.MAIN])
                info_msg.exec_()

                # Placeholder for future implementation:
                # - Open browser to Maa-Amet website
                # - Provide download instructions
                # - Handle downloaded file import

        except Exception as e:
            critical_msg = QMessageBox(QMessageBox.Critical,
                                     self.lang_manager.translate("Error") or "Viga",
                                     self.lang_manager.translate("Web loading failed") or f"Veebilaadimine ebaõnnestus: {str(e)}",
                                     QMessageBox.Ok,
                                     self)
            ThemeManager.apply_module_style(critical_msg, [QssPaths.MAIN])
            critical_msg.exec_()

class LayerChecker:
    """
    Modular class to check layer state for multiple buttons based on different condition types.
    Manages buttons' enabled states dynamically based on layer presence and data.
    """
    
    def __init__(self, button_configs, lang_manager):
        """
        button_configs: List of tuples (button, condition_type, params)
        condition_types:
        - "tag_with_data": (tag_name, min_features) - disable if layer with tag has > min_features
        - "both_tags_exist": (tag1, tag2) - disable if layers with both tags exist
        - "tag_exists": (tag_name,) - disable if layer with tag exists
        - "tag_not_exists": (tag_name,) - disable if no layer with tag exists
        """
        self.button_configs = button_configs
        self.lang_manager = lang_manager

    def _connect_project_signals(self, parent):
        """Connect to QGIS project signals to update button states dynamically"""
        try:
            project = QgsProject.instance()
            if project:
                project.layersAdded.connect(parent._on_project_layers_changed)
                project.layersRemoved.connect(parent._on_project_layers_changed)
        except Exception as e:
            print(f"Warning: Could not connect to project signals: {e}")

    def _update_button_states(self):
        """Enable/disable buttons based on their layer state conditions"""
        try:
            project = QgsProject.instance()
            layers = project.mapLayers()
            
            for button, condition_type, params in self.button_configs:
                condition_met = self._check_condition(condition_type, params, layers)
                should_enable = not condition_met
                if button.isEnabled() != should_enable:
                    button.setEnabled(should_enable)
                tooltip = self._get_tooltip_for_condition(condition_type) if condition_met else ""
                if button.toolTip() != tooltip:
                    button.setToolTip(tooltip)
        except Exception as e:
            print(f"Warning: Could not update button states: {e}")

    def _check_condition(self, condition_type, params, layers):
        """Check if the condition is met based on type and params"""
        if condition_type == "tag_with_data":
            tag_name, min_features = params
            return any(
                layer.customProperty(tag_name) and layer.featureCount() > min_features
                for layer in layers.values()
            )
        elif condition_type == "both_tags_exist":
            tag1, tag2 = params
            has_tag1 = any(layer.customProperty(tag1) for layer in layers.values())
            has_tag2 = any(layer.customProperty(tag2) for layer in layers.values())
            return has_tag1 and has_tag2
        elif condition_type == "tag_exists":
            tag_name = params[0]
            return any(layer.customProperty(tag_name) for layer in layers.values())
        elif condition_type == "tag_not_exists":
            tag_name = params[0]
            return not any(layer.customProperty(tag_name) for layer in layers.values())
        else:
            return False

    def _get_tooltip_for_condition(self, condition_type):
        """Get appropriate tooltip based on condition type"""
        if condition_type == "tag_with_data":
            return self.lang_manager.translate("Import layer with data already exists") or "Import kiht andmetega on juba olemas"
        elif condition_type == "both_tags_exist":
            return self.lang_manager.translate("Both import and property layers exist") or "Nii import kui ka kinnistute kihid on olemas"
        elif condition_type == "tag_exists":
            return self.lang_manager.translate("Property layer exists") or "Kinnistute kiht on olemas"
        elif condition_type == "tag_not_exists":
            return self.lang_manager.translate("No property layer exists") or "Kinnistute kihti pole olemas"
        else:
            return ""