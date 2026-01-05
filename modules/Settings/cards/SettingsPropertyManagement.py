# PropertyManagement.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton
)
from qgis.core import QgsProject

from .SettingsBaseCard import SettingsBaseCard
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....utils.SHPLayerLoader import SHPLayerLoader
from ....utils.MapTools.MapHelpers import MapHelpers
from ....widgets.AddUpdatePropertyDialog import AddPropertyDialog
from ....modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ....modules.Property.FlowControllers.MainDeleteProperties import DeletePropertyUI
from ....modules.Property.FlowControllers.BackendPropertyActions import BackendPropertyActions
from ....languages.translation_keys import TranslationKeys
from ....languages.language_manager import LanguageManager
from ....constants.settings_keys import SettingsService
from ....utils.url_manager import Module
from ....utils.messagesHelper import ModernMessageDialog
from ....utils.MapTools.map_selection_controller import MapSelectionController
from ....widgets.AddFromMapPropertyDialog import AddFromMapPropertyDialog
from ....modules.signaltest.BackendActionPromptDialog import BackendActionPromptDialog
from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget
from ....utils.MapTools.MapHelpers import ActiveLayersHelper, FeatureActions
from ....constants.cadastral_fields import Katastriyksus

try:
    from qgis.utils import iface
except Exception:
    iface = None


class PropertyManagementUI(SettingsBaseCard):
    def __init__(self, lang_manager: LanguageManager):
        super().__init__(
            lang_manager,
            lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT),
            None,
        )

        self._project = QgsProject.instance()
        self._import_selection_controller = None
        self._delete_selection_controller = None
        self._add_from_map_dialog = None

        self._map_action_parent_window = None
        self._restore_parent_after_map_action = False

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
        # Primary delete UX: SignalTest-style dialog.
        self.btn_remove_property = QPushButton(
            self.lang_manager.translate(TranslationKeys.REMOVE_PROPERTY),
            cw,
        )

        # Emergency option: delete by backend ID.
        self.btn_remove_property_by_id = QPushButton(
            self.lang_manager.translate(TranslationKeys.DELETE_BY_ID) or "Delete by ID",
            cw,
        )

        self.btn_add_shp.clicked.connect(self._handle_file_import)
        self.btn_add_property.clicked.connect(self._on_add_property_clicked)
        self.btn_remove_property.clicked.connect(self._on_remove_property_clicked)
        self.btn_remove_property_by_id.clicked.connect(self._on_remove_property_by_id_clicked)

        self.btn_add_shp.setObjectName("ConfirmButton")
        self.btn_add_property.setObjectName("ConfirmButton")
        self.btn_remove_property.setObjectName("ConfirmButton")
        self.btn_remove_property_by_id.setObjectName("ConfirmButton")

        btn_row.addWidget(self.btn_add_shp)
        btn_row.addWidget(self.btn_add_property)
        btn_row.addWidget(self.btn_remove_property)
        btn_row.addWidget(self.btn_remove_property_by_id)
        btn_row.addStretch(1)

        main_layout.addLayout(btn_row)

        # Initial state
        self._update_button_states()

    def _minimize_plugin_window_if_safe(self) -> None:
        """Minimize only the plugin window (never QGIS main window)."""

        try:
            w = self.window()
        except Exception:
            w = None

        if w is None:
            return

        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception:
            qgis_main = None

        # Never minimize QGIS main window.
        if qgis_main is not None and w is qgis_main:
            return

        try:
            if w.isVisible() and not w.isMinimized():
                w.showMinimized()
                self._map_action_parent_window = w
                self._restore_parent_after_map_action = True
        except Exception:
            pass

    def _restore_plugin_window(self) -> None:
        if not self._restore_parent_after_map_action:
            return

        w = self._map_action_parent_window
        if w is None:
            return

        try:
            w.showNormal()
            w.raise_()
            w.activateWindow()
        except Exception:
            pass
        finally:
            self._map_action_parent_window = None
            self._restore_parent_after_map_action = False

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
        """SignalTest-style delete/action flow.

        User selects features on the MAIN property layer, then chooses action in the same
        dialog used by SignalTest (Archive/Unarchive/Delete).
        """

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if not main_layer:
            return

        ModernMessageDialog.Info_messages_modern(
            "Select properties",
            "Select one or more properties on the map from the MAIN property layer.\n\n"
            "Then choose an action (Archive/Unarchive/Delete).",
        )

        controller = MapSelectionController()
        self._delete_selection_controller = controller

        # Let user interact with the map: minimize plugin window only.
        self._minimize_plugin_window_if_safe()

        def _on_selected(_layer, features):
            try:
                # Bring plugin UI back before we show any dialogs.
                self._restore_plugin_window()

                feats = list(features or [])
                if not feats:
                    ModernMessageDialog.Info_messages_modern(
                        "No selection",
                        "No properties were selected.",
                    )
                    return

                rows = []
                tunnused: list[str] = []
                for f in feats:
                    try:
                        cadastral_id = str(f[Katastriyksus.tunnus])
                    except Exception:
                        cadastral_id = ""
                    try:
                        address = str(f[Katastriyksus.l_aadress])
                    except Exception:
                        address = ""
                    try:
                        area = str(f[Katastriyksus.pindala])
                    except Exception:
                        area = ""
                    try:
                        settlement = str(f[Katastriyksus.ay_nimi])
                    except Exception:
                        settlement = ""

                    if cadastral_id:
                        tunnused.append(cadastral_id)

                    rows.append(
                        {
                            "cadastral_id": cadastral_id,
                            "address": address,
                            "area": area,
                            "settlement": settlement,
                            "feature": f,
                        }
                    )

                # Build a read-only snapshot table and show the exact same prompt dialog as SignalTest.
                frame, table = PropertyTableWidget._create_properties_table()
                PropertyTableManager.reset_and_populate_properties_table(table, rows)
                try:
                    table.selectAll()
                except Exception:
                    pass

                dlg = BackendActionPromptDialog(parent=self, table_frame=frame, table=table, title="Choose action")
                ok = dlg.exec_()
                if not ok:
                    return

                action = dlg.action
                if not action:
                    return

                # De-dup tunnused while preserving order.
                seen = set()
                tunnused_u: list[str] = []
                for t in tunnused:
                    t = str(t or "").strip()
                    if not t or t in seen:
                        continue
                    seen.add(t)
                    tunnused_u.append(t)

                if not tunnused_u:
                    ModernMessageDialog.Warning_messages_modern(
                        "Missing tunnus",
                        "Selected features do not contain cadastral tunnus.",
                    )
                    return

                if action == "archive":
                    BackendPropertyActions.archive_properties_by_tunnused(
                        tunnused_u,
                        archive_tag_name="Arhiveeritud",
                        module_name=Module.PROPERTY.name,
                    )
                    ModernMessageDialog.Info_messages_modern(
                        "Backend action",
                        f"Archived in backend: {len(tunnused_u)}",
                    )
                elif action == "unarchive":
                    BackendPropertyActions.unarchive_properties_by_tunnused(tunnused_u)
                    ModernMessageDialog.Info_messages_modern(
                        "Backend action",
                        f"Unarchived in backend: {len(tunnused_u)}",
                    )
                elif action == "delete":
                    # SignalTest-style: delete backend + delete MAIN features by tunnus.
                    BackendPropertyActions.delete_properties_by_tunnused(tunnused_u)

                    ok_commit, feature_ids, err = FeatureActions.delete_features_by_field_values(
                        main_layer,
                        Katastriyksus.tunnus,
                        tunnused_u,
                    )

                    lines = [
                        f"Backend delete attempted: {len(tunnused_u)}",
                        f"MAIN matched: {len(feature_ids or [])}",
                        f"MAIN deleted: {len(feature_ids or []) if ok_commit else 0}",
                    ]
                    if err:
                        lines.append(f"Error: {err}")

                    if ok_commit:
                        ModernMessageDialog.Info_messages_modern("Delete", "\n".join(lines))
                    else:
                        ModernMessageDialog.Warning_messages_modern("Delete (partial)", "\n".join(lines))

                else:
                    ModernMessageDialog.Warning_messages_modern(
                        "Unknown action",
                        f"Action '{action}' is not supported.",
                    )
            finally:
                self._delete_selection_controller = None
                self._restore_plugin_window()

        started = controller.start_selection(
            main_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=False,
        )

        if not started:
            self._delete_selection_controller = None
            self._restore_plugin_window()
            ModernMessageDialog.Warning_messages_modern(
                "Selection failed",
                "Could not start map selection on the MAIN property layer.",
            )

    def _on_remove_property_by_id_clicked(self):
        """Emergency delete-by-id dialog (legacy)."""
        DeletePropertyUI(self)

    def _on_add_property_clicked(self):
        """Handle Add property button click"""

        btn_from_map = self.lang_manager.translate(TranslationKeys.SELECT_FROM_MAP) or "Select from map"
        btn_by_location = self.lang_manager.translate(TranslationKeys.SELECT_BY_LOCATION_LIST) or "Select by location (list)"
        btn_cancel = self.lang_manager.translate(TranslationKeys.CANCEL) or "Cancel"

        choice = ModernMessageDialog.ask_choice_modern(
            self.lang_manager.translate(TranslationKeys.ADD_PROPERTY) or "Add property",
            "How do you want to select properties?",
            buttons=[btn_from_map, btn_by_location, btn_cancel],
            default=btn_by_location,
            cancel=btn_cancel,
        )

        if choice in (None, btn_cancel):
            return

        if choice == btn_by_location:
            if not MainAddPropertiesFlow.preflight_archive_layer_before_dialog():
                return
            AddPropertyDialog(self)
            return

        if choice == btn_from_map:
            if not MainAddPropertiesFlow.preflight_archive_layer_before_dialog():
                return

            # New UX: open a dialog similar to AddPropertyDialog, but without location filters.
            # User selects from map, table fills like SignalTest, then user clicks Add.
            try:
                if self._add_from_map_dialog is not None and self._add_from_map_dialog.isVisible():
                    self._add_from_map_dialog.raise_()
                    self._add_from_map_dialog.activateWindow()
                    return
            except Exception:
                pass

            self._add_from_map_dialog = AddFromMapPropertyDialog(self)
            return

        # Unknown choice (future-proof)
        return


    def _handle_file_import(self):
        """Handle file import for property data using existing SHPLayerLoader"""
        # Use the existing SHPLayerLoader for proper import functionality
        loader = SHPLayerLoader(self)
        success = loader.load_shp_layer()
        if success:
            self._update_button_states()
            pass
        else:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate("Import Failed") or "Import ebaõnnestus",
                self.lang_manager.translate("Failed to import property file.") or
                "Kinnistute faili import ebaõnnestus.",
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
        # Primary delete depends on MAIN layer.
        self.btn_remove_property.setEnabled(rem_en)

        # Emergency delete-by-id should stay available.
        try:
            self.btn_remove_property_by_id.setEnabled(True)
        except Exception:
            pass


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