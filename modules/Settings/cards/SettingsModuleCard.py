

from PyQt5.QtWidgets import QVBoxLayout,  QFrame, QHBoxLayout, QGroupBox, QWidget
from PyQt5.QtCore import pyqtSignal
from .SettingsBaseCard import SettingsBaseCard
from .UIUtils import SettingsModuleFeatureCard
from ....widgets.StatusFilterWidget import StatusFilterWidget
from ....widgets.TypeFilterWidget import TypeFilterWidget
from ....widgets.TagsFilterWidget import TagsFilterWidget
from ....constants.module_icons import ModuleIconPaths
from ....utils.url_manager import Module
from ....constants.settings_keys import SettingsService
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.FilterHelpers.FilterHelper import FilterHelper
from ....utils.url_manager import ModuleSupports
from ....languages.translation_keys import TranslationKeys
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayer, QgsProject, Qgis

class SettingsModuleCard(SettingsBaseCard):
    pendingChanged = pyqtSignal(bool)

    def __init__(
        self,
        lang_manager,
        module_name: str,
        translated_name: str,
        supports_types: bool = False,
        supports_statuses: bool = False,
        supports_tags: bool = False,
        logic=None,
    ):
        # Ikon pealkirjale
        #print(f"module name {module_name.lower()}")
        icon_path = ModuleIconPaths.get_module_icon(module_name.lower())
        #print(f"icon path: {icon_path}")
        super().__init__(lang_manager, translated_name, icon_path)

        # Kasuta kanonilist võtmekuju (lowercase) KÕIKJAL
        self.module_key = (module_name).lower().strip()  # võtmekuju (nt "property")
        self.supports_archive = self.module_key == Module.PROPERTY.value

        self.supports_types = supports_types
        self.supports_statuses = supports_statuses
        self.supports_tags = supports_tags
        self.logic = logic
        self._settings = SettingsService()


        # Layer pickers
        self._layer_selector: QgsMapLayerComboBox | None = None
        self._archive_picker: QgsMapLayerComboBox | None = None

        # Originaal vs pending
        self._orig_element_name = ""
        self._orig_archive_name = ""
        self._pend_element_name = ""
        self._pend_archive_name = ""
        self._orig_status_preferences = set()
        self._pend_status_preferences = set()
        self._orig_type_preferences = set()
        self._pend_type_preferences = set()
        self._orig_tag_preferences = set()
        self._pend_tag_preferences = set()

        # Filtrite viidad
        self._status_filter_widget: StatusFilterWidget | None = None
        self._type_filter_widget: TypeFilterWidget | None = None
        self._tags_filter_widget: TagsFilterWidget | None = None

        self.placeholder_text = self.lang_manager.translate(TranslationKeys.SELECT_LAYER)

        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(1, 1, 1, 1)
        cl.setSpacing(6)

        # Layers container
        layers_container = QFrame(cw)
        layers_container.setObjectName("LayersContainer")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(8)

        primary_layer_group, primary_layer_widget = SettingsModuleFeatureCard.build_filter_group(
            parent=layers_container,
            title_key=TranslationKeys.MODULES_MAIN_LAYER,
            description_key=TranslationKeys.MAIN_LAYER_DESCRIPTION,
            group_object_name="MainLayerGroup",
            container_object_name="LayerSelectorContainer",
            widget_factory=lambda container: self._create_layer_combobox(container),
        )
        self._layer_selector = primary_layer_widget
        self._layer_selector.layerChanged.connect(self._on_primary_layer_changed)
        layers_layout.addWidget(primary_layer_group)

        if self.supports_archive:
            archive_group, archive_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=layers_container,
                title_key=TranslationKeys.ARCHIVE_LAYER,
                description_key=TranslationKeys.ARCHIVE_LAYER_DESCRIPTION,
                group_object_name="ArchiveLayerGroup",
                container_object_name="ArchivePickerContainer",
                widget_factory=lambda container: self._create_layer_combobox(container),
            )
            self._archive_picker = archive_widget
            self._archive_picker.layerChanged.connect(self._on_archive_layer_changed)
            layers_layout.addWidget(archive_group)

        cl.addWidget(layers_container)

        # Options container
        options_container = QFrame(cw)
        options_container.setObjectName("OptionsContainer")
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)

        # 1. rida – Status preferences
        first_row_container = QFrame(options_container)
        first_row_container.setObjectName("FirstRowContainer")
        first_row_layout = QHBoxLayout(first_row_container)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(8)
        options_layout.addWidget(first_row_container)

        if self.supports_statuses:
            status_group, status_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=first_row_container,
                title_key=TranslationKeys.STATUS_PREFERENCES,
                description_key=TranslationKeys.SELECT_STATUSES_DESCRIPTION,
                group_object_name="StatusPreferencesGroup",
                container_object_name="StatusContainer",
                widget_factory=lambda container: StatusFilterWidget(
                    self.module_key,
                    container,
                ),
            )
            self._status_filter_widget = status_widget
            self._status_filter_widget.selectionChanged.connect(self._on_status_selection_changed)
            first_row_layout.addWidget(status_group)

        if self.supports_tags:
            tags_group, tags_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=first_row_container,
                title_key=TranslationKeys.TAGS_PREFERENCES,
                description_key=TranslationKeys.SELECT_TAGS_DESCRIPTION,
                
                group_object_name="TagPreferencesGroup",
                container_object_name="TagsContainer",
                widget_factory=lambda container: TagsFilterWidget(
                    self.module_key,
                    self.lang_manager,
                    container,
                ),
            )
            self._tags_filter_widget = tags_widget
            self._tags_filter_widget.selectionChanged.connect(self._on_tags_selection_changed)
            first_row_layout.addWidget(tags_group)

        if self.supports_types:
            type_group, type_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=options_container,
                title_key=TranslationKeys.TYPE_PREFERENCES,
                description_key=TranslationKeys.SELECT_TYPE_DESCRIPTION,
                
                group_object_name="TypePreferencesGroup",
                container_object_name="TypeContainer",
                widget_factory=lambda container: TypeFilterWidget(
                    self.module_key,
                    container,
                ),
            )
            self._type_filter_widget = type_widget
            self._type_filter_widget.selectionChanged.connect(self._on_type_selection_changed)
            options_layout.addWidget(type_group)

        cl.addWidget(options_container)
        cl.addStretch(1)

        # Reset nupp jaluses
        reset_btn = self.reset_button()
        reset_btn.setToolTip(self.lang_manager.translate(TranslationKeys.RESET_ALL_SETTINGS))
        reset_btn.setVisible(True)
        reset_btn.clicked.connect(self._on_reset_settings)

    def _create_layer_combobox(self, parent: QWidget) -> QgsMapLayerComboBox:
        combo = QgsMapLayerComboBox(parent)
        combo.setObjectName("ModuleLayerCombo")
        combo.setAllowEmptyLayer(True, self.placeholder_text)
        combo.setShowCrs(False)
        combo.setFilters(Qgis.LayerFilter.HasGeometry)
        return combo

    def _on_primary_layer_changed(self, layer: QgsMapLayer | None) -> None:
        self._on_element_selected(layer.id() if layer else "")

    def _on_archive_layer_changed(self, layer: QgsMapLayer | None) -> None:
        if not self.supports_archive:
            return
        self._on_archive_selected(layer.id() if layer else "")


    # --- Lifecycle hooks (SettingsUI) ---
    def on_settings_activate(self, snapshot=None):
        project = QgsProject.instance() if QgsProject else None
        if self._layer_selector:
            self._layer_selector.setProject(project)
        if self.supports_archive and self._archive_picker:
            self._archive_picker.setProject(project)
        
            
        # Lae algsed layer-nimed
        self._orig_element_name = self._settings.module_main_layer_id(self.module_key) or ""
        if not self.supports_archive:
            self._orig_archive_name = ""
        else:
            self._orig_archive_name = self._settings.module_archive_layer_id(self.module_key) or ""
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Lae status/type eelistused
        self._orig_status_preferences = SettingsService.load_preferred_ids_by_key(ModuleSupports.STATUSES.value, self.module_key)
        self._pend_status_preferences = set(self._orig_status_preferences)

        if self.supports_types:
            self._orig_type_preferences = SettingsService.load_preferred_ids_by_key(ModuleSupports.TYPES.value, self.module_key)
            self._pend_type_preferences = set(self._orig_type_preferences)
        else:
            self._orig_type_preferences = set()
            self._pend_type_preferences = set()

        if self.supports_tags:
            self._orig_tag_preferences = SettingsService.load_preferred_ids_by_key(ModuleSupports.TAGS.value, self.module_key)
            self._pend_tag_preferences = set(self._orig_tag_preferences)
        else:
            self._orig_tag_preferences = set()
            self._pend_tag_preferences = set()


        # Taasta layeri valikud (vaid kui kiht on olemas)
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)

        self._update_stored_values_display()

    def on_settings_deactivate(self):
        self._cancel_filter_workers()



    # --- Persistence helpers -------------------------------------------------

    def _write_saved_layer_value(self, kind: str, layer_name: str):
        try:
            if kind == "element":
                if layer_name:
                    self._settings.module_main_layer_id(self.module_key, value=layer_name)
                else:
                    self._settings.module_main_layer_id(self.module_key, clear=True)
            else:
                if not self.supports_archive:
                    return
                if layer_name:
                    self._settings.module_archive_layer_id(self.module_key, value=layer_name)
                else:
                    self._settings.module_archive_layer_id(self.module_key, clear=True)
        except Exception:
            pass

    # --- Apply/Revert/State ---
    def has_pending_changes(self) -> bool:
        el_dirty = self._pend_element_name != self._orig_element_name
        ar_dirty = self._pend_archive_name != self._orig_archive_name
        status_dirty = self._pend_status_preferences != self._orig_status_preferences
        type_dirty = bool(self.supports_types) and self._pend_type_preferences != self._orig_type_preferences
        tag_dirty = bool(self.supports_tags) and self._pend_tag_preferences != self._orig_tag_preferences
        return el_dirty or ar_dirty or status_dirty or type_dirty or tag_dirty

    def apply(self):
        changed = False

        if self._pend_element_name != self._orig_element_name:
            self._write_saved_layer_value("element", self._pend_element_name)
            self._orig_element_name = self._pend_element_name
            self._restore_layer_selection(self._layer_selector, self._orig_element_name)
            changed = True

        if self.supports_archive and (self._pend_archive_name != self._orig_archive_name):
            self._write_saved_layer_value("archive", self._pend_archive_name)
            self._orig_archive_name = self._pend_archive_name
            if self._archive_picker:
                self._restore_layer_selection(self._archive_picker, self._orig_archive_name)
            changed = True

        # Save status prefs
        if self._pend_status_preferences != self._orig_status_preferences:
            SettingsService.save_preferred_ids_by_key(
                ModuleSupports.STATUSES.value,
                self.module_key,
                self._pend_status_preferences,
            )
            self._orig_status_preferences = set(self._pend_status_preferences)
            changed = True

        # Save tag prefs
        if self.supports_tags and (self._pend_tag_preferences != self._orig_tag_preferences):
            SettingsService.save_preferred_ids_by_key(
                ModuleSupports.TAGS.value,
                self.module_key,
                self._pend_tag_preferences,
            )
            self._orig_tag_preferences = set(self._pend_tag_preferences)
            changed = True

        # Save type prefs
        if self.supports_types and (self._pend_type_preferences != self._orig_type_preferences):
            SettingsService.save_preferred_ids_by_key(
                ModuleSupports.TYPES.value,
                self.module_key,
                self._pend_type_preferences,
            )
            self._orig_type_preferences = set(self._pend_type_preferences)
            changed = True

        # Reset pending layer ids
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        self._update_stored_values_display()
        self.pendingChanged.emit(False if changed else self.has_pending_changes())

    def revert(self):
        # Layers
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Status prefs
        self._pend_status_preferences = set(self._orig_status_preferences)
        FilterHelper.set_selected_ids(self._status_filter_widget, list(self._orig_status_preferences), emit=False)

        # Tag prefs
        if self.supports_tags:
            self._pend_tag_preferences = set(self._orig_tag_preferences)
            FilterHelper.set_selected_ids(self._tags_filter_widget, list(self._orig_tag_preferences), emit=False)


        # Type prefs
        if self.supports_types:
            self._pend_type_preferences = set(self._orig_type_preferences)
            FilterHelper.set_selected_ids(self._type_filter_widget, list(self._orig_type_preferences), emit=False)

        self._update_stored_values_display()
        self.pendingChanged.emit(False)

    def _update_stored_values_display(self):
        """Footeris voolav kokkuvõte salvestatud väärtustest."""
        try:
            def display_for(combo, fallback_name: str) -> str:
                try:
                    if combo:
                        lyr = combo.currentLayer()
                        if lyr:
                            return lyr.name()
                except Exception:
                    pass
                return fallback_name or ""

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
                values_text = " | ".join(parts)
                self.set_status_text(f"Active layers: {values_text}")
            else:
                self.set_status_text("No layers configured")
        except Exception:
            self.set_status_text("Settings loaded")


    # --- Filter handlers & Reset ---
    def _cancel_filter_workers(self):
        for widget in (
            self._status_filter_widget,
            self._type_filter_widget,
            self._tags_filter_widget,
                ):
            FilterHelper.cancel_pending_load(widget, invalidate_request=True)
            
    def _on_type_selection_changed(self, texts=None, ids=None):
        try:
            selected_ids = ids if ids is not None else self._type_filter_widget.selected_ids()
            self._pend_type_preferences = set(selected_ids or [])
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as exc:
            print(f"Error handling type selection change: {exc}")

    def _on_status_selection_changed(self, texts=None, ids=None):
        try:
            selected_ids = ids if ids is not None else FilterHelper.selected_ids(self._status_filter_widget)
            self._pend_status_preferences = {str(v) for v in (selected_ids or [])}
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as exc:
            print(f"Error handling status selection change: {exc}")

    def _on_tags_selection_changed(self, texts=None, ids=None):
        try:
            selected_ids = ids if ids is not None else FilterHelper.selected_ids(self._tags_filter_widget)
            self._pend_tag_preferences = {str(v) for v in (selected_ids or [])}
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as exc:
            print(f"Error handling tag selection change: {exc}")

    def _on_reset_settings(self):
        """Reset all stored values for this module card."""
        try:
            # Reset layer selections
            self._clear_layer_combo(self._layer_selector)
            if self.supports_archive:
                self._clear_layer_combo(self._archive_picker)
            self._pend_element_name = ""
            self._pend_archive_name = ""

            # Reset filters
            if self._status_filter_widget:
                try:
                    FilterHelper.set_selected_ids(self._status_filter_widget, [], emit=False)
                except Exception:
                    pass
            if self.supports_types and self._type_filter_widget:
                try:
                    FilterHelper.set_selected_ids(self._type_filter_widget, [], emit=False)
                except Exception:
                    pass
            if self.supports_tags and self._tags_filter_widget:
                try:
                    FilterHelper.set_selected_ids(self._tags_filter_widget, [], emit=False)
                except Exception:
                    pass

            self._orig_status_preferences = set()
            self._orig_type_preferences = set()
            self._orig_tag_preferences = set()
            self._pend_status_preferences = set()
            self._pend_type_preferences = set()
            self._pend_tag_preferences = set()

            # Clear stored settings
            self._write_saved_layer_value("element", "")
            if self.supports_archive:
                self._write_saved_layer_value("archive", "")
            self._settings.module_preferred_statuses(self.module_key, clear=True)
            if self.supports_tags:
                self._settings.module_preferred_tags(self.module_key, clear=True)
            if self.supports_types:
                self._settings.module_preferred_types(self.module_key, clear=True)

            self._update_stored_values_display()
            self.set_status_text(f"✅ {self.lang_manager.translate('Settings reset to defaults')}", True)
            self.pendingChanged.emit(self.has_pending_changes())
        except Exception as exc:
            self.set_status_text(f"❌ {self.lang_manager.translate('Reset failed')}: {exc}", True)

    # --- Eelistused (settings) ---

    def _restore_layer_selection(self, combo: QgsMapLayerComboBox | None, stored_name: str):
        """Resolve a stored layer name and update the combo selection."""
        if not combo:
            return
        try:
            resolved_id = MapHelpers.resolve_layer_id(stored_name)
        except Exception:
            resolved_id = None

        project = QgsProject.instance() if QgsProject else None
        layer = project.mapLayer(resolved_id) if (project and resolved_id) else None

        try:
            combo.blockSignals(True)
            combo.setLayer(layer)
        except Exception:
            combo.setLayer(None)
        finally:
            combo.blockSignals(False)

    def _clear_layer_combo(self, combo: QgsMapLayerComboBox | None) -> None:
        if not combo:
            return
        try:
            combo.blockSignals(True)
            combo.setLayer(None)
        finally:
            combo.blockSignals(False)

    # --- Layer valiku handlerid ---
    def _on_element_selected(self, layer_id: str):
        self._pend_element_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        self._update_stored_values_display()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        if not self.supports_archive:
            return
        self._pend_archive_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        self._update_stored_values_display()
        self.pendingChanged.emit(self.has_pending_changes())
