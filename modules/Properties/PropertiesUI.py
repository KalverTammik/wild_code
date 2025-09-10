from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...constants.module_names import USER_SETTINGS_MODULE

class PropertiesUI(QWidget):
    """
    Properties management module - handles property-related workflows
    including SHP file loading from Maa-Amet.
    """

    # Signal to switch to user settings module
    switchToUserSettings = pyqtSignal(str)

    def __init__(self, lang_manager=None, theme_manager=None):
        super().__init__()
        self.name = "PropertiesModule"

        # Language manager
        self.lang_manager = lang_manager or LanguageManager()

        # Setup UI
        self.setup_ui()

        # Apply theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

    def setup_ui(self):
        """Setup the properties management interface."""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # Header
        header_label = QLabel("Kinnistud")
        header_label.setObjectName("ModuleHeader")
        header_label.setAlignment(Qt.AlignCenter)
        root.addWidget(header_label)

        # Description
        desc_label = QLabel("Halda kinnistute andmeid ja töövooge")
        desc_label.setObjectName("ModuleDescription")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        root.addWidget(desc_label)

        # Scrollable area for action buttons
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for buttons
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)

        # Action buttons
        self.create_action_buttons(button_layout)

        scroll_area.setWidget(button_container)
        root.addWidget(scroll_area)

    def create_action_buttons(self, layout):
        """Create buttons for different property-related actions."""

        # Load SHP File button
        load_shp_btn = self.create_action_button(
            "Laadi SHP fail",
            "Laadi kinnistute andmed SHP failist",
            self.load_shp_file
        )
        layout.addWidget(load_shp_btn)

        # View Properties button
        view_btn = self.create_action_button(
            "Vaata kinnistuid",
            "Sirvi olemasolevaid kinnistute kihte",
            self.view_properties
        )
        layout.addWidget(view_btn)

        # Import from Database button
        import_btn = self.create_action_button(
            "Impordi andmebaasist",
            "Laadi kinnistute andmed andmebaasist",
            self.import_from_database
        )
        layout.addWidget(import_btn)

        # Export Properties button
        export_btn = self.create_action_button(
            "Ekspordi kinnistuid",
            "Ekspordi kinnistute andmed faili",
            self.export_properties
        )
        layout.addWidget(export_btn)

        # User Settings button
        user_settings_btn = self.create_action_button(
            "Kasutaja seaded",
            "Isiklikud seaded kinnistute haldamiseks",
            self.open_user_settings
        )
        layout.addWidget(user_settings_btn)

        # Add spacer at the end
        layout.addStretch()

    def create_action_button(self, title, description, callback):
        """Create a styled action button with title and description."""
        button_frame = QFrame()
        button_frame.setObjectName("ActionButtonFrame")
        button_frame.setFrameStyle(QFrame.StyledPanel)

        frame_layout = QVBoxLayout(button_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("ActionButtonTitle")
        frame_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("ActionButtonDescription")
        desc_label.setWordWrap(True)
        frame_layout.addWidget(desc_label)

        # Make the frame clickable
        button_frame.mousePressEvent = lambda event: callback()

        return button_frame

    def load_shp_file(self):
        """Handle SHP file loading - moved from direct button click."""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            from ...engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders

            # Show file dialog for SHP files
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.lang_manager.translate("select_shp_file") or "Vali SHP fail",
                "",
                "SHP files (*.shp);;All files (*.*)"
            )

            if not file_path:
                return  # User cancelled

            # Get the layer creation engine
            engine = get_layer_engine()

            # Load SHP file as memory layer
            from qgis.core import QgsVectorLayer
            layer_name = file_path.split('/')[-1].replace('.shp', '')
            shp_layer = QgsVectorLayer(file_path, layer_name, 'ogr')

            if not shp_layer.isValid():
                QMessageBox.warning(
                    self,
                    self.lang_manager.translate("invalid_shp") or "Vigane SHP fail",
                    self.lang_manager.translate("invalid_shp_message") or "Valitud SHP fail ei ole kehtiv."
                )
                return

            # Create memory layer from SHP
            result = engine.copy_virtual_layer_for_properties(
                f"{layer_name}_memory",
                MailablGroupFolders.IMPORT,
                shp_layer
            )

            if result:
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("shp_loaded") or "SHP fail laaditud",
                    self.lang_manager.translate("shp_loaded_message") or f"SHP fail '{layer_name}' on edukalt laaditud grupis '{MailablGroupFolders.IMPORT}'"
                )
            else:
                QMessageBox.warning(
                    self,
                    self.lang_manager.translate("shp_load_failed") or "SHP laadimine ebaõnnestus",
                    self.lang_manager.translate("shp_load_failed_message") or "SHP faili laadimine ebaõnnestus."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                self.lang_manager.translate("error") or "Viga",
                self.lang_manager.translate("shp_loading_error") or f"SHP faili laadimisel tekkis viga: {str(e)}"
            )

    def view_properties(self):
        """Handle viewing existing properties."""
        # TODO: Implement property viewing functionality
        # For now, show available property layers
        try:
            from qgis.core import QgsProject
            from PyQt5.QtWidgets import QMessageBox

            project = QgsProject.instance()
            layers = project.mapLayers().values()

            property_layers = []
            for layer in layers:
                if layer.customProperty("property_layer") or "kinnistu" in layer.name().lower():
                    property_layers.append(layer.name())

            if property_layers:
                layer_list = "\n".join(f"• {name}" for name in property_layers)
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("Available Property Layers") or "Saadaolevad kinnistute kihid",
                    self.lang_manager.translate("Found the following property layers:") or
                    f"Leiti järgmised kinnistute kihid:\n\n{layer_list}"
                )
            else:
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("No Property Layers") or "Kinnistute kihte pole",
                    self.lang_manager.translate("No property layers found. Please load a property layer first.") or
                    "Kinnistute kihte ei leitud. Palun laadi esmalt kinnistute kiht."
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error") or "Viga",
                self.lang_manager.translate("Failed to check for property layers.") or
                f"Kinnistute kihtide kontrollimine ebaõnnestus: {str(e)}"
            )

    def import_from_database(self):
        """Handle importing properties from database."""
        # TODO: Implement database import functionality
        QMessageBox.information(
            self,
            self.lang_manager.translate("Database Import") or "Andmebaasi import",
            self.lang_manager.translate("Database import functionality will be available in a future update.") or
            "Andmebaasi importimise funktsionaalsus on tulevases versioonis saadaval."
        )

    def export_properties(self):
        """Handle exporting properties."""
        # TODO: Implement property export functionality
        QMessageBox.information(
            self,
            self.lang_manager.translate("Export Properties") or "Ekspordi kinnistuid",
            self.lang_manager.translate("Property export functionality will be available in a future update.") or
            "Kinnistute eksportimise funktsionaalsus on tulevases versioonis saadaval."
        )

    def open_user_settings(self):
        """Open user settings module."""
        self.switchToUserSettings.emit(USER_SETTINGS_MODULE)

    def activate(self):
        """Called when the module becomes active."""
        pass

    def deactivate(self):
        """Called when the module becomes inactive."""
        pass

    def get_widget(self):
        """Return the module's main QWidget."""
        return self
