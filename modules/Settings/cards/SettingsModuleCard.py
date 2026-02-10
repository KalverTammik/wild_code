

from typing import Any

from PyQt5.QtWidgets import QVBoxLayout,  QFrame, QHBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, QTimer, QEvent
from .SettingsBaseCard import SettingsBaseCard
from .SettingModuleFeatureCard import SettingsModuleFeatureCard
from .ModuleLabelsWidget import ModuleLabelsWidget
from ..SettinsUtils.SettingsLogic import SettingsLogic
from ....widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ....widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ....widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ....constants.module_icons import ModuleIconPaths
from ....utils.url_manager import Module
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.FilterHelpers.FilterHelper import FilterHelper
from ....utils.url_manager import ModuleSupports
from ....languages.translation_keys import TranslationKeys
from ....Logs.python_fail_logger import PythonFailLogger

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
        supports_archive_layer: bool = False,
        module_labels=None,
        logic=None,
    ):
        # Ikon pealkirjale
        #print(f"module name {module_name.lower()}")
        icon_path = ModuleIconPaths.get_module_icon(module_name.lower())
        #print(f"icon path: {icon_path}")
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
        self._layer_selector: QgsMapLayerComboBox | None = None
        self._archive_picker: QgsMapLayerComboBox | None = None

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


    def set_module_label_value(self, key: str, value: str):
        if self._labels_widget:
            self._labels_widget.set_label_value(key, value)

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
            title_text=self.lang_manager.translate(TranslationKeys.MAIN_PROPERTY_LAYER),
            lang_manager=self.lang_manager,
            description_text=self.lang_manager.translate(TranslationKeys.PROPERTY_LAYER_OVERVIEW),
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
                title_text=self.lang_manager.translate(TranslationKeys.ARCHIVE_LAYER),
                lang_manager=self.lang_manager,
                description_text=self.lang_manager.translate(TranslationKeys.ARCHIVE_LAYER_DESCRIPTION),
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
                title_text=self.lang_manager.translate(TranslationKeys.STATUS_PREFERENCES),
                lang_manager=self.lang_manager,
                description_text=self.lang_manager.translate(TranslationKeys.SELECT_STATUSES_DESCRIPTION),
                group_object_name="StatusPreferencesGroup",
                container_object_name="StatusContainer",
                widget_factory=lambda container: StatusFilterWidget(
                    self.module_key,
                    container,
                    settings_logic=self.logic,
                    auto_load=False,
                ),
            )
            self._status_filter_widget = status_widget
            self._status_filter_widget.selectionChanged.connect(self._on_status_selection_changed)
            self._install_lazy_filter_loader(self._status_filter_widget)
            first_row_layout.addWidget(status_group)

        if self.supports_tags:
            tags_group, tags_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=first_row_container,
                title_text=self.lang_manager.translate(TranslationKeys.TAGS_PREFERENCES),
                lang_manager=self.lang_manager,
                description_text=self.lang_manager.translate(TranslationKeys.SELECT_TAGS_DESCRIPTION),
                
                group_object_name="TagPreferencesGroup",
                container_object_name="TagsContainer",
                widget_factory=lambda container: TagsFilterWidget(
                    self.module_key,
                    self.lang_manager,
                    container,
                    settings_logic=self.logic,
                    auto_load=False,
                ),
            )
            self._tags_filter_widget = tags_widget
            self._tags_filter_widget.selectionChanged.connect(self._on_tags_selection_changed)
            self._install_lazy_filter_loader(self._tags_filter_widget)
            first_row_layout.addWidget(tags_group)

        if self.supports_types:
            type_group, type_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=options_container,
                title_text=self.lang_manager.translate(TranslationKeys.TYPE_PREFERENCES),
                lang_manager=self.lang_manager,
                description_text=self.lang_manager.translate(TranslationKeys.SELECT_TYPE_DESCRIPTION),
                
                group_object_name="TypePreferencesGroup",
                container_object_name="TypeContainer",
                widget_factory=lambda container: TypeFilterWidget(
                    self.module_key,
                    container,
                    settings_logic=self.logic,
                    auto_load=False,
                ),
            )
            self._type_filter_widget = type_widget
            self._type_filter_widget.selectionChanged.connect(self._on_type_selection_changed)
            self._install_lazy_filter_loader(self._type_filter_widget)
            options_layout.addWidget(type_group)

        cl.addWidget(options_container)

        labels_widget = None
        if self._module_labels:
            prepared_labels = []
            for label_def in self._module_labels:
                key = label_def.get("key")
                stored_value = self.logic.load_module_label_value(self.module_key, key) if key else ""
                if key:
                    label_def = dict(label_def)
                    tool = label_def.get("tool")
                    if tool == "checkBox":
                        label_def["value"] = self._as_bool(stored_value)
                    else:
                        label_def["value"] = stored_value or ""
                prepared_labels.append(label_def)

            labels_widget = ModuleLabelsWidget(self.module_key, prepared_labels, self.lang_manager)
            self._labels_widget = labels_widget
            for label_def in prepared_labels:
                key = label_def.get("key")
                if key:
                    val = label_def.get("value")
                    if val is None:
                        val = False if label_def.get("tool") == "checkBox" else ""
                    self._orig_label_values[key] = val
                    self._pend_label_values[key] = val
            labels_widget.labelChanged.connect(self._on_label_changed)
            cl.addWidget(labels_widget)

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

    def _set_layer_combo_project(self, combo: QgsMapLayerComboBox | None, project) -> None:
        if combo is None:
            return
        try:
            current = combo.project() if hasattr(combo, "project") else None
            if current is project:
                return
        except Exception:
            pass
        combo.setProject(project)

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
            except Exception:
                sip = None

            self._pending_emit_scheduled = False
            if self._last_pending_state is None:
                return
            try:
                if sip and sip.isdeleted(self):
                    return
            except Exception:
                return
            if hasattr(self, "isVisible") and not self.isVisible():
                return
            self.pendingChanged.emit(bool(self._last_pending_state))

        QTimer.singleShot(0, _flush)

    def _install_lazy_filter_loader(self, widget: QWidget | None) -> None:
        if widget is None:
            return
        targets = [widget]
        combo = getattr(widget, "combo", None)
        if combo is not None:
            targets.append(combo)
        group_combo = getattr(widget, "group_combo", None)
        if group_combo is not None:
            targets.append(group_combo)
        type_combo = getattr(widget, "type_combo", None)
        if type_combo is not None:
            targets.append(type_combo)

        for target in targets:
            if target is None:
                continue
            self._lazy_filter_widgets.add(target)
            target.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj in self._lazy_filter_widgets:
            if event.type() in (QEvent.MouseButtonPress, QEvent.FocusIn, QEvent.Show):
                ensure_loaded = getattr(obj, "ensure_loaded", None)
                if callable(ensure_loaded):
                    try:
                        ensure_loaded()
                    except Exception as exc:
                        PythonFailLogger.log_exception(
                            exc,
                            module="settings",
                            event="settings_module_filter_lazy_load_failed",
                            extra={"widget": type(obj).__name__},
                        )
                to_remove = {obj}
                for target in list(self._lazy_filter_widgets):
                    if target is obj:
                        continue
                    owner = None
                    try:
                        owner = target.parent()
                    except Exception:
                        owner = None
                    if owner is obj:
                        to_remove.add(target)
                for target in to_remove:
                    self._lazy_filter_widgets.discard(target)
                    try:
                        target.removeEventFilter(self)
                    except Exception:
                        pass
        return super().eventFilter(obj, event)


    # --- Lifecycle hooks (SettingsUI) ---
    def on_settings_activate(self, snapshot=None):
        project = QgsProject.instance() if QgsProject else None
        if project is not None and not self._project_bound:
            self._set_layer_combo_project(self._layer_selector, project)
            if self.supports_archive and self._archive_picker:
                self._set_layer_combo_project(self._archive_picker, project)
            self._project_bound = True
        self._connect_layer_signals()
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

        # Lae status/type eelistused
        self._orig_status_preferences = set(
            self.logic.load_module_preference_ids(
                self.module_key,
                support_key=ModuleSupports.STATUSES.value,
            )
        )
        self._pend_status_preferences = set(self._orig_status_preferences)
        # Load label values from settings and sync UI
        self._orig_label_values = self._load_label_values()
        self._pend_label_values = dict(self._orig_label_values)
        if self._labels_widget:
            for k, v in self._orig_label_values.items():
                self._labels_widget.set_label_value(k, v)

        if self.supports_types:
            self._orig_type_preferences = set(
                self.logic.load_module_preference_ids(
                    self.module_key,
                    support_key=ModuleSupports.TYPES.value,
                )
            )
            self._pend_type_preferences = set(self._orig_type_preferences)
        else:
            self._orig_type_preferences = set()
            self._pend_type_preferences = set()

        if self.supports_tags:
            self._orig_tag_preferences = set(
                self.logic.load_module_preference_ids(
                    self.module_key,
                    support_key=ModuleSupports.TAGS.value,
                )
            )
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
        self._disconnect_layer_signals()
        # Clear filter widgets to release memory
        for widget in (
            self._status_filter_widget,
            self._type_filter_widget,
            self._tags_filter_widget,
        ):
            if widget is None:
                continue
            clear_fn = getattr(widget, "clear_data", None)
            if callable(clear_fn):
                try:
                    clear_fn()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_filter_clear_failed",
                        extra={"widget": type(widget).__name__},
                    )

        if self._labels_widget:
            clear_labels = getattr(self._labels_widget, "clear_data", None)
            if callable(clear_labels):
                try:
                    clear_labels()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_labels_clear_failed",
                    )
        try:
            self._set_status_text_if_changed("")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_clear_status_failed",
            )

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
        type_dirty = bool(self.supports_types) and self._pend_type_preferences != self._orig_type_preferences
        tag_dirty = bool(self.supports_tags) and self._pend_tag_preferences != self._orig_tag_preferences
        label_dirty = any(
            self._pend_label_values.get(k, "") != self._orig_label_values.get(k, "")
            for k in set(self._pend_label_values.keys()) | set(self._orig_label_values.keys())
        )
        return el_dirty or ar_dirty or status_dirty or type_dirty or tag_dirty or label_dirty

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
            self.logic.save_module_preference_ids(
                self.module_key,
                support_key=ModuleSupports.STATUSES.value,
                ids=self._pend_status_preferences,
            )
            self._orig_status_preferences = set(self._pend_status_preferences)
            changed = True

        # Save tag prefs
        if self.supports_tags and (self._pend_tag_preferences != self._orig_tag_preferences):
            self.logic.save_module_preference_ids(
                self.module_key,
                support_key=ModuleSupports.TAGS.value,
                ids=self._pend_tag_preferences,
            )
            self._orig_tag_preferences = set(self._pend_tag_preferences)
            changed = True

        # Save type prefs
        if self.supports_types and (self._pend_type_preferences != self._orig_type_preferences):
            self.logic.save_module_preference_ids(
                self.module_key,
                support_key=ModuleSupports.TYPES.value,
                ids=self._pend_type_preferences,
            )
            self._orig_type_preferences = set(self._pend_type_preferences)
            changed = True

        # Save label values
        for key, value in self._pend_label_values.items():
            if self._orig_label_values.get(key, "") != value:
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
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        # Status prefs
        self._pend_status_preferences = set(self._orig_status_preferences)
        if self._status_filter_widget:
            self._status_filter_widget.set_selected_ids(list(self._orig_status_preferences), emit=False)

        # Tag prefs
        if self.supports_tags:
            self._pend_tag_preferences = set(self._orig_tag_preferences)
            if self._tags_filter_widget:
                self._tags_filter_widget.set_selected_ids(list(self._orig_tag_preferences), emit=False)


        # Type prefs
        if self.supports_types:
            self._pend_type_preferences = set(self._orig_type_preferences)
            if self._type_filter_widget:
                self._type_filter_widget.set_selected_ids(list(self._orig_type_preferences), emit=False)

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
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_display_for_failed",
                    )
                return fallback_name or ""

            element_name = display_for(self._layer_selector, self._pend_element_name or self._orig_element_name)
            supports_archive_layer: bool = False
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
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_update_status_failed",
            )
            self._set_status_text_if_changed("Settings loaded")


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
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_type_selection_failed",
            )

    def _on_status_selection_changed(self, texts=None, ids=None):
        try:
            selected_ids = ids if ids is not None else self._status_filter_widget.selected_ids()
            self._pend_status_preferences = {str(v) for v in (selected_ids or [])}
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_status_selection_failed",
            )

    def _on_tags_selection_changed(self, texts=None, ids=None):
        try:
            selected_ids = ids if ids is not None else self._tags_filter_widget.selected_ids()
            self._pend_tag_preferences = {str(v) for v in (selected_ids or [])}
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_tags_selection_failed",
            )

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
                    self._status_filter_widget.set_selected_ids([], emit=False)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_reset_status_failed",
                    )
            if self.supports_types and self._type_filter_widget:
                try:
                    self._type_filter_widget.set_selected_ids([], emit=False)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_reset_type_failed",
                    )
            if self.supports_tags and self._tags_filter_widget:
                try:
                    self._tags_filter_widget.set_selected_ids([], emit=False)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="settings",
                        event="settings_module_reset_tags_failed",
                    )

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
            self.logic.clear_module_preference_ids(
                self.module_key,
                support_key=ModuleSupports.STATUSES.value,
            )
            if self.supports_tags:
                self.logic.clear_module_preference_ids(
                    self.module_key,
                    support_key=ModuleSupports.TAGS.value,
                )
            if self.supports_types:
                self.logic.clear_module_preference_ids(
                    self.module_key,
                    support_key=ModuleSupports.TYPES.value,
                )

            # Clear label values
            for key in list(self._orig_label_values.keys()):
                self.logic.clear_module_label_value(self.module_key, key)
                if self._labels_widget:
                    self._labels_widget.set_label_value(key, "")
            self._orig_label_values = {}
            self._pend_label_values = {}

            self._update_stored_values_display()
            self.set_status_text(f"✅ {self.lang_manager.translate('Settings reset to defaults')}", True)
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            self.set_status_text(f"❌ {self.lang_manager.translate('Reset failed')}: {exc}", True)

    # --- Eelistused (settings) ---

    def _restore_layer_selection(self, combo: QgsMapLayerComboBox | None, stored_name: str):
        """Resolve a stored layer name and update the combo selection."""
        if not combo:
            return
        try:
            resolved_id = MapHelpers.resolve_layer_id(stored_name)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_resolve_layer_failed",
            )
            resolved_id = None

        project = QgsProject.instance() if QgsProject else None
        layer = project.mapLayer(resolved_id) if (project and resolved_id) else None

        try:
            combo.blockSignals(True)
            combo.setLayer(layer)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_set_layer_failed",
            )
            combo.setLayer(None)
        finally:
            combo.blockSignals(False)

    def _connect_layer_signals(self) -> None:
        if self._layer_signals_connected:
            return
        project = QgsProject.instance() if QgsProject else None
        if project is None:
            return
        try:
            project.layersAdded.connect(self._on_project_layers_changed)
            project.layersRemoved.connect(self._on_project_layers_changed)
            self._layer_signals_connected = True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_layer_signal_connect_failed",
            )

    def _disconnect_layer_signals(self) -> None:
        if not self._layer_signals_connected:
            return
        project = QgsProject.instance() if QgsProject else None
        if project is None:
            self._layer_signals_connected = False
            return
        try:
            project.layersAdded.disconnect(self._on_project_layers_changed)
            project.layersRemoved.disconnect(self._on_project_layers_changed)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="settings",
                event="settings_module_layer_signal_disconnect_failed",
            )
        finally:
            self._layer_signals_connected = False

    def _on_project_layers_changed(self, *args) -> None:
        self._restore_layer_selection(self._layer_selector, self._orig_element_name)
        if self.supports_archive and self._archive_picker:
            self._restore_layer_selection(self._archive_picker, self._orig_archive_name)

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
        self._emit_pending_changed(self.has_pending_changes())

    def _on_archive_selected(self, layer_id: str):
        if not self.supports_archive:
            return
        self._pend_archive_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        self._update_stored_values_display()
        self._emit_pending_changed(self.has_pending_changes())

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
            self._restore_layer_selection(self._archive_picker, normalized)

        self._update_stored_values_display()
        self._emit_pending_changed(self.has_pending_changes())
        return True

    def _on_label_changed(self, key: str, value: Any):
        if not key:
            return
        self._pend_label_values[key] = value
        self._emit_pending_changed(self.has_pending_changes())

    def _load_label_values(self):
        values = {}
        for label_def in self._module_labels:
            key = label_def.get("key")
            if not key:
                continue
            stored = self.logic.load_module_label_value(self.module_key, key) or ""
            values[key] = stored
        return values

    def _as_bool(self, value: Any) -> bool:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off", ""}:
                return False
        return bool(value)
