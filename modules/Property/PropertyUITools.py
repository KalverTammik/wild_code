from typing import Optional

from PyQt5.QtCore import QThread
from ...constants.cadastral_fields import Katastriyksus
from ...languages.translation_keys import TranslationKeys
from ...constants.settings_keys import SettingsService
from ...utils.url_manager import Module
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from .query_cordinator import (
    PropertiesConnectedElementsQueries,
    PropertyLookupService,
    PropertyConnectionFormatter,
)
from ...python.workers import FunctionWorker, start_worker


class PropertyUITools:

    def __init__(self, property_ui):
        self.property_ui = property_ui
        self._settings = SettingsService()
        self._selection_layer = None
        self._connection_request_id = 0
        self._connection_thread: Optional[QThread] = None
        self._connection_worker: Optional[FunctionWorker] = None

    def _configured_property_layer(self):
        layer_name = self._settings.module_main_layer_id(Module.PROPERTY.value) or ""
        if not layer_name:
            return None
        return MapHelpers.resolve_layer(layer_name)

    def _warn_no_property_layer(self, detail: Optional[str] = None):
        from PyQt5.QtWidgets import QMessageBox
        base = self.property_ui.lang_manager.translate(TranslationKeys.ERROR_SELECTING_PROPERTY)
        message = f"{base}: {detail}" if detail else base
        QMessageBox.warning(
            self.property_ui,
            self.property_ui.lang_manager.translate(TranslationKeys.ERROR),
            message
        )

    def select_property_from_map(self):
        """Activate map selection tool for property selection."""
        try:
            from qgis.utils import iface

            active_layer = self._configured_property_layer()
            if not active_layer:
                self._warn_no_property_layer("Property layer not configured or missing from project")
                return

            iface.setActiveLayer(active_layer)
            MapHelpers.ensure_layer_visible(active_layer)
            active_layer.removeSelection()

            # Ensure previous listeners are detached so we only react once per selection
            self._disconnect_selection_listener()

            # Connect selection changed signal
            active_layer.selectionChanged.connect(self._on_selection_changed)
            self._selection_layer = active_layer

            # Activate selection tool
            iface.actionSelectRectangle().trigger()

            # Emit signal to minimize dialog
            self.property_ui.property_selected_from_map.emit()

        except Exception as e:
            print(f"Error selecting property from map: {e}")
            # Show error message
            self._warn_no_property_layer(str(e))

    def _on_selection_changed(self):
        """Handle selection changes during map selection process."""
        try:
            from qgis.utils import iface

            active_layer = self._selection_layer or iface.activeLayer()
            if not active_layer:
                return
            selected_features = active_layer.selectedFeatures()

            if len(selected_features) == 1:
                # Single feature selected: update display
                self.update_property_display(active_layer)

                # Disconnect the signal
                self._disconnect_selection_listener()

                # Switch back to pan tool
                iface.actionPan().trigger()

                # Emit completion signal to maximize dialog
                self.property_ui.property_selection_completed.emit()
                PropertiesSelectors.bring_dialog_to_front(self.property_ui)

        except Exception as e:
            print(f"Error in selection changed: {e}")
            self._disconnect_selection_listener()

    def _disconnect_selection_listener(self):
        if not self._selection_layer:
            return
        try:
            self._selection_layer.selectionChanged.disconnect(self._on_selection_changed)
        except Exception:
            pass
        finally:
            self._selection_layer = None

    def update_property_display(self, active_layer):
        """Update the UI labels with the selected property data."""

        features = active_layer.selectedFeatures()
        if not features:
            return  # No selection
        feature = features[0]  # Use the first (and assumed only) selected feature
        cadastral_value = None
        try:
            # Update katastritunnus label
            katastritunnus = feature.attribute(Katastriyksus.tunnus)
            if self._is_not_null(katastritunnus):
                cadastral_value = str(katastritunnus)
                self.property_ui.lbl_katastritunnus_value.setText(cadastral_value)
            else:
                self.property_ui.lbl_katastritunnus_value.setText("...")

            # Update address label
            l_address = feature.attribute(Katastriyksus.l_aadress)
            ay_name = feature.attribute(Katastriyksus.ay_nimi)
            mk_name = feature.attribute(Katastriyksus.mk_nimi)
            address_parts = []
            if self._is_not_null(l_address): address_parts.append(str(l_address))
            if self._is_not_null(ay_name): address_parts.append(str(ay_name))
            if self._is_not_null(mk_name): address_parts.append(str(mk_name))
            address = ", ".join(address_parts) if address_parts else "..."
            self.property_ui.lbl_address_value.setText(address)

            # Update area label
            area = feature.attribute(Katastriyksus.pindala)
            self.property_ui.lbl_area_value.setText(str(area) if self._is_not_null(area) else "0.00")

            # Update sihtotstarve labels (3 separate labels, hide if NULL)
            siht1 = feature.attribute(Katastriyksus.siht1)
            siht2 = feature.attribute(Katastriyksus.siht2)
            siht3 = feature.attribute(Katastriyksus.siht3)
            so_prts1 = feature.attribute(Katastriyksus.so_prts1)
            so_prts2 = feature.attribute(Katastriyksus.so_prts2)
            so_prts3 = feature.attribute(Katastriyksus.so_prts3)

            # Siht 1
            if self._is_not_null(siht1):
                formatted_siht1 = str(siht1).lower().capitalize()
                percentage1 = f" {so_prts1}%" if self._is_not_null(so_prts1) else ""
                self.property_ui.lbl_siht1_value.setText(f"{formatted_siht1}{percentage1}")
                self.property_ui.lbl_siht1_label.show()
                self.property_ui.lbl_siht1_value.show()
            else:
                self.property_ui.lbl_siht1_label.hide()
                self.property_ui.lbl_siht1_value.hide()

            # Siht 2
            if self._is_not_null(siht2):
                formatted_siht2 = str(siht2).lower().capitalize()
                percentage2 = f" {so_prts2}%" if self._is_not_null(so_prts2) else ""
                self.property_ui.lbl_siht2_value.setText(f"{formatted_siht2}{percentage2}")
                self.property_ui.lbl_siht2_label.show()
                self.property_ui.lbl_siht2_value.show()
            else:
                self.property_ui.lbl_siht2_label.hide()
                self.property_ui.lbl_siht2_value.hide()

            # Siht 3
            if self._is_not_null(siht3):
                formatted_siht3 = str(siht3).lower().capitalize()
                percentage3 = f" {so_prts3}%" if self._is_not_null(so_prts3) else ""
                self.property_ui.lbl_siht3_value.setText(f"{formatted_siht3}{percentage3}")
                self.property_ui.lbl_siht3_label.show()
                self.property_ui.lbl_siht3_value.show()
            else:
                self.property_ui.lbl_siht3_label.hide()
                self.property_ui.lbl_siht3_value.hide()

            # Update registr (registration date)
            registr = feature.attribute(Katastriyksus.registr)
            if self._is_not_null(registr):
                # Format date if it's a QDate or datetime object
                if hasattr(registr, 'toString'):
                    # QDate object
                    formatted_date = registr.toString("dd.MM.yyyy")
                else:
                    # Try to parse as string/date
                    try:
                        from datetime import datetime
                        if isinstance(registr, str):
                            # Assume YYYY-MM-DD format and convert to DD.MM.YYYY
                            date_obj = datetime.fromisoformat(str(registr).split('T')[0])
                            formatted_date = date_obj.strftime("%d.%m.%Y")
                        else:
                            formatted_date = str(registr)
                    except:
                        formatted_date = str(registr)
                self.property_ui.lbl_registr_value.setText(formatted_date)
            else:
                self.property_ui.lbl_registr_value.setText("...")

            # Update muudet (modification date)
            muudet = feature.attribute(Katastriyksus.muudet)
            if self._is_not_null(muudet):
                # Format date if it's a QDate or datetime object
                if hasattr(muudet, 'toString'):
                    # QDate object
                    formatted_date = muudet.toString("dd.MM.yyyy")
                else:
                    # Try to parse as string/date
                    try:
                        from datetime import datetime
                        if isinstance(muudet, str):
                            # Assume YYYY-MM-DD format and convert to DD.MM.YYYY
                            date_obj = datetime.fromisoformat(str(muudet).split('T')[0])
                            formatted_date = date_obj.strftime("%d.%m.%Y")
                        else:
                            formatted_date = str(muudet)
                    except:
                        formatted_date = str(muudet)
                self.property_ui.lbl_muudet_value.setText(formatted_date)
            else:
                self.property_ui.lbl_muudet_value.setText("...")

            # Update kinnistu (property registry number)
            kinnistu = feature.attribute(Katastriyksus.kinnistu)
            self.property_ui.lbl_kinnistu_value.setText(str(kinnistu) if self._is_not_null(kinnistu) else "...")

        except Exception as e:
            print(f"Error updating property display: {e}")
            return

        self._load_property_connections(cadastral_value)

    @staticmethod
    def _is_not_null(value):
        return (
            value is not None
            and str(value).strip()
            and str(value).upper() != 'NULL'
        )

    def _load_property_connections(self, cadastral_number: Optional[str]):
        tree_widget = getattr(self.property_ui, "tree_section", None)
        if not tree_widget:
            return

        if not cadastral_number:
            tree_widget.show_message("Kinnistu pole valitud")
            return

        tree_widget.show_loading()
        self._connection_request_id += 1
        request_id = self._connection_request_id

        worker = FunctionWorker(self._build_connection_payload, cadastral_number)
        def handle_success(payload, rid=request_id):
            if rid != self._connection_request_id:
                return
            entries = payload.get("entries") or []
            message = payload.get("message")
            if message:
                tree_widget.show_message(message)
            elif entries:
                tree_widget.load_connections(entries)
            else:
                tree_widget.show_message("Seoseid ei leitud")

        def handle_error(error_message, rid=request_id):
            if rid != self._connection_request_id:
                return
            tree_widget.show_message(f"Viga: {error_message}")

        worker.finished.connect(handle_success)
        worker.error.connect(handle_error)

        thread = start_worker(worker)
        self._connection_thread = thread
        self._connection_worker = worker

        def cleanup():
            if self._connection_worker is worker:
                self._connection_worker = None
            if self._connection_thread is thread:
                self._connection_thread = None

        thread.finished.connect(cleanup)

    def _build_connection_payload(self, cadastral_number: str):
        lookup = PropertyLookupService()
        connections = PropertiesConnectedElementsQueries()
        formatter = PropertyConnectionFormatter()

        property_id = lookup.property_id_by_cadastral(cadastral_number)
        if not property_id:
            return {"entries": [], "message": "Kinnistut ei leitud"}

        module_data = connections.fetch_all_module_data(property_id)
        entry = formatter.build_entry(cadastral_number, property_id, module_data)
        return {"entries": [entry]}

