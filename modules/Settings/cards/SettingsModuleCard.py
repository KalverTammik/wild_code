

from typing import Any

from PyQt5.QtWidgets import QVBoxLayout,  QFrame, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer, QEvent
from .SettingsBaseCard import SettingsBaseCard
from .SettingModuleFeatureCard import SettingsModuleFeatureCard
from .ModuleLabelsWidget import ModuleLabelsWidget
from ..SettinsUtils.SettingsLogic import SettingsLogic
from ..settings_layer_helper import SettingsLayerHelper
from ...works.works_temp_layer_helper import WorksTempLayerHelper
from ....widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ....widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ....widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ....constants.module_icons import ModuleIconPaths
from ....constants.button_props import ButtonVariant, ButtonSize
from ....utils.url_manager import Module
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.FilterHelpers.FilterHelper import FilterHelper
from ....utils.url_manager import ModuleSupports
from ....languages.translation_keys import TranslationKeys
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.messagesHelper import ModernMessageDialog
from ....utils.text_helpers import to_bool

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

    def _log_error(self, event: str, exc: Exception, *, extra: dict | None = None) -> None:
        PythonFailLogger.log_exception(
            exc,
            module=Module.SETTINGS.value,
            event=event,
            extra=extra,
        )


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

        if self.module_key == Module.WORKS.value:
            works_temp_group, _works_temp_button = SettingsModuleFeatureCard.build_filter_group(
                parent=cw,
                title_text=self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_HELPER_TITLE),
                lang_manager=self.lang_manager,
                description_text=self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_HELPER_DESCRIPTION),
                group_object_name="WorksTempLayerHelperGroup",
                container_object_name="WorksTempLayerHelperContainer",
                widget_factory=lambda container: self._create_works_temp_layer_button(container),
            )
            cl.addWidget(works_temp_group)

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
            self._connect_preference_selection(self._status_filter_widget, ModuleSupports.STATUSES.value)
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
            self._connect_preference_selection(self._tags_filter_widget, ModuleSupports.TAGS.value)
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
            self._connect_preference_selection(self._type_filter_widget, ModuleSupports.TYPES.value)
            self._install_lazy_filter_loader(self._type_filter_widget)
            options_layout.addWidget(type_group)

        cl.addWidget(options_container)

        labels_widget = None
        if self._module_labels:
            loaded_label_values = self.logic.load_module_label_values(self.module_key, self._module_labels)
            prepared_labels = []
            for label_def in self._module_labels:
                key = label_def.get("key")
                stored_value = loaded_label_values.get(key, "") if key else ""
                if key:
                    label_def = dict(label_def)
                    tool = label_def.get("tool")
                    if tool == "checkBox":
                        label_def["value"] = to_bool(stored_value)
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

    def _create_works_temp_layer_button(self, parent: QWidget) -> QPushButton:
        button = QPushButton(
            self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_CREATE_BUTTON),
            parent,
        )
        button.setObjectName("WorksTempLayerCreateButton")
        button.setProperty("variant", ButtonVariant.WARNING)
        button.setProperty("btnSize", ButtonSize.SMALL)
        button.setAutoDefault(False)
        button.setDefault(False)
        button.clicked.connect(self._on_create_temp_works_layer_clicked)
        return button

    def _on_create_temp_works_layer_clicked(self) -> None:
        preferred_layer = self._layer_selector.currentLayer() if self._layer_selector else None
        reference_layer = WorksTempLayerHelper.resolve_reference_layer(preferred_layer)
        if reference_layer is None:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_REFERENCE_REQUIRED),
            )
            return

        if not WorksTempLayerHelper.gpkg_path_for_layer(reference_layer):
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_GPKG_REQUIRED),
            )
            return

        default_name = (
            self._pend_element_name
            or self._orig_element_name
            or WorksTempLayerHelper.DEFAULT_LAYER_NAME
        )
        layer_name, ok = ModernMessageDialog.get_text_modern(
            self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_PROMPT_TITLE),
            self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_PROMPT_LABEL),
            text=default_name,
        )
        if not ok:
            return

        normalized_name = (layer_name or "").strip()
        if not normalized_name:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_NAME_REQUIRED),
            )
            return

        created_layer, error_text = WorksTempLayerHelper.create_or_load_layer(
            reference_layer,
            normalized_name,
        )
        if created_layer is None or not created_layer.isValid():
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_CREATE_FAILED).format(
                    name=normalized_name,
                    error=error_text or self.lang_manager.translate(TranslationKeys.ERROR),
                ),
            )
            return

        actual_name = created_layer.name() or normalized_name
        self._write_saved_layer_value("element", actual_name)
        self.sync_main_layer_selection(actual_name, force=True)

        ModernMessageDialog.show_info(
            self.lang_manager.translate(TranslationKeys.SUCCESS),
            self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_READY).format(name=actual_name),
        )

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

    def _set_status_text_if_changed(self, text: str, visible: bool = True) -> None:
        if self._last_status_text == text:
            return
        self._last_status_text = text
        self.set_status_text(text, visible)

    def _preference_specs(self):
        return (
            (True, ModuleSupports.STATUSES.value, "_orig_status_preferences", "_pend_status_preferences", self._status_filter_widget),
            (self.supports_tags, ModuleSupports.TAGS.value, "_orig_tag_preferences", "_pend_tag_preferences", self._tags_filter_widget),
            (self.supports_types, ModuleSupports.TYPES.value, "_orig_type_preferences", "_pend_type_preferences", self._type_filter_widget),
        )

    def _load_preference_states(self) -> None:
        for enabled, support_key, orig_attr, pend_attr, _widget in self._preference_specs():
            if not enabled:
                setattr(self, orig_attr, set())
                setattr(self, pend_attr, set())
                continue
            loaded = set(
                self.logic.load_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                )
            )
            setattr(self, orig_attr, loaded)
            setattr(self, pend_attr, set(loaded))

    def _save_preference_states(self) -> bool:
        changed = False
        for enabled, support_key, orig_attr, pend_attr, _widget in self._preference_specs():
            if not enabled:
                continue
            original = getattr(self, orig_attr)
            pending = getattr(self, pend_attr)
            if pending != original:
                self.logic.save_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                    ids=pending,
                )
                setattr(self, orig_attr, set(pending))
                changed = True
        return changed

    def _revert_preference_states(self) -> None:
        for enabled, _support_key, orig_attr, pend_attr, widget in self._preference_specs():
            original = set(getattr(self, orig_attr))
            setattr(self, pend_attr, set(original))
            if enabled and widget is not None:
                widget.set_selected_ids(list(original), emit=False)

    def _clear_preference_states_and_storage(self) -> None:
        for enabled, support_key, orig_attr, pend_attr, widget in self._preference_specs():
            if widget is not None:
                widget.set_selected_ids([], emit=False)
            setattr(self, orig_attr, set())
            setattr(self, pend_attr, set())
            if enabled:
                self.logic.clear_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                )

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
                        self._log_error("settings_module_filter_lazy_load_failed", exc, extra={"widget": type(obj).__name__})
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
                        continue
        return super().eventFilter(obj, event)


    # --- Lifecycle hooks (SettingsUI) ---
    def on_settings_activate(self, snapshot=None):
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
            self._type_filter_widget,
            self._tags_filter_widget,
        ):
            if widget is None:
                continue
            clear_fn = getattr(widget, "clear_data", None)
            if callable(clear_fn):
                try:
                    clear_fn()
                except Exception:
                    continue

        if self._labels_widget:
            clear_labels = getattr(self._labels_widget, "clear_data", None)
            if callable(clear_labels):
                try:
                    clear_labels()
                except Exception:
                    pass
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
            SettingsLayerHelper.restore_combo_selection(self._layer_selector, self._orig_element_name)
            changed = True

        if self.supports_archive and (self._pend_archive_name != self._orig_archive_name):
            self._write_saved_layer_value("archive", self._pend_archive_name)
            self._orig_archive_name = self._pend_archive_name
            if self._archive_picker:
                SettingsLayerHelper.restore_combo_selection(self._archive_picker, self._orig_archive_name)
            changed = True

        changed = self._save_preference_states() or changed

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
        self._restore_layer_selections(
            element_name=self._orig_element_name,
            archive_name=self._orig_archive_name,
        )
        self._pend_element_name = self._orig_element_name
        self._pend_archive_name = self._orig_archive_name

        self._revert_preference_states()

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
                except Exception:
                    return fallback_name or ""
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
                values_text = ", ".join(parts)
                self._set_status_text_if_changed(f"Active layers: {values_text}")
            else:
                self._set_status_text_if_changed("No layers configured")
        except Exception as exc:
            self._log_error("settings_module_update_status_failed", exc)
            self._set_status_text_if_changed("Settings loaded")


    # --- Filter handlers & Reset ---
    def _cancel_filter_workers(self):
        for widget in (
            self._status_filter_widget,
            self._type_filter_widget,
            self._tags_filter_widget,
                ):
            FilterHelper.cancel_pending_load(widget, invalidate_request=True)

    @staticmethod
    def _preference_error_event(support_key: str) -> str:
        return {
            ModuleSupports.STATUSES.value: "settings_module_status_selection_failed",
            ModuleSupports.TAGS.value: "settings_module_tags_selection_failed",
            ModuleSupports.TYPES.value: "settings_module_type_selection_failed",
        }.get(support_key, "settings_module_preference_selection_failed")

    def _apply_pending_preference_set(self, support_key: str, values: set) -> None:
        if support_key == ModuleSupports.STATUSES.value:
            self._pend_status_preferences = values
            return
        if support_key == ModuleSupports.TAGS.value:
            self._pend_tag_preferences = values
            return
        if support_key == ModuleSupports.TYPES.value:
            self._pend_type_preferences = values

    @staticmethod
    def _stringify_preference_ids(support_key: str) -> bool:
        return support_key in (ModuleSupports.STATUSES.value, ModuleSupports.TAGS.value)

    def _connect_preference_selection(self, widget, support_key: str) -> None:
        if widget is None:
            return
        widget.selectionChanged.connect(
            lambda texts=None, ids=None: self._on_preference_selection_changed(
                support_key=support_key,
                widget=widget,
                ids=ids,
            )
        )

    def _on_preference_selection_changed(self, *, support_key: str, widget, ids=None) -> None:
        try:
            selected_ids = ids if ids is not None else (widget.selected_ids() if widget is not None else [])
            stringify = self._stringify_preference_ids(support_key)
            normalized = {str(v) for v in (selected_ids or [])} if stringify else set(selected_ids or [])
            self._apply_pending_preference_set(support_key, normalized)
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            self._log_error(self._preference_error_event(support_key), exc)

    def _on_reset_settings(self):
        """Reset all stored values for this module card."""
        try:
            # Reset layer selections
            SettingsLayerHelper.clear_combo_selection(self._layer_selector)
            if self.supports_archive:
                SettingsLayerHelper.clear_combo_selection(self._archive_picker)
            self._pend_element_name = ""
            self._pend_archive_name = ""

            # Reset filters and clear stored preference settings
            self._clear_preference_states_and_storage()

            # Clear stored layer settings
            self._write_saved_layer_value("element", "")
            if self.supports_archive:
                self._write_saved_layer_value("archive", "")

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
        layer_name = MapHelpers.layer_name_from_id(layer_id) if layer_id else ""
        setattr(self, target_attr, layer_name)
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

