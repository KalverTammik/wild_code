from typing import Optional

from PyQt5.QtCore import QThread
try:
    import sip
except ImportError:  # PyQt6 fallback, though project currently uses PyQt5
    sip = None
from .property_service import PropertyDataService
from ...constants.cadastral_fields import Katastriyksus
from ...constants.settings_keys import SettingsService
from ...python.api_client import APIClient
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...languages.language_manager import LanguageManager
from ...languages.MaaAmetFieldFormater import format_field
from ...utils.MapTools.MapHelpers import ActiveLayersHelper
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...utils.MapTools.map_selection_controller import MapSelectionController
from ...utils.url_manager import Module
from ...python.workers import FunctionWorker, start_worker


class PropertyUITools:

    def __init__(self, property_ui, data_service: Optional[PropertyDataService] = None):
        self.property_ui = property_ui
        self._settings = SettingsService()
        self._connection_request_id = 0
        self._connection_thread: Optional[QThread] = None
        self._connection_worker: Optional[FunctionWorker] = None
        self._data_service = data_service or PropertyDataService()
        self.lang_manager = LanguageManager()
        self._selection_controller = MapSelectionController()
        self._lookup_request_id = 0
        self._lookup_thread: Optional[QThread] = None
        self._lookup_worker: Optional[FunctionWorker] = None

    def _get_active_ui(self):
        ui = getattr(self, "property_ui", None)
        if not ui:
            return None
        if sip:
            try:
                if sip.isdeleted(ui):
                    return None
            except Exception:
                return None
        return ui

    def _emit_ui_signal(self, signal_name: str):
        ui = self._get_active_ui()
        if not ui:
            return
        signal = getattr(ui, signal_name, None)
        if callable(getattr(signal, "emit", None)):
            try:
                signal.emit()
            except RuntimeError:
                pass


    def select_property_from_map(self):
        """Activate map selection tool for property selection."""
        ui = self._get_active_ui()
        if not ui:
            return
        active_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if not active_layer:
            return

        started = self._selection_controller.start_single_selection(
            active_layer,
            on_selected=self._handle_property_layer_selection,
        )
        if started:
            self._emit_ui_signal("property_selected_from_map")


    def _handle_property_layer_selection(self, active_layer, _features):
        ui = self._get_active_ui()
        if not ui:
            return
        try:
            self.update_property_display(active_layer)
        finally:
            self._emit_ui_signal("property_selection_completed")
            self.bring_dialog_to_front(ui)

    @staticmethod
    def bring_dialog_to_front(widget) -> None:
        """Best-effort attempt to bring the widget's top-level window to the foreground."""
        if widget is None:
            return
        try:
            main_dialog = widget.window()
            if not main_dialog:
                return
            main_dialog.showNormal()
            main_dialog.raise_()
            main_dialog.activateWindow()
        except Exception:
            # Not fatal if the window cannot be brought to the foreground
            pass

    def update_property_display(self, active_layer, *, trigger_connections: bool = True):
        """Update the UI labels with the selected property data."""
        ui = self._get_active_ui()
        if not ui:
            return

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
            ui.lbl_katastritunnus_value.setText(
                format_field(Katastriyksus.tunnus, katastritunnus)
            )

            # Update address label
            l_address = feature.attribute(Katastriyksus.l_aadress)
            ay_name = feature.attribute(Katastriyksus.ay_nimi)
            mk_name = feature.attribute(Katastriyksus.mk_nimi)
            address_parts = []
            if self._is_not_null(l_address): address_parts.append(str(l_address))
            if self._is_not_null(ay_name): address_parts.append(str(ay_name))
            if self._is_not_null(mk_name): address_parts.append(str(mk_name))
            address = ", ".join(address_parts) if address_parts else "..."
            ui.lbl_address_value.setText(address)

            # Update area label
            area = feature.attribute(Katastriyksus.pindala)
            ui.lbl_area_value.setText(
                format_field(Katastriyksus.pindala, area)
            )

            # Update sihtotstarve labels (3 separate labels, hide if NULL)
            siht1 = feature.attribute(Katastriyksus.siht1)
            siht2 = feature.attribute(Katastriyksus.siht2)
            siht3 = feature.attribute(Katastriyksus.siht3)
            so_prts1 = feature.attribute(Katastriyksus.so_prts1)
            so_prts2 = feature.attribute(Katastriyksus.so_prts2)
            so_prts3 = feature.attribute(Katastriyksus.so_prts3)

            # Siht 1
            self._update_siht_label(
                ui.lbl_siht1_label,
                ui.lbl_siht1_value,
                Katastriyksus.siht1,
                siht1,
                Katastriyksus.so_prts1,
                so_prts1,
            )

            # Siht 2
            self._update_siht_label(
                ui.lbl_siht2_label,
                ui.lbl_siht2_value,
                Katastriyksus.siht2,
                siht2,
                Katastriyksus.so_prts2,
                so_prts2,
            )

            # Siht 3
            self._update_siht_label(
                ui.lbl_siht3_label,
                ui.lbl_siht3_value,
                Katastriyksus.siht3,
                siht3,
                Katastriyksus.so_prts3,
                so_prts3,
            )

            # Update registr (registration date)
            registr = feature.attribute(Katastriyksus.registr)
            ui.lbl_registr_value.setText(
                format_field(Katastriyksus.registr, registr)
            )

            # Update muudet (modification date)
            muudet = feature.attribute(Katastriyksus.muudet)
            ui.lbl_muudet_value.setText(
                format_field(Katastriyksus.muudet, muudet)
            )

            # Update kinnistu (property registry number)
            kinnistu = feature.attribute(Katastriyksus.kinnistu)
            ui.lbl_kinnistu_value.setText(
                format_field(Katastriyksus.kinnistu, kinnistu)
            )

        except Exception as e:
            print(f"Error updating property display: {e}")
            return
        if trigger_connections:
            self._load_property_connections(cadastral_value)

    @staticmethod
    def _is_not_null(value):
        return (
            value is not None
            and str(value).strip()
            and str(value).upper() != 'NULL'
        )

    @staticmethod
    def _update_siht_label(label_widget, value_widget, field_name, field_value, percentage_field, percentage_value):
        formatted_value = format_field(field_name, field_value)
        if formatted_value == '---':
            label_widget.hide()
            value_widget.hide()
            return

        percentage_text = format_field(percentage_field, percentage_value)
        suffix = f" {percentage_text}" if percentage_text != '---' else ""
        value_widget.setText(f"{formatted_value}{suffix}")
        label_widget.show()
        value_widget.show()

    def _load_property_connections(self, cadastral_number: Optional[str]):
        ui = self._get_active_ui()
        if not ui:
            return
        tree_widget = ui.tree_section
        if not tree_widget:
            return

        if not cadastral_number:
            tree_widget.show_message("Kinnistu pole valitud")
            return

        tree_widget.show_loading()
        self._connection_request_id += 1
        request_id = self._connection_request_id

        worker = FunctionWorker(self._data_service.build_connections_for_cadastral, cadastral_number)

        # eeldus: FunctionWorker.finished emiteerib payload (nt dict)
        worker.finished.connect(
            lambda payload, rid=request_id: self.handle_success(payload, rid)
        )

        # eeldus: FunctionWorker.error emiteerib error_message (str)
        worker.error.connect(
            lambda error_message, rid=request_id: self.handle_error(
                error_message, rid
            )
        )

        thread = start_worker(worker)
        self._connection_thread = thread
        self._connection_worker = worker

        # kui see konkreetne thread lõpetab, siis puhastame viited
        thread.finished.connect(lambda t=thread, w=worker: self.cleanup(t, w))

    def open_property_from_search(self, item_id: str):
        ui = self._get_active_ui()
        if ui and ui.tree_section:
            ui.tree_section.show_loading()

        self._lookup_request_id += 1
        request_id = self._lookup_request_id

        worker = FunctionWorker(self._fetch_property_payload, item_id)
        worker.finished.connect(
            lambda payload, rid=request_id: self._handle_property_lookup_success(payload, rid)
        )
        worker.error.connect(
            lambda message, rid=request_id: self._handle_property_lookup_error(message, rid)
        )

        self._lookup_worker = worker
        self._lookup_thread = start_worker(worker, on_thread_finished=self._clear_lookup_worker_refs)

    def _fetch_property_payload(self, item_id: str):
        query = GraphQLQueryLoader().load_query_by_module(
            Module.PROPERTY.value,
            "cadastralNumber_by_id.graphql",
        )
        variables = {"id": item_id}
        response = APIClient().send_query(query, variables, return_raw=True) or {}
        property_data = (
            response.get("data", {}).get("property")
            or response.get("property")
            or {}
        )
        if not property_data:
            raise RuntimeError("Kinnistu ei leitud")
        return property_data

    def _handle_property_lookup_success(self, payload: dict, request_id: int):
        if request_id != self._lookup_request_id:
            return

        cadastral_number = payload.get("cadastralUnitNumber")
        if not cadastral_number:
            self._show_tree_message("Kinnistu ei leitud")
            return

        active_layer = PropertiesSelectors.show_connected_properties_on_map([cadastral_number],Module.PROPERTY.value)

        if active_layer:
            self.update_property_display(active_layer, trigger_connections=False)
        else:
            print("[PropertyUITools] Property layer missing while opening from search")

        self._load_property_connections(cadastral_number)

    def _handle_property_lookup_error(self, message: str, request_id: int):
        if request_id != self._lookup_request_id:
            return
        friendly = message or "Kinnistu ei leitud"
        self._show_tree_message(friendly)



    def _show_tree_message(self, message: str):
        ui = self._get_active_ui()
        tree_widget = ui.tree_section if ui else None
        if tree_widget:
            tree_widget.show_message(message)

    def _clear_lookup_worker_refs(self):
        self._lookup_worker = None
        self._lookup_thread = None

    def handle_success(self, payload: dict, rid: int):
        """Käsitle õnnestunud ühenduse laadimise tulemust."""
        if rid != self._connection_request_id:
            # Vahepeal käivitati uus päring; ignoreeri vana vastust.
            return

        ui = self._get_active_ui()
        tree_widget = ui.tree_section if ui else None
        if not tree_widget:
            return

        entries = payload.get("entries") or []
        message = payload.get("message")

        if message:
            tree_widget.show_message(message)
        elif entries:
            tree_widget.load_connections(entries)
        else:
            tree_widget.show_message("Seoseid ei leitud")

    def handle_error(self, error_message: str, rid: int):
        """Käsitle veaolukorda ühenduse laadimisel."""
        if rid != self._connection_request_id:
            # Vahepeal käivitati uus päring; ignoreeri vana viga.
            return

        ui = self._get_active_ui()
        tree_widget = ui.tree_section if ui else None
        if not tree_widget:
            return

        tree_widget.show_message(f"Viga: {error_message or 'Ühenduste laadimisel tekkis viga'}")

    def cleanup(self, thread: QThread, worker: FunctionWorker):
        """Puhasta viited aktiivsele workerile/threadile, kui just see eksemplar lõpetas."""
        if self._connection_worker is worker:
            self._connection_worker = None
        if self._connection_thread is thread:
            self._connection_thread = None
