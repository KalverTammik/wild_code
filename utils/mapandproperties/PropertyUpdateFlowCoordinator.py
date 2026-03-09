from PyQt5.QtCore import QSignalBlocker, QTimer

from ...languages.translation_keys import TranslationKeys
from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ...utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ...languages.language_manager import LanguageManager 
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.MapTools.MapHelpers import MapHelpers
from ...constants.layer_constants import IMPORT_PROPERTY_TAG

class PropertyUpdateFlowCoordinator:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """

    _LARGE_SCOPE_ROW_THRESHOLD = 8000
    _last_loaded_scope_key = None
    _last_loaded_scope_rows = 0
    _map_update_request_id = 0

    @staticmethod
    def _normalize_text(value) -> str:
        return str(value or "").strip()

    @staticmethod
    def _scope_key(*, county_name=None, municipality_name=None, settlements=None):
        county = PropertyUpdateFlowCoordinator._normalize_text(county_name)
        municipality = PropertyUpdateFlowCoordinator._normalize_text(municipality_name)
        cleaned_settlements = sorted({str(v).strip() for v in (settlements or []) if str(v).strip()})
        return (county, municipality, tuple(cleaned_settlements))

    @staticmethod
    def _reset_scope_cache() -> None:
        PropertyUpdateFlowCoordinator._last_loaded_scope_key = None
        PropertyUpdateFlowCoordinator._last_loaded_scope_rows = 0
        PropertyUpdateFlowCoordinator._map_update_request_id += 1

    @staticmethod
    def _remember_loaded_scope(table, scope_key) -> None:
        PropertyUpdateFlowCoordinator._last_loaded_scope_key = scope_key
        PropertyUpdateFlowCoordinator._last_loaded_scope_rows = PropertyTableManager.row_count(table)

    @staticmethod
    def _should_reuse_loaded_scope(table, scope_key) -> bool:
        if scope_key != PropertyUpdateFlowCoordinator._last_loaded_scope_key:
            return False
        current_rows = PropertyTableManager.row_count(table)
        if current_rows <= 0:
            return False
        if int(PropertyUpdateFlowCoordinator._last_loaded_scope_rows or 0) < PropertyUpdateFlowCoordinator._LARGE_SCOPE_ROW_THRESHOLD:
            return False
        return True

    @staticmethod
    def _schedule_latest_map_update(callback) -> None:
        PropertyUpdateFlowCoordinator._map_update_request_id += 1
        request_id = PropertyUpdateFlowCoordinator._map_update_request_id

        def _run_if_latest() -> None:
            if request_id != PropertyUpdateFlowCoordinator._map_update_request_id:
                return
            try:
                callback()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="property_filter_scheduled_map_update_failed",
                )

        QTimer.singleShot(0, _run_if_latest)

    @staticmethod
    def _zoom_to_scope(*, county_name=None, municipality_name=None, settlements=None) -> None:
        layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if layer is None or not layer.isValid():
            return

        expression = PropertyDataLoader.build_scope_expression(
            county_name=county_name,
            municipality_name=municipality_name,
            settlements=settlements,
        )
        if not expression:
            return

        try:
            MapHelpers.zoom_to_expression_scope(
                layer,
                expression,
                padding_factor=1.12,
                make_active=True,
                clear_selection=True,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="property_filter_scope_zoom_failed",
            )

    @staticmethod
    def _refresh_map_selection_for_scope(*, county_name=None, municipality_name=None, settlements=None) -> None:
        layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if layer is None or not layer.isValid():
            return

        expression = PropertyDataLoader.build_scope_expression(
            county_name=county_name,
            municipality_name=municipality_name,
            settlements=settlements,
        )
        if not expression:
            return

        try:
            MapHelpers.select_and_zoom_to_expression_scope(
                layer,
                expression,
                padding_factor=1.12,
                make_active=True,
                clear_existing=True,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="property_filter_scope_zoom_failed",
            )


    @staticmethod
    def load_county_combo(county_combo, layer):
        """Load data from the property layer"""

        # Load counties using data loader
        counties = PropertyDataLoader().load_counties(layer)

        # Populate county dropdown (avoid emitting signals during repopulation)
        blocker = QSignalBlocker(county_combo)
        try:
            county_combo.clear()
            county_combo.addItem(LanguageManager().translate(TranslationKeys.SELECT_COUNTY), "")

            for county in counties:
                county_combo.addItem(county, county)
        finally:
            del blocker

    @staticmethod
    def on_county_changed(county_name, municipality_combo, city_combo, table, *, after_table_update=None):
        """Handle county selection change."""
        
        if not municipality_combo or not PropertyTableManager():
            return  # UI not fully initialized yet

        # County scope changed -> reset settlement scope immediately for clarity.
        if city_combo is not None:
            city_blocker = QSignalBlocker(city_combo)
            try:
                city_combo.clear()
                city_combo.setEnabled(False)
                city_combo.update()
            finally:
                del city_blocker
            
        if not county_name or county_name == LanguageManager().translate(TranslationKeys.SELECT_COUNTY):
            #block table signals for performance
            table.blockSignals(True)
            # Clear municipality dropdown
            blocker = QSignalBlocker(municipality_combo)
            try:
                municipality_combo.clear()
                municipality_combo.addItem(LanguageManager().translate(TranslationKeys.SELECT_MUNICIPALITY), "")
                municipality_combo.setEnabled(False)
            finally:
                del blocker
            # Clear properties table
            PropertyTableManager().populate_properties_table([], table)
            table.blockSignals(False)
            try:
                if callable(after_table_update):
                    after_table_update(table)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="property_table_after_update_failed",
                )
            PropertyUpdateFlowCoordinator._reset_scope_cache()
            return

        # Load municipalities for selected county
        municipalities = PropertyDataLoader().load_municipalities_for_county(county_name)

        # Populate municipality dropdown
        blocker = QSignalBlocker(municipality_combo)
        try:
            municipality_combo.clear()
            municipality_combo.addItem(LanguageManager().translate(TranslationKeys.SELECT_MUNICIPALITY), "")
            for municipality in municipalities:
                municipality_combo.addItem(municipality, municipality)
            municipality_combo.setEnabled(True)
        finally:
            del blocker

        # Clear stale rows from previous county scope.
        table.blockSignals(True)
        PropertyTableManager().populate_properties_table([], table)
        table.blockSignals(False)
        try:
            if callable(after_table_update):
                after_table_update(table)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_after_update_failed",
            )

        PropertyUpdateFlowCoordinator._reset_scope_cache()

        should_zoom_county_scope = len(municipalities) != 1
        if should_zoom_county_scope:
            PropertyUpdateFlowCoordinator._zoom_to_scope(county_name=county_name)

    @staticmethod
    def on_municipality_changed(municipality_name, county_combo, municipality_combo, city_combo, table, *, after_table_update=None):
        """Handle municipality selection change"""
            
        if not municipality_name or municipality_name == LanguageManager().translate(TranslationKeys.SELECT_MUNICIPALITY):
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
            try:
                if callable(after_table_update):
                    after_table_update(table)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="property_table_after_update_failed",
                )
            county_name = county_combo.currentData() if county_combo is not None else ""
            PropertyUpdateFlowCoordinator._reset_scope_cache()
            PropertyUpdateFlowCoordinator._zoom_to_scope(county_name=county_name)
            return

        # Load settlements for selected municipality
        county_name = county_combo.currentData()
        municipality_name = municipality_combo.currentData()

        PropertyUpdateFlowCoordinator._schedule_latest_map_update(
            lambda cn=county_name, mn=municipality_name: PropertyUpdateFlowCoordinator._zoom_to_scope(
                county_name=cn,
                municipality_name=mn,
            )
        )

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
        # Load properties for selected municipality (avoid duplicate heavy reloads for unchanged large scopes)
        scope_key = PropertyUpdateFlowCoordinator._scope_key(
            county_name=county_name,
            municipality_name=municipality_name,
            settlements=None,
        )
        if not PropertyUpdateFlowCoordinator._should_reuse_loaded_scope(table, scope_key):
            properties = PropertyDataLoader().load_properties_for_municipality(county_name, municipality_name)
            PropertyTableManager().populate_properties_table(properties, table)
            PropertyUpdateFlowCoordinator._remember_loaded_scope(table, scope_key)
        try:
            if callable(after_table_update):
                after_table_update(table)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_after_update_failed",
            )
   
    @staticmethod
    def on_city_changed(
        table=None,
        county_combo=None,
        municipality_combo=None,
        city_combo=None,
        *,
        after_table_update=None,
        update_map: bool = True,
    ):
        """Handle settlement/city selection change"""
            
        # Get checked settlements

        checked_settlements = city_combo.checkedItems()
        if not checked_settlements:
            # No settlements selected - show all properties for the municipality
            county_name = county_combo.currentData()
            municipality_name = municipality_combo.currentData()
            if county_name and municipality_name:
                if update_map:
                    PropertyUpdateFlowCoordinator._schedule_latest_map_update(
                        lambda cn=county_name, mn=municipality_name: PropertyUpdateFlowCoordinator._refresh_map_selection_for_scope(
                            county_name=cn,
                            municipality_name=mn,
                        )
                    )
                scope_key = PropertyUpdateFlowCoordinator._scope_key(
                    county_name=county_name,
                    municipality_name=municipality_name,
                    settlements=None,
                )
                if not PropertyUpdateFlowCoordinator._should_reuse_loaded_scope(table, scope_key):
                    properties = PropertyDataLoader().load_properties_for_municipality(county_name, municipality_name)
                    table.blockSignals(True)
                    PropertyTableManager().populate_properties_table(properties, table)
                    table.blockSignals(False)
                    PropertyUpdateFlowCoordinator._remember_loaded_scope(table, scope_key)
                try:
                    if callable(after_table_update):
                        after_table_update(table)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="property_table_after_update_failed",
                    )
                return

        # Load properties for selected settlements
        county_name = county_combo.currentData()
        municipality_name = municipality_combo.currentData()
        if update_map:
            selected_settlements = list(checked_settlements or [])
            PropertyUpdateFlowCoordinator._schedule_latest_map_update(
                lambda cn=county_name, mn=municipality_name, st=selected_settlements: PropertyUpdateFlowCoordinator._refresh_map_selection_for_scope(
                    county_name=cn,
                    municipality_name=mn,
                    settlements=st,
                )
            )
        scope_key = PropertyUpdateFlowCoordinator._scope_key(
            county_name=county_name,
            municipality_name=municipality_name,
            settlements=checked_settlements,
        )
        if not PropertyUpdateFlowCoordinator._should_reuse_loaded_scope(table, scope_key):
            all_properties = PropertyDataLoader().load_properties_for_settlements(
                county_name,
                municipality_name,
                checked_settlements,
            )
            table.blockSignals(True)
            PropertyTableManager().populate_properties_table(all_properties, table)
            table.blockSignals(False)
            PropertyUpdateFlowCoordinator._remember_loaded_scope(table, scope_key)
        try:
            if callable(after_table_update):
                after_table_update(table)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_after_update_failed",
            )
    
 