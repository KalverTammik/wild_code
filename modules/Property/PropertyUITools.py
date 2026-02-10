from typing import Optional
import sys

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
from ...Logs.switch_logger import SwitchLogger
from ...Logs.python_fail_logger import PythonFailLogger
from ...ui.window_state.DialogCoordinator import get_dialog_coordinator
from qgis.utils import iface


class PropertyUITools:

    def __init__(self, property_ui, data_service: Optional[PropertyDataService] = None):
        self.property_ui = property_ui
        self._settings = SettingsService()
        self._connection_thread: Optional[QThread] = None
        self._connection_worker: Optional[FunctionWorker] = None
        self._data_service = data_service or PropertyDataService()
        self.lang_manager = LanguageManager()
        self._selection_controller = MapSelectionController()
        self._lookup_thread: Optional[QThread] = None
        self._lookup_worker: Optional[FunctionWorker] = None
        self._disable_map_lookup_on_search = True

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

    def _is_layer_valid(self, layer) -> bool:
        if layer is None:
            return False
        if sip:
            try:
                if sip.isdeleted(layer):
                    return False
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_layer_sip_check_failed",
                )
                return False
        try:
            if hasattr(layer, "isValid") and not layer.isValid():
                return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_layer_valid_check_failed",
            )
            return False
        return True

    def _emit_ui_signal(self, signal_name: str):
        ui = self._get_active_ui()
        if not ui:
            return
        signal = getattr(ui, signal_name, None)
        if callable(getattr(signal, "emit", None)):
            try:
                signal.emit()
            except RuntimeError as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_signal_emit_failed",
                    extra={"signal": signal_name},
                )

    def _current_token(self) -> int | None:
        ui = self._get_active_ui()
        if ui is None:
            return None
        return getattr(ui, "_active_token", None)

    def _is_token_active(self, token: int | None) -> bool:
        if token is None:
            return True
        ui = self._get_active_ui()
        if ui is None:
            return False
        if hasattr(ui, "is_token_active"):
            try:
                return bool(ui.is_token_active(token))
            except Exception:
                return False
        return bool(getattr(ui, "_activated", False)) and token == getattr(ui, "_active_token", None)


    def select_property_from_map(self):
        """Activate map selection tool for property selection."""
        ui = self._get_active_ui()
        if not ui:
            return
        active_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if not active_layer:
            try:
                PythonFailLogger.log(
                    "property_layer_missing",
                    module=Module.PROPERTY.value,
                    message="Active property layer not found when selecting from map",
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
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
            coordinator = get_dialog_coordinator(iface)
            coordinator.bring_to_front(main_dialog)
        except Exception:
            # Not fatal if the window cannot be brought to the foreground
            pass

    def update_property_display(self, active_layer, *, trigger_connections: bool = True):
        """Update the UI labels with the selected property data."""
        ui = self._get_active_ui()
        if not ui:
            return

        if not self._is_layer_valid(active_layer):
            try:
                PythonFailLogger.log(
                    "property_layer_invalid",
                    module=Module.PROPERTY.value,
                    message="Active layer invalid or deleted",
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
            return

        features = active_layer.selectedFeatures()
        if not features:
            try:
                PythonFailLogger.log(
                    "property_layer_no_selection",
                    module=Module.PROPERTY.value,
                    message="No selected features in property layer",
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
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
            try:
                PythonFailLogger.log_exception(
                    e,
                    module=Module.PROPERTY.value,
                    event="property_display_error",
                )
            except Exception as exc:
                print(f"[PropertyUITools] log_exception failed: {exc}", file=sys.stderr)
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
            try:
                PythonFailLogger.log(
                    "property_connections_missing_id",
                    module=Module.PROPERTY.value,
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
            tree_widget.show_message("Kinnistu pole valitud")
            return

        tree_widget.show_loading()
        token = self._current_token()

        try:
            PythonFailLogger.log(
                "property_connections_start",
                module=Module.PROPERTY.value,
                extra={"token": token, "cadastral": cadastral_number},
            )
        except Exception as exc:
            print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)

        worker = FunctionWorker(self._data_service.build_connections_for_cadastral, cadastral_number)
        worker.active_token = token

        # eeldus: FunctionWorker.finished emiteerib payload (nt dict)
        worker.finished.connect(
            lambda payload, tok=token: self.handle_success(payload, tok)
        )

        # eeldus: FunctionWorker.error emiteerib error_message (str)
        worker.error.connect(
            lambda error_message, tok=token: self.handle_error(
                error_message, tok
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

        token = self._current_token()

        try:
            PythonFailLogger.log(
                "property_search_start",
                module=Module.PROPERTY.value,
                extra={"token": token, "item_id": item_id},
            )
        except Exception as exc:
            print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)

        worker = FunctionWorker(self._fetch_property_payload, item_id)
        worker.active_token = token
        worker.finished.connect(
            lambda payload, tok=token: self._handle_property_lookup_success(payload, tok)
        )
        worker.error.connect(
            lambda message, tok=token: self._handle_property_lookup_error(message, tok)
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

    def _handle_property_lookup_success(self, payload: dict, token: int | None):
        if not self._is_token_active(token):
            SwitchLogger.log(
                "property_lookup_ignored_inactive_token",
                module=Module.PROPERTY.value,
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "property_lookup_token_ok",
            module=Module.PROPERTY.value,
            extra={"token": token, "current": self._current_token()},
        )

        cadastral_number = payload.get("cadastralUnitNumber")
        if not cadastral_number:
            try:
                PythonFailLogger.log(
                    "property_search_missing_cadastral",
                    module=Module.PROPERTY.value,
                    extra={"token": token},
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
            self._show_tree_message("Kinnistu ei leitud")
            return

        if self._disable_map_lookup_on_search:
            try:
                PythonFailLogger.log(
                    "property_map_lookup_skipped",
                    module=Module.PROPERTY.value,
                    extra={"cadastral": cadastral_number},
                )
            except Exception as exc:
                print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
        else:
            active_layer = PropertiesSelectors.show_connected_properties_on_map([cadastral_number], Module.PROPERTY.value)

            if active_layer:
                if self._is_layer_valid(active_layer):
                    selected = []
                    try:
                        selected = active_layer.selectedFeatures() or []
                    except Exception as exc:
                        PythonFailLogger.log_exception(
                            exc,
                            module=Module.PROPERTY.value,
                            event="property_layer_selected_features_failed",
                        )
                        selected = []
                    if selected:
                        self.update_property_display(active_layer, trigger_connections=False)
                    else:
                        try:
                            PythonFailLogger.log(
                                "property_layer_no_selection",
                                module=Module.PROPERTY.value,
                                message="No selected features after search map lookup",
                                extra={"cadastral": cadastral_number},
                            )
                        except Exception as exc:
                            print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
                        self._show_tree_message("Kinnistu puudub kihil")
                else:
                    try:
                        PythonFailLogger.log(
                            "property_layer_invalid",
                            module=Module.PROPERTY.value,
                            message="Layer invalid after search map lookup",
                            extra={"cadastral": cadastral_number},
                        )
                    except Exception as exc:
                        print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
                    self._show_tree_message("Kinnistu puudub kihil")
            else:
                try:
                    PythonFailLogger.log(
                        "property_feature_not_found",
                        module=Module.PROPERTY.value,
                        message="No matching features after search map lookup",
                        extra={"cadastral": cadastral_number},
                    )
                except Exception as exc:
                    print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)
                self._show_tree_message("Kinnistu puudub kihil")

        self._load_property_connections(cadastral_number)

    def _handle_property_lookup_error(self, message: str, token: int | None):
        if not self._is_token_active(token):
            SwitchLogger.log(
                "property_lookup_ignored_inactive_token",
                module=Module.PROPERTY.value,
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "property_lookup_token_ok",
            module=Module.PROPERTY.value,
            extra={"token": token, "current": self._current_token()},
        )
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

    def handle_success(self, payload: dict, token: int | None):
        """Käsitle õnnestunud ühenduse laadimise tulemust."""
        if not self._is_token_active(token):
            SwitchLogger.log(
                "property_connections_ignored_inactive_token",
                module=Module.PROPERTY.value,
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "property_connections_token_ok",
            module=Module.PROPERTY.value,
            extra={"token": token, "current": self._current_token()},
        )

        ui = self._get_active_ui()
        tree_widget = ui.tree_section if ui else None
        if not tree_widget:
            return

        entries = payload.get("entries") or []
        message = payload.get("message")

        try:
            PythonFailLogger.log(
                "property_connections_success",
                module=Module.PROPERTY.value,
                extra={"token": token, "entries": len(entries)},
            )
        except Exception as exc:
            print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)

        if message:
            tree_widget.show_message(message)
        elif entries:
            tree_widget.load_connections(entries)
        else:
            tree_widget.show_message("Seoseid ei leitud")

    def handle_error(self, error_message: str, token: int | None):
        """Käsitle veaolukorda ühenduse laadimisel."""
        if not self._is_token_active(token):
            SwitchLogger.log(
                "property_connections_ignored_inactive_token",
                module=Module.PROPERTY.value,
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "property_connections_token_ok",
            module=Module.PROPERTY.value,
            extra={"token": token, "current": self._current_token()},
        )

        try:
            PythonFailLogger.log(
                "property_connections_error",
                module=Module.PROPERTY.value,
                message=error_message,
                extra={"token": token},
            )
        except Exception as exc:
            print(f"[PropertyUITools] log failed: {exc}", file=sys.stderr)

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
