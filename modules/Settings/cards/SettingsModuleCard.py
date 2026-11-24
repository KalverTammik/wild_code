

from typing import Any

from PyQt5.QtWidgets import QVBoxLayout,  QFrame, QWidget
from PyQt5.QtCore import pyqtSignal, QTimer
from .SettingsBaseCard import SettingsBaseCard
from .settings_module_card_ui import SettingsModuleCardUiMixin
from .settings_module_preferences import SettingsModulePreferencesMixin
from .settings_temp_layer_flow import SettingsTempLayerMixin
from .ModuleLabelsWidget import ModuleLabelsWidget
from .SettingsPropertyManagement import PropertyManagementUI
from ..GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from ....utils.settings_logic import SettingsLogic
from ..settings_layer_helper import SettingsLayerHelper
from ....widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ....widgets.Filters.NotStartedStatusFilterWidget import NotStartedStatusFilterWidget
from ....widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ....widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ....widgets.layer_tree_picker import LayerTreePicker
from ....constants.module_icons import ModuleIconPaths
from ....utils.settings_service import SettingsService
from ....constants.module_names import Module
from ....utils.MapTools.MapHelpers import MapHelpers
from ....languages.translation_keys import TranslationKeys
from ....Logs.python_fail_logger import PythonFailLogger
from ....ui.messages_helper import ModernMessageDialog

from qgis.core import QgsMapLayer, QgsProject

class SettingsModuleCard(
    SettingsModuleCardUiMixin, SettingsModulePreferencesMixin, SettingsTempLayerMixin, SettingsBaseCard
):
    pendingChanged = pyqtSignal(bool)

    def __init__(
        self,
        lang_manager,
        module_name: str,
        translated_name: str,
        supports_types: bool = False,
        supports_statuses: bool = False,
        supports_tags: bool = False,
        supports_archive_layer: bool = False,
        module_labels=None,
        logic=None,
    ):
        # Ikon pealkirjale
        icon_path = ModuleIconPaths.get_module_icon(module_name.lower())
        super().__init__(lang_manager, translated_name, icon_path)

        # Kasuta kanonilist võtmekuju (lowercase) KÕIKJAL
        self.module_key = (module_name).lower().strip()  # võtmekoju (nt "property")
        self.supports_archive = bool(supports_archive_layer) or (self.module_key == Module.PROPERTY.value)
        self._pending_emit_scheduled = False
        self._last_pending_state: bool | None = None
        self._last_status_text: str | None = None

        self.supports_types = supports_types
        self.supports_statuses = supports_statuses
        self.supports_tags = supports_tags
        self.logic = logic or SettingsLogic()


        # Layer pickers
        self._layer_selector: LayerTreePicker | None = None
        self._archive_picker: LayerTreePicker | None = None
        self._works_temp_group: QFrame | None = None
        self._geospatial_mapper_group: QFrame | None = None
        self._property_management_container: QFrame | None = None
        self._property_management_widget: PropertyManagementUI | None = None
        self._can_manage_properties = False
        self._geospatial_mode_active = False

        self._module_labels = module_labels or []
        self._labels_widget: ModuleLabelsWidget | None = None
        self._orig_label_values = {}
        self._pend_label_values = {}
        self._lazy_filter_widgets: set[QWidget] = set()
        self._project_bound = False
        self._layer_signals_connected = False
        # Originaal vs pending
        self._orig_element_name = ""
        self._orig_archive_name = ""
        self._pend_element_name = ""
        self._pend_archive_name = ""
        self._orig_status_preferences = set()
        self._pend_status_preferences = set()
        self._orig_not_started_status_preferences = set()
        self._pend_not_started_status_preferences = set()
        self._orig_type_preferences = set()
        self._pend_type_preferences = set()
        self._orig_tag_preferences = set()
        self._pend_tag_preferences = set()

        # Filtrite viidad
        self._status_filter_widget: StatusFilterWidget | None = None
        self._not_started_status_filter_widget: NotStartedStatusFilterWidget | None = None
        self._type_filter_widget: TypeFilterWidget | None = None
        self._tags_filter_widget: TagsFilterWidget | None = None

        self.placeholder_text = self.lang_manager.translate(TranslationKeys.SELECT_LAYER)

        self._build_ui()

    def _log_error(self, event: str, exc: Exception, *, extra: dict | None = None) -> None:
        PythonFailLogger.log_exception(
            exc,
            module=Module.SETTINGS.value,
            event=event,
            extra=extra,
        )


    # --- UI ---
    def set_geospatial_mode_active(self, active: bool) -> None:
        self._geospatial_mode_active = bool(active)
        self._apply_geospatial_visibility()
        if self._property_management_widget is not None:
            self._property_management_widget.set_geospatial_mode_active(self._geospatial_mode_active)

    def _apply_geospatial_visibility(self) -> None:
        if self._geospatial_mapper_group is not None:
            self._geospatial_mapper_group.setVisible(self._geospatial_mode_active)
        if self.module_key == Module.WORKS.value and self._works_temp_group is not None:
            self._works_temp_group.setVisible(not self._geospatial_mode_active)

    def set_property_management_available(self, available: bool) -> None:
        if self.module_key != Module.PROPERTY.value:
            return
        self._can_manage_properties = bool(available)
        self._sync_property_management_widget()

    def _sync_property_management_widget(self) -> None:
        container = self._property_management_container
        if container is None:
            return
        layout = container.layout()
        if layout is None:
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        if not self._can_manage_properties:
            if self._property_management_widget is not None:
                try:
                    layout.removeWidget(self._property_management_widget)
                    self._property_management_widget.setParent(None)
                    self._property_management_widget.deleteLater()
                except Exception as exc:
                    self._log_error("settings_property_card_remove_management_failed", exc)
                self._property_management_widget = None
            container.setVisible(False)
            return

        if self._property_management_widget is None:
            self._property_management_widget = PropertyManagementUI(self.lang_manager)
            self._property_management_widget.set_geospatial_mode_active(self._geospatial_mode_active)
            layout.addWidget(self._property_management_widget)
        container.setVisible(True)

    def _on_open_geospatial_mapper_clicked(self) -> None:
        try:
            target_layer = self._layer_selector.currentLayer() if self._layer_selector is not None else None
            GeospatialLayerMapperDialog.open_for_module(
                lang_manager=self.lang_manager,
                module_name=self.module_key,
                target_layer=target_layer,
                parent=self,
            )
        except Exception as exc:
            self._log_error(
                "geospatial_layer_mapper_open_failed",
                exc,
                extra={"module": self.module_key},
            )
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                str(exc),
            )

    def _on_primary_layer_changed(self, layer: QgsMapLayer | None) -> None:
        self._on_element_selected(layer.id() if layer else "")

    def _on_archive_layer_changed(self, layer: QgsMapLayer | None) -> None:
        if not self.supports_archive:
            return
        self._on_archive_selected(layer.id() if layer else "")

    def _set_status_text_if_changed(self, text: str, visible: bool = True) -> None:
        if self._last_status_text == text:
            return
        self._last_status_text = text
        self.set_status_text(text, visible)

    def _emit_pending_changed(self, state: bool) -> None:
        self._last_pending_state = bool(state)
        if self._pending_emit_scheduled:
            return
        self._pending_emit_scheduled = True

        def _flush():
            try:
                import sip
            except ImportError:
                sip = None

            self._pending_emit_scheduled = False
            if self._last_pending_state is None:
                return
            try:
                if sip and sip.isdeleted(self):
                    return
            except TypeError:
                return
            if not self.isVisible():
                return
            self.pendingChanged.emit(bool(self._last_pending_state))

        QTimer.singleShot(0, _flush)

    # --- Lifecycle hooks (SettingsUI) ---
    def on_settings_activate(self, snapshot=None):
        self._geospatial_mode_active = SettingsService().geospatial_setup_mode() == "geospatial"
        project = QgsProject.instance() if QgsProject else None
        if project is not None and not self._project_bound:
            SettingsLayerHelper.set_combo_project(self._layer_selector, project)
            if self.supports_archive and self._archive_picker:
                SettingsLayerHelper.set_combo_project(self._archive_picker, project)
            self._project_bound = True
        if not self._layer_signals_connected:
            self._layer_signals_connected = SettingsLayerHelper.connect_project_layer_signals(
                project=project,
                handler=self._on_project_layers_changed,
            )
        # Lae algsed layer-nimed
        layer_state = self.logic.get_module_layer_ids(self.module_key, include_archive=self.supports_archive)
        next_element = layer_state.get("element", "")
        next_archive = "" if not self.supports_archive else layer_state.get("archive", "")
        if next_element != self._orig_element_name:
            self._orig_element_name = next_element
            self._pend_element_name = next_element
        if next_archive != self._orig_archive_name:
            self._orig_archive_name = next_archive
            self._pend_archive_name = next_archive

        # Lae status/type/tag eelistused
        self._load_preference_states()
        self._ensure_saved_preference_widgets_loaded()
        # Load label values from settings and sync UI
        self._orig_label_values = self.logic.load_module_label_values(self.module_key, self._module_labels)
        self._pend_label_values = dict(self._orig_label_values)
        if self._labels_widget:
            for k, v in self._orig_label_values.items():
                self._labels_widget.set_label_value(k, v)


        # Taasta layeri valikud (vaid kui kiht on olemas)
        self._restore_layer_selections(
            element_name=self._orig_element_name,
            archive_name=self._orig_archive_name,
        )

        self._apply_geospatial_visibility()
        self._update_stored_values_display()

    def on_settings_deactivate(self):
        self._cancel_filter_workers()
        if self._layer_signals_connected:
            project = QgsProject.instance() if QgsProject else None
            SettingsLayerHelper.disconnect_project_layer_signals(
                project=project,
                handler=self._on_project_layers_changed,
            )
            self._layer_signals_connected = False
        # Clear filter widgets to release memory
        for widget in (
            self._status_filter_widget,
            self._not_started_status_filter_widget,
            self._type_filter_widget,
            self._tags_filter_widget,
        ):
            if widget is None:
                continue
            try:
                widget.clear_data()
            except Exception as exc:
                self._log_error("settings_card_clear_data_failed", exc, extra={"widget": type(widget).__name__})
                continue

        if self._labels_widget:
            try:
                self._labels_widget.clear_data()
            except Exception as exc:
                self._log_error(
                    "settings_card_clear_data_failed", exc, extra={"widget": type(self._labels_widget).__name__}
                )
        try:
            self._set_status_text_if_changed("")
        except Exception as exc:
            self._log_error("settings_module_clear_status_failed", exc)

        # Keep map layer combo bindings to avoid expensive rebinds on next open



    # --- Persistence helpers -------------------------------------------------

    def _write_saved_layer_value(self, kind: str, layer_name: str):
        if kind == "archive" and not self.supports_archive:
            return
        self.logic.set_module_layer_id(
            self.module_key,
            kind="archive" if kind == "archive" else "element",
            layer_name=layer_name,
        )

    # --- Apply/Revert/State ---
    def has_pending_changes(self) -> bool:
        el_dirty = self._pend_element_name != self._orig_element_name
        ar_dirty = self._pend_archive_name != self._orig_archive_name
        status_dirty = self._pend_status_preferences != self._orig_status_preferences
        not_started_status_dirty = self._pend_not_started_status_preferences != self._orig_not_started_status_preferences
        type_dirty = bool(self.supports_types) and self._pend_type_preferences != self._orig_type_preferences
        tag_dirty = bool(self.supports_tags) and self._pend_tag_preferences != self._orig_tag_preferences
        label_dirty = any(
            self._pend_label_values.get(k, "") != self._orig_label_values.get(k, "")
            for k in set(self._pend_label_values.keys()) | set(self._orig_label_values.keys())
        )
        return el_dirty or ar_dirty or status_dirty or not_started_status_dirty or type_dirty or tag_dirty or label_dirty

    def apply(self):
        changed = False

        if self._pend_element_name != self._orig_element_name:
            self._write_saved_layer_value("element", self._pend_element_name)
            self._orig_element_name = self._pend_element_name
            SettingsLayerHelper.restore_combo_selection(self._layer_selector, self._orig_element_name)
            changed = True

        if self.supports_archive and (self._pend_archive_name != self._orig_archive_name):
            self._write_saved_layer_value("archive", self._pend_archive_name)
            self._orig_archive_name = self._pend_archive_name
            if self._archive_picker:
                SettingsLayerHelper.restore_combo_selection(self._archive_picker, self._orig_archive_name)
            changed = True

        changed = self._save_preference_states() or changed

        # Save label values; an emptied one (a reset) is removed from the storage.
        for key, value in self._pend_label_values.items():
            if self._orig_label_values.get(key, "") != value:
                if str(value or "") == "":
                    self.logic.clear_module_label_value(self.module_key, key)
                else:
                    self.logic.save_module_label_value(self.module_key, key, value)
                changed = True
        if changed:
            self._orig_label_values = dict(self._pend_label_values)

        # Reset pending layer ids
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Labels
        self._pend_label_values = dict(self._orig_label_values)
        if self._labels_widget:
            for k, v in self._orig_label_values.items():
                self._labels_widget.set_label_value(k, v)

        self._update_stored_values_display()
        self._emit_pending_changed(False if changed else self.has_pending_changes())

    def revert(self):
        # Layers
        self._restore_layer_selections(
            element_name=self._orig_element_name,
            archive_name=self._orig_archive_name,
        )
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        self._revert_preference_states()

        # The label values too: a pending reset emptied them on screen.
        self._pend_label_values = dict(self._orig_label_values)
        if self._labels_widget:
            for key, value in self._orig_label_values.items():
                self._labels_widget.set_label_value(key, value)

        self._update_stored_values_display()
        self._emit_pending_changed(False)

    def _update_stored_values_display(self):
        """Footeris voolav kokkuvõte salvestatud väärtustest."""
        try:
            def display_for(combo, fallback_name: str) -> str:
                try:
                    if combo:
                        lyr = combo.currentLayer()
                        if lyr:
                            return lyr.name()
                except (AttributeError, RuntimeError):
                    pass
                return MapHelpers.layer_name_from_id(fallback_name) or fallback_name or ""

            element_name = display_for(self._layer_selector, self._pend_element_name or self._orig_element_name)
            archive_name = ""
            if self.supports_archive:
                archive_name = display_for(self._archive_picker, self._pend_archive_name or self._orig_archive_name)

            parts = []
            if element_name:
                parts.append(f"📄 Main: {element_name}")
            if archive_name:
                parts.append(f"📁 Archive: {archive_name}")

            if parts:
                values_text = ", ".join(parts)
                self._set_status_text_if_changed(f"Active layers: {values_text}")
            else:
                self._set_status_text_if_changed("No layers configured")
        except Exception as exc:
            self._log_error("settings_module_update_status_failed", exc)
            self._set_status_text_if_changed("Settings loaded")


    # --- Filter handlers & Reset ---
    def _on_reset_settings(self):
        """Empty every value of this card as a pending change (audit 2026-11-24).

        Nothing is written here: the general Confirm saves the reset, Discard brings the old values back.
        It used to clear the storage at once, without asking, and Discard then showed values that were gone.
        """
        if not ModernMessageDialog.ask_yes_no(
            self.lang_manager.translate(TranslationKeys.RESET),
            self.lang_manager.translate(TranslationKeys.SETTINGS_RESET_CONFIRM),
            yes_label=self.lang_manager.translate(TranslationKeys.RESET),
            no_label=self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON),
            default=self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON),
        ):
            return
        try:
            SettingsLayerHelper.clear_combo_selection(self._layer_selector)
            if self.supports_archive:
                SettingsLayerHelper.clear_combo_selection(self._archive_picker)
            self._pend_element_name = ""
            self._pend_archive_name = ""

            for _enabled, _support_key, _orig_attr, pend_attr, widget in self._preference_specs():
                setattr(self, pend_attr, set())
                if widget is not None:
                    widget.set_selected_ids([], emit=False)
            self._pend_not_started_status_preferences = set()
            if self._not_started_status_filter_widget is not None:
                self._not_started_status_filter_widget.set_selected_ids([], emit=False)

            self._pend_label_values = {key: "" for key in self._orig_label_values}
            if self._labels_widget:
                for key in self._pend_label_values:
                    self._labels_widget.set_label_value(key, "")

            self._update_stored_values_display()
            self.set_status_text(self.lang_manager.translate(TranslationKeys.SETTINGS_RESET_PENDING), True)
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:  # button callback: nothing may escape
            self._log_error("settings_module_reset_failed", exc)
            self.set_status_text(f"❌ {self.lang_manager.translate(TranslationKeys.SETTINGS_RESET_FAILED)}: {exc}", True)

    # --- Eelistused (settings) ---

    def _on_project_layers_changed(self, *args) -> None:
        self._restore_layer_selections(
            element_name=self._pend_element_name,
            archive_name=self._pend_archive_name,
        )

    def _restore_layer_selections(self, *, element_name: str, archive_name: str = "") -> None:
        SettingsLayerHelper.restore_combo_selection(self._layer_selector, element_name)
        if self.supports_archive and self._archive_picker:
            SettingsLayerHelper.restore_combo_selection(self._archive_picker, archive_name)

    # --- Layer valiku handlerid ---
    def _update_pending_layer_selection(self, *, layer_id: str, target_attr: str) -> None:
        setattr(self, target_attr, str(layer_id or "").strip())
        self._update_stored_values_display()
        self._emit_pending_changed(self.has_pending_changes())

    def _on_element_selected(self, layer_id: str):
        self._update_pending_layer_selection(layer_id=layer_id, target_attr="_pend_element_name")

    def _on_archive_selected(self, layer_id: str):
        if not self.supports_archive:
            return
        self._update_pending_layer_selection(layer_id=layer_id, target_attr="_pend_archive_name")

    # --- External sync helpers (used by flows) ---
    def sync_archive_layer_selection(self, layer_name: str, *, force: bool = False) -> bool:
        """Sync archive picker + stored values to an already-persisted setting.

        This is useful when some flow creates an archive layer programmatically and
        also persists it via SettingsService/SettingsLogic; the Settings UI should
        immediately reflect the new layer.

        Returns True if the UI was updated.
        """

        if not self.supports_archive:
            return False

        normalized = (layer_name or "").strip()

        # If user has a pending archive change, don't override unless forced.
        if (not force) and (self._pend_archive_name != self._orig_archive_name):
            return False

        self._orig_archive_name = normalized
        self._pend_archive_name = normalized

        if self._archive_picker:
            SettingsLayerHelper.restore_combo_selection(self._archive_picker, normalized)

        self._update_stored_values_display()
        self._emit_pending_changed(self.has_pending_changes())
        return True

    def sync_main_layer_selection(self, layer_name: str, *, force: bool = False) -> bool:
        """Sync main-layer picker + stored values to an already-persisted setting."""

        normalized = (layer_name or "").strip()

        if (not force) and (self._pend_element_name != self._orig_element_name):
            return False

        self._orig_element_name = normalized
        self._pend_element_name = normalized

        SettingsLayerHelper.restore_combo_selection(self._layer_selector, normalized)
        self._update_stored_values_display()
        self._emit_pending_changed(self.has_pending_changes())
        return True

    def _on_label_changed(self, key: str, value: Any):
        if not key:
            return
        self._pend_label_values[key] = value
        self._emit_pending_changed(self.has_pending_changes())

