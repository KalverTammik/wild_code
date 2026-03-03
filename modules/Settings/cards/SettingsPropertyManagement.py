# PropertyManagement.py

from ....constants.button_props import ButtonVariant
from qgis.utils import iface
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
from qgis.core import QgsProject

from .SettingsBaseCard import SettingsBaseCard
from ..settings_layer_helper import SettingsLayerHelper
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....utils.SHPLayerLoader import SHPLayerLoader
from ....utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from ....widgets.AddUpdatePropertyDialog import AddPropertyDialog, PropertyDialogMode
from ....modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ....modules.Property.FlowControllers.MainDeleteProperties import DeletePropertyUI
from ....languages.translation_keys import TranslationKeys
from ....languages.language_manager import LanguageManager
from ....utils.url_manager import Module
from ....utils.messagesHelper import ModernMessageDialog
from ....utils.mapandproperties.property_action_service import PropertyActionService
from ....utils.mapandproperties.property_action_service import PropertySelectionActionService
from ....Logs.python_fail_logger import PythonFailLogger
from ....ui.window_state.DialogCoordinator import get_dialog_coordinator
from time import monotonic




class PropertyManagementUI(SettingsBaseCard):
    def __init__(self, lang_manager: LanguageManager):
        super().__init__(
            lang_manager,
            lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT),
            None,
        )

        self._import_selection_controller = None
        self._delete_selection_controller = None
        self._add_from_map_dialog = None

        self._map_action_parent_window = None
        self._restore_parent_after_map_action = False
        self._shp_feature_cache: dict[str, object] = {
            "layer_id": None,
            "count": 0,
            "ts": 0.0,
        }
        self._layer_signals_connected = False
        self._has_shown_once = False

        cw = self.content_widget()
        main_layout = QVBoxLayout(cw)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # --- buttons row ---
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        self.btn_open_maa_amet = QPushButton(
            self.lang_manager.translate(TranslationKeys.OPEN_MAA_AMET_PAGE),
            cw,
        )

        self.btn_add_shp = QPushButton(
            self.lang_manager.translate(TranslationKeys.ADD_SHP_FILE),
            cw,
        )
        self.btn_add_property = QPushButton(
            self.lang_manager.translate(TranslationKeys.ADD_PROPERTY),
            cw,
        )
        # Primary delete UX: SignalTest-style dialog.
        self.btn_remove_property = QPushButton(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY),
            cw,
        )

        # Emergency option: delete by backend ID.
        self.btn_remove_property_by_id = QPushButton(
            self.lang_manager.translate(TranslationKeys.DELETE_BY_ID),
            cw,
        )

        self.btn_open_maa_amet.clicked.connect(self._handle_maa_amet_page)
        self.btn_add_shp.clicked.connect(self._handle_file_import)
        self.btn_add_property.clicked.connect(self._on_add_property_clicked)
        self.btn_remove_property.clicked.connect(self._on_remove_property_clicked)
        self.btn_remove_property_by_id.clicked.connect(self._on_remove_property_by_id_clicked)

        self.btn_open_maa_amet.setObjectName("ConfirmButton")
        self.btn_add_shp.setObjectName("ConfirmButton")
        self.btn_add_property.setObjectName("ConfirmButton")
        self.btn_remove_property.setObjectName("ConfirmButton")
        self.btn_remove_property_by_id.setObjectName("ConfirmButton")

        self.btn_open_maa_amet.setProperty("variant", ButtonVariant.WARNING)
        self.btn_add_shp.setProperty("variant", ButtonVariant.PRIMARY)
        self.btn_add_property.setProperty("variant", ButtonVariant.SUCCESS)
        self.btn_remove_property.setProperty("variant", ButtonVariant.DANGER)
        self.btn_remove_property_by_id.setProperty("variant", ButtonVariant.DANGER)


        btn_row.addWidget(self.btn_open_maa_amet)
        btn_row.addWidget(self.btn_add_shp)
        btn_row.addWidget(self.btn_add_property)
        btn_row.addWidget(self.btn_remove_property)
        btn_row.addWidget(self.btn_remove_property_by_id)
        btn_row.addStretch(1)

        main_layout.addLayout(btn_row)

        # Initial state deferred until widget is shown

    def _minimize_plugin_window_if_safe(self) -> None:
        self._enter_map_selection_mode()

    def _restore_plugin_window(self) -> None:
        self._exit_map_selection_mode()

    def _get_safe_parent_window(self):
        try:
            w = self.window()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_property_window_failed",
            )
            w = None

        if w is None:
            return None

        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_property_qgis_main_failed",
            )
            qgis_main = None

        if qgis_main is not None and w is qgis_main:
            return None

        return w

    def _enter_map_selection_mode(self) -> None:
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window()
        coordinator.enter_map_selection_mode(parent=parent_window)
        if parent_window is not None:
            self._map_action_parent_window = parent_window
            self._restore_parent_after_map_action = True

    def _exit_map_selection_mode(self) -> None:
        if not self._restore_parent_after_map_action:
            return
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window() or self._map_action_parent_window
        coordinator.exit_map_selection_mode(parent=parent_window)
        self._map_action_parent_window = None
        self._restore_parent_after_map_action = False

    def hideEvent(self, event):
        """Clean up when widget is hidden"""
        super().hideEvent(event)
        self._disconnect_layer_signals()

    def showEvent(self, event):
        """Update button states when widget becomes visible"""
        super().showEvent(event)
        self._connect_layer_signals()
        if not self._has_shown_once:
            self._has_shown_once = True
            self._update_button_states()

    # ---------- Button Handlers ----------
    def _on_property_added(self, property_data):
        """Handle when a property is successfully added"""
        # Here you can add logic to save the property data
        # For now, just emit the original signal
        self.addPropertyClicked.emit()

    def _on_remove_property_clicked(self):
        """SignalTest-style delete/action flow.

        User selects features on the MAIN property layer, then chooses action in the same
        dialog used by SignalTest (Archive/Unarchive/Delete).
        """

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if not main_layer:
            return

        self._delete_selection_controller = PropertySelectionActionService.start_settings_remove_flow(
            parent=self,
            main_layer=main_layer,
            translate=self.lang_manager.translate,
            prompt_title=self.lang_manager.translate(TranslationKeys.PROPERTY_BACKEND_ACTION_PROMPT_TITLE),
            on_restore_ui=self._restore_plugin_window,
            on_minimize_ui=self._minimize_plugin_window_if_safe,
            on_flow_finished=self._finish_remove_flow,
        )

    def _finish_remove_flow(self) -> None:
        self._delete_selection_controller = None
        self._invalidate_shp_feature_cache()
        self._restore_plugin_window()

    def _on_remove_property_by_id_clicked(self):
        """Emergency delete-by-id dialog (legacy)."""
        DeletePropertyUI(self)

    def _on_add_property_clicked(self):
        """Handle Add property button click"""

        btn_from_map = self.lang_manager.translate(TranslationKeys.SELECT_FROM_MAP)
        btn_by_location = self.lang_manager.translate(TranslationKeys.SELECT_BY_LOCATION_LIST)
        btn_cancel = self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON)

        choice = ModernMessageDialog.ask_choice_modern(
            self.lang_manager.translate(TranslationKeys.ADD_PROPERTY),
            self.lang_manager.translate(TranslationKeys.HOW_SELECT_PROPERTIES),
            buttons=[btn_from_map, btn_by_location, btn_cancel],
            default=btn_by_location,
            cancel=btn_cancel,
            button_variants=[ButtonVariant.PRIMARY, ButtonVariant.SUCCESS, ButtonVariant.WARNING],
        )

        if choice in (None, btn_cancel):
            return

        mode = None
        if choice == btn_by_location:
            mode = PropertyDialogMode.BY_LOCATION
        elif choice == btn_from_map:
            mode = PropertyDialogMode.FROM_MAP

        if mode is not None:
            if not MainAddPropertiesFlow.preflight_archive_layer_before_dialog():
                return
            AddPropertyDialog(self, mode=mode)
            return

        # Unknown choice (future-proof)
        return

    @staticmethod
    def _handle_maa_amet_page():
        """Open the Maa-Amet page for cadastral data."""
        from ....utils.url_manager import OpenLink, loadWebpage
        wl = OpenLink()
        loadWebpage.open_webpage(wl.maa_amet)

    def _handle_file_import(self):
        """Handle file import for property data using existing SHPLayerLoader"""
        # Use the existing SHPLayerLoader for proper import functionality
        loader = SHPLayerLoader(self)
        success = loader.load_shp_layer()
        if success:
            self._invalidate_shp_feature_cache()
            self._update_button_states()
        else:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.SHAPEFILE_LOAD_FAILED),
                self.lang_manager.translate(TranslationKeys.SHAPEFILE_LOAD_FAILED_MESSAGE),
            )
            

    
    
    def _update_button_states(self):
        """
        Internal logic that reads layers and applies the enabled/disabled states
        using the pure helper.
        """
        # 1) Discover layers
        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=True)
        shp_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)

        main_exists = main_layer is not None
        shp_exists = shp_layer is not None

        # 2) Compute state using helper
        shp_feature_count = self._get_shp_feature_count_cached(shp_layer) if shp_exists else 0

        shp_en, add_en, rem_en = LayerChecker.compute_property_button_states(
            main_exists,
            shp_exists,
            shp_feature_count,
        )

        # 3) Apply to buttons
        self.btn_add_shp.setEnabled(shp_en)
        self.btn_add_property.setEnabled(add_en)
        # Primary delete depends on MAIN layer.
        self.btn_remove_property.setEnabled(rem_en)

        # Emergency delete-by-id should stay available.
        self._best_effort_ui_call(
            self.btn_remove_property_by_id.setEnabled,
            True,
            event="settings_property_set_emergency_button_failed",
        )

    @staticmethod
    def _best_effort_ui_call(func, *args, event: str, **kwargs) -> bool:
        """Best-effort UI helper: logs failures and returns explicit success/failure."""
        try:
            func(*args, **kwargs)
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event=event,
            )
            return False

    def _get_shp_feature_count_cached(self, shp_layer) -> int:
        if shp_layer is None:
            self._invalidate_shp_feature_cache()
            return 0

        try:
            layer_id = shp_layer.id() if hasattr(shp_layer, "id") else None
        except Exception:
            layer_id = None

        now = monotonic()
        cached_id = self._shp_feature_cache.get("layer_id")
        cached_ts = float(self._shp_feature_cache.get("ts") or 0.0)
        cached_count = int(self._shp_feature_cache.get("count") or 0)

        if layer_id and cached_id == layer_id and (now - cached_ts) < 3.0:
            return cached_count

        try:
            count = 0
            for _idx, _feat in enumerate(shp_layer.getFeatures()):
                count += 1
                if count >= 3:
                    break
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_property_shp_feature_count_failed",
            )
            return 0

        self._shp_feature_cache.update({"layer_id": layer_id, "count": count, "ts": now})
        return count

    def _invalidate_shp_feature_cache(self) -> None:
        self._shp_feature_cache.update({"layer_id": None, "count": 0, "ts": 0.0})

    def _connect_layer_signals(self) -> None:
        if self._layer_signals_connected:
            return
        self._layer_signals_connected = SettingsLayerHelper.connect_project_layer_signals(
            project=QgsProject.instance() if QgsProject else None,
            handler=self._on_layers_changed,
            layer_will_be_removed_handler=self._on_layers_changed,
        )

    def _disconnect_layer_signals(self) -> None:
        if not self._layer_signals_connected:
            return
        SettingsLayerHelper.disconnect_project_layer_signals(
            project=QgsProject.instance() if QgsProject else None,
            handler=self._on_layers_changed,
            layer_will_be_removed_handler=self._on_layers_changed,
        )
        self._layer_signals_connected = False

    def _on_layers_changed(self, *args) -> None:
        self._invalidate_shp_feature_cache()
        self._update_button_states()


class LayerChecker:    
    @staticmethod
    def compute_property_button_states(main_layer_exists: bool, shp_layer_exists: bool, shp_feature_count: int = 0):
        """
        Return a tuple (shp_enabled, add_prop_enabled, remove_prop_enabled)
        based purely on whether layers exist.
        """
        # Base rule:
        # - SHP import button: always enabled (user can always try to import)
        # - Add property: enabled once SHP import layer exists and has features
        # - Remove property: only if main layer exists
        shp_enabled = True
        add_prop_enabled = shp_layer_exists and (shp_feature_count > 0)
        remove_prop_enabled = main_layer_exists

        return shp_enabled, add_prop_enabled, remove_prop_enabled