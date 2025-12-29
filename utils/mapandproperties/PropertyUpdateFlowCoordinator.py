from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import QMessageBox

from ...languages.translation_keys import TranslationKeys
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...constants.settings_keys import SettingsService
from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ...utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ...languages.language_manager import LanguageManager 
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.url_manager import Module

class PropertyUpdateFlowCoordinator:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """


    @staticmethod
    def load_county_combo(county_combo, layer):
        """Load data from the property layer"""

        # Load counties using data loader
        counties = PropertyDataLoader().load_counties(layer)

        # Populate county dropdown (avoid emitting signals during repopulation)
        blocker = QSignalBlocker(county_combo)
        try:
            county_combo.clear()
            county_combo.addItem(
                LanguageManager().translate(TranslationKeys.SELECT_COUNTY) or "Vali maakond", "")

            for county in counties:
                county_combo.addItem(county, county)
        finally:
            del blocker

    @staticmethod
    def on_county_changed(county_name, municipality_combo, table):
        """Handle county selection change."""
        
        if not municipality_combo or not PropertyTableManager():
            return  # UI not fully initialized yet
            
        if not county_name or county_name == (LanguageManager().translate("Select County") or "Vali maakond"):
            #block table signals for performance
            table.blockSignals(True)
            # Clear municipality dropdown
            blocker = QSignalBlocker(municipality_combo)
            try:
                municipality_combo.clear()
                municipality_combo.addItem(LanguageManager().translate("Select Municipality") or "Vali omavalitsus", "")
                municipality_combo.setEnabled(False)
            finally:
                del blocker
            # Clear properties table
            PropertyTableManager().populate_properties_table([], table)
            table.blockSignals(False)
            return

        # Load municipalities for selected county
        municipalities = PropertyDataLoader().load_municipalities_for_county(county_name)

        # Populate municipality dropdown
        blocker = QSignalBlocker(municipality_combo)
        try:
            municipality_combo.clear()
            municipality_combo.addItem(LanguageManager().translate("Select Municipality") or "Vali omavalitsus", "")
            for municipality in municipalities:
                municipality_combo.addItem(municipality, municipality)
            municipality_combo.setEnabled(True)
        finally:
            del blocker

    @staticmethod
    def on_municipality_changed(municipality_name, county_combo, municipality_combo, city_combo, table):
        """Handle municipality selection change"""
            
        if not municipality_name or municipality_name == (LanguageManager().translate("Select Municipality") or "Vali omavalitsus"):
            # Clear city/settlement dropdown
            if city_combo is not None:
                blocker = QSignalBlocker(city_combo)
                try:
                    city_combo.clear()
                    city_combo.setEnabled(False)
                finally:
                    del blocker
            # Clear properties table
            table.blockSignals(True)
            PropertyTableManager().populate_properties_table([], table)
            table.blockSignals(False)
            return

        # Load settlements for selected municipality
        county_name = county_combo.currentData()
        municipality_name = municipality_combo.currentData()

        settlements = PropertyDataLoader().load_settlements_for_municipality(county_name, municipality_name)
        # Populate settlement dropdown
        if city_combo is not None:
            blocker = QSignalBlocker(city_combo)
            try:
                city_combo.clear()
                if settlements:
                    # Add all settlements to the checkable combo box
                    for settlement in settlements:
                        city_combo.addItem(settlement)
                    city_combo.setEnabled(True)
                else:
                    city_combo.setEnabled(False)
                city_combo.update()
            finally:
                del blocker
        # Load properties for selected municipality
        properties = PropertyDataLoader().load_properties_for_municipality(county_name, municipality_name)
        result = PropertyTableManager().populate_properties_table(properties, table)
        if result == True:            
            table.selectAll()
   
    @staticmethod
    def on_city_changed(table=None,county_combo=None, municipality_combo=None, city_combo=None):
        """Handle settlement/city selection change"""
            
        # Get checked settlements

        checked_settlements = city_combo.checkedItems()
        print(f"DEBUG: Checked settlements: {checked_settlements}")
        if not checked_settlements:
            # No settlements selected - show all properties for the municipality
            print(f"DEBUG: no settlements selected, loading all properties for municipality")
            county_name = county_combo.currentData()
            municipality_name = municipality_combo.currentData()
            if county_name and municipality_name:
                properties = PropertyDataLoader().load_properties_for_municipality(county_name, municipality_name)
                table.blockSignals(True)
                result = PropertyTableManager().populate_properties_table(properties, table)
                table.blockSignals(False)
                if result == True:
                    table.selectAll()
                return

        # Load properties for selected settlements
        county_name = county_combo.currentData()
        municipality_name = municipality_combo.currentData()
        # Load properties for each selected settlement and combine
        all_properties = []
        for settlement in checked_settlements:
            properties = PropertyDataLoader().load_properties_for_settlement(county_name, municipality_name, settlement)
            all_properties.extend(properties)
        print(f"DEBUG: adding properties for settelments as there was selection")
        table.blockSignals(True)
        result = PropertyTableManager().populate_properties_table(all_properties, table)
        table.blockSignals(False)
        if result == True:
            table.selectAll()
            from ...utils.MapTools.item_selector_tools import PropertiesSelectors
            PropertiesSelectors.show_connected_properties_on_map_from_table(table, use_shp=True)
    
 