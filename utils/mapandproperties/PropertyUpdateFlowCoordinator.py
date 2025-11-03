from PyQt5.QtWidgets import QMessageBox


class PropertyUpdateFlowCoordinator:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """

    def __init__(self, data_loader, table_manager, county_combo, municipality_combo, city_combo, lang_manager):
        self.data_loader = data_loader
        self.table_manager = table_manager
        self.county_combo = county_combo
        self.municipality_combo = municipality_combo
        self.city_combo = city_combo
        self.lang_manager = lang_manager

    def on_county_changed(self, county_name):
        """Handle county selection change"""
        if not self.municipality_combo or not self.table_manager:
            return  # UI not fully initialized yet
            
        if not county_name or county_name == (self.lang_manager.translate("Select County") or "Vali maakond"):
            # Clear municipality dropdown
            self.municipality_combo.clear()
            self.municipality_combo.addItem(self.lang_manager.translate("Select Municipality") or "Vali omavalitsus", "")
            self.municipality_combo.setEnabled(False)
            # Clear properties table
            self.table_manager.populate_properties_table([])
            return

        # Load municipalities for selected county
        try:
            municipalities = self.data_loader.load_municipalities_for_county(county_name)

            # Populate municipality dropdown
            self.municipality_combo.clear()
            self.municipality_combo.addItem(self.lang_manager.translate("Select Municipality") or "Vali omavalitsus", "")

            for municipality in municipalities:
                self.municipality_combo.addItem(municipality, municipality)

            self.municipality_combo.setEnabled(True)

        except Exception as e:
            parent_widget = self.municipality_combo.parent() if self.municipality_combo else None
            QMessageBox.warning(
                parent_widget,
                self.lang_manager.translate("Data Loading Error") or "Andmete laadimise viga",
                self.lang_manager.translate("Failed to load municipalities from layer.") or
                f"Omavalitsuste laadimine kihist ebaõnnestus: {str(e)}"
            )

    def on_municipality_changed(self, municipality_name):
        """Handle municipality selection change"""
        if not self.table_manager or not self.county_combo or not self.municipality_combo:
            return  # UI not fully initialized yet
            
            
        if not municipality_name or municipality_name == (self.lang_manager.translate("Select Municipality") or "Vali omavalitsus"):
            # Clear city/settlement dropdown
            if self.city_combo is not None:
                self.city_combo.clear()
                self.city_combo.setEnabled(False)
            # Clear properties table
            self.table_manager.populate_properties_table([])
            return

        # Load settlements for selected municipality
        county_name = self.county_combo.currentData()
        municipality_name = self.municipality_combo.currentData()
        try:
            settlements = self.data_loader.load_settlements_for_municipality(county_name, municipality_name)

            # Populate settlement dropdown
            if self.city_combo is not None:
                self.city_combo.clear()
                if settlements:
                    # Add all settlements to the checkable combo box
                    for settlement in settlements:
                        self.city_combo.addItem(settlement)
                    self.city_combo.setEnabled(True)
                else:
                    self.city_combo.setEnabled(False)
                self.city_combo.update()

            # Load properties for selected municipality
            properties = self.data_loader.load_properties_for_municipality(county_name, municipality_name)
            self.table_manager.populate_properties_table(properties)
            #print(f"DEBUG: Loaded {len(properties)} properties")

        except Exception as e:
            print(f"DEBUG: Error in on_municipality_changed: {e}")
            parent_widget = self.municipality_combo.parent() if self.municipality_combo else None
            QMessageBox.warning(
                parent_widget,
                self.lang_manager.translate("Data Loading Error") or "Andmete laadimise viga",
                self.lang_manager.translate("Failed to load settlements and properties from layer.") or
                f"Asustusüksuste ja kinnistute laadimine kihist ebaõnnestus: {str(e)}"
            )

    def on_city_changed(self):
        """Handle settlement/city selection change"""
        if not self.table_manager or not self.county_combo or not self.municipality_combo:
            return  # UI not fully initialized
            
        if self.city_combo is None:
            return
            
        # Get checked settlements
        checked_settlements = self.city_combo.checkedItems()
        
        if not checked_settlements:
            # No settlements selected - show all properties for the municipality
            county_name = self.county_combo.currentData()
            municipality_name = self.municipality_combo.currentData()
            if county_name and municipality_name:
                try:
                    properties = self.data_loader.load_properties_for_municipality(county_name, municipality_name)
                    self.table_manager.populate_properties_table(properties)
                except Exception as e:
                    parent_widget = self.city_combo.parent() if self.city_combo is not None else None
                    QMessageBox.warning(
                        parent_widget,
                        self.lang_manager.translate("Data Loading Error") or "Andmete laadimise viga",
                        self.lang_manager.translate("Failed to load properties from layer.") or
                        f"Kinnistute laadimine kihist ebaõnnestus: {str(e)}"
                    )
            return

        # Load properties for selected settlements
        county_name = self.county_combo.currentData()
        municipality_name = self.municipality_combo.currentData()
        try:
            # Load properties for each selected settlement and combine
            all_properties = []
            for settlement in checked_settlements:
                properties = self.data_loader.load_properties_for_settlement(county_name, municipality_name, settlement)
                all_properties.extend(properties)
            
            self.table_manager.populate_properties_table(all_properties)

        except Exception as e:
            parent_widget = self.city_combo.parent() if self.city_combo is not None else None
            QMessageBox.warning(
                parent_widget,
                self.lang_manager.translate("Data Loading Error") or "Andmete laadimise viga",
                self.lang_manager.translate("Failed to load properties from layer.") or
                f"Kinnistute laadimine kihist ebaõnnestus: {str(e)}"
            )

    def collect_active_selections_from_table(self):
        """Get the selected properties data"""
        
            
        selected_features = self.table_manager.get_selected_features()

        if not selected_features:
            return None

        return selected_features