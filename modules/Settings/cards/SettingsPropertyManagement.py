# PropertyManagement.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)
from qgis.core import QgsProject

from .SettingsBaseCard import SettingsBaseCard
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....utils.SHPLayerLoader import SHPLayerLoader
from ....utils.MapTools.MapHelpers import MapHelpers
from ....widgets.AddUpdatePropertyDialog import AddPropertyDialog
from ....modules.Property.FlowControllers.MainDeleteProperties import DeletePropertyUI
from ....languages.translation_keys import TranslationKeys
from ....languages.language_manager import LanguageManager
from ....constants.settings_keys import SettingsService
from ....utils.url_manager import Module


class PropertyManagementUI(SettingsBaseCard):
    def __init__(self, lang_manager: LanguageManager):
        super().__init__(
            lang_manager,
            lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT),
            None,
        )

        self._project = QgsProject.instance()

        cw = self.content_widget()
        main_layout = QVBoxLayout(cw)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # --- buttons row ---
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        self.btn_add_shp = QPushButton(
            self.lang_manager.translate(TranslationKeys.ADD_SHP_FILE),
            cw,
        )
        self.btn_add_property = QPushButton(
            self.lang_manager.translate(TranslationKeys.ADD_PROPERTY),
            cw,
        )
        self.btn_remove_property = QPushButton(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY),
            cw,
        )

        self.btn_add_shp.clicked.connect(self._handle_file_import)
        self.btn_add_property.clicked.connect(self._on_add_property_clicked)
        self.btn_remove_property.clicked.connect(self._on_remove_property_clicked)

        self.btn_add_shp.setObjectName("ConfirmButton")
        self.btn_add_property.setObjectName("ConfirmButton")
        self.btn_remove_property.setObjectName("ConfirmButton")

        btn_row.addWidget(self.btn_add_shp)
        btn_row.addWidget(self.btn_add_property)
        btn_row.addWidget(self.btn_remove_property)
        btn_row.addStretch(1)

        main_layout.addLayout(btn_row)

        # Initial state
        self._update_button_states()

    def hideEvent(self, event):
        """Clean up when widget is hidden"""
        super().hideEvent(event)

    def showEvent(self, event):
        """Update button states when widget becomes visible"""
        super().showEvent(event)

    # ---------- Button Handlers ----------
    def _on_add_shp_clicked(self):
        """Handle Add SHP file button click"""
        self._handle_file_import()



    def _on_property_added(self, property_data):
        """Handle when a property is successfully added"""
        print(f"Property added: {property_data}")
        # Here you can add logic to save the property data
        # For now, just emit the original signal
        self.addPropertyClicked.emit()

    def _on_remove_property_clicked(self):
        """Handle Remove property button click"""
        DeletePropertyUI(self)

    def _on_add_property_clicked(self):
        """Handle Add property button click"""
        AddPropertyDialog(self)


    def _handle_file_import(self):
        """Handle file import for property data using existing SHPLayerLoader"""
        # Use the existing SHPLayerLoader for proper import functionality
        loader = SHPLayerLoader(self)
        success = loader.load_shp_layer()
        if success:
            self._update_button_states()
            pass
        else:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Import Failed") or "Import ebaõnnestus",
                self.lang_manager.translate("Failed to import property file.") or
                "Kinnistute faili import ebaõnnestus.",
                QMessageBox.Ok
            )
            

    
    
    def _update_button_states(self):
        """
        Internal logic that reads layers and applies the enabled/disabled states
        using the pure helper.
        """
        # 1) Discover layers
        main_layer_name = SettingsService().module_main_layer_name(
            Module.PROPERTY.name.lower()
        )
        main_layer = MapHelpers.find_layer_by_name(main_layer_name)
        shp_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)

        main_exists = main_layer is not None
        shp_exists = shp_layer is not None

        # 2) Compute state using helper
        shp_en, add_en, rem_en = LayerChecker.compute_property_button_states(
            main_exists,
            shp_exists,
        )

        # 3) Apply to buttons
        self.btn_add_shp.setEnabled(shp_en)
        self.btn_add_property.setEnabled(add_en)
        self.btn_remove_property.setEnabled(rem_en) 


class LayerChecker:    
    @staticmethod
    def compute_property_button_states(main_layer_exists: bool, shp_layer_exists: bool):
        """
        Return a tuple (shp_enabled, add_prop_enabled, remove_prop_enabled)
        based purely on whether layers exist.
        """
        # Base rule:
        # - SHP import button: always enabled (user can always try to import)
        # - Add property: only if BOTH main layer and shp layer exist
        # - Remove property: only if main layer exists
        shp_enabled = True
        add_prop_enabled = main_layer_exists and shp_layer_exists
        remove_prop_enabled = main_layer_exists

        return shp_enabled, add_prop_enabled, remove_prop_enabled