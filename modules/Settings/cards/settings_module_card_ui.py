"""Builds the widgets of a settings module card: layer pickers, helper buttons, preference
filters and module labels.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from qgis.core import Qgis

from .ModuleLabelsWidget import ModuleLabelsWidget
from .SettingModuleFeatureCard import SettingsModuleFeatureCard
from .settings_temp_layer_flow import PROJECTS_TEMP_LAYER_FLOW, WORKS_TEMP_LAYER_FLOW
from ....constants.button_props import ButtonSize, ButtonVariant
from ....constants.module_names import Module, ModuleSupports
from ....languages.translation_keys import TranslationKeys
from ....utils.text_helpers import to_bool
from ....widgets.Filters.NotStartedStatusFilterWidget import NotStartedStatusFilterWidget
from ....widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ....widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ....widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ....widgets.layer_tree_picker import LayerTreePicker


class SettingsModuleCardUiMixin:
    """Mixed into SettingsModuleCard, whose __init__ sets the state these builders fill."""

    def _build_ui(self):
        cw = self.content_widget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(1, 1, 1, 1)
        cl.setSpacing(6)

        cl.addWidget(self._build_layer_pickers(cw))
        if self.module_key == Module.PROPERTY.value:
            self._property_management_container = QFrame(cw)
            self._property_management_container.setObjectName("PropertyManagementContainer")
            property_management_layout = QVBoxLayout(self._property_management_container)
            property_management_layout.setContentsMargins(0, 0, 0, 0)
            property_management_layout.setSpacing(0)
            self._property_management_container.setVisible(False)
            cl.addWidget(self._property_management_container)
        self._add_helper_groups(cw, cl)
        cl.addWidget(self._build_preference_filters(cw))
        self._add_module_labels(cl)
        cl.addStretch(1)

        # Reset nupp jaluses
        reset_btn = self.reset_button()
        reset_btn.setToolTip(self.lang_manager.translate(TranslationKeys.RESET_ALL_SETTINGS))
        reset_btn.setVisible(True)
        reset_btn.clicked.connect(self._on_reset_settings)

    def _build_layer_pickers(self, cw: QWidget) -> QFrame:
        if self.module_key == Module.PROPERTY.value:
            primary_layer_title = self.lang_manager.translate(TranslationKeys.MAIN_PROPERTY_LAYER)
            primary_layer_description = self.lang_manager.translate(TranslationKeys.PROPERTY_LAYER_OVERVIEW)
        else:
            primary_layer_title = self.lang_manager.translate(TranslationKeys.MODULE_MAIN_LAYER)
            primary_layer_description = self.lang_manager.translate(TranslationKeys.MODULE_LAYER_OVERVIEW)

        layers_container = QFrame(cw)
        layers_container.setObjectName("LayersContainer")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(8)

        primary_layer_group, primary_layer_widget = SettingsModuleFeatureCard.build_filter_group(
            parent=layers_container,
            title_text=primary_layer_title,
            description_text=primary_layer_description,
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
                description_text=self.lang_manager.translate(TranslationKeys.ARCHIVE_LAYER_DESCRIPTION),
                group_object_name="ArchiveLayerGroup",
                container_object_name="ArchivePickerContainer",
                widget_factory=lambda container: self._create_layer_combobox(container),
            )
            self._archive_picker = archive_widget
            self._archive_picker.layerChanged.connect(self._on_archive_layer_changed)
            layers_layout.addWidget(archive_group)
        return layers_container

    def _add_helper_groups(self, cw: QWidget, cl: QVBoxLayout) -> None:
        """The geospatial mapper button, and the temp layer button on works and projects."""
        geospatial_mapper_group, _geospatial_mapper_button = SettingsModuleFeatureCard.build_filter_group(
            parent=cw,
            title_text=self.lang_manager.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_HELPER_TITLE),
            description_text=self.lang_manager.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_HELPER_DESCRIPTION),
            group_object_name="GeospatialLayerMapperGroup",
            container_object_name="GeospatialLayerMapperContainer",
            widget_factory=lambda container: self._create_geospatial_mapper_button(container),
        )
        self._geospatial_mapper_group = geospatial_mapper_group
        cl.addWidget(geospatial_mapper_group)

        if self.module_key == Module.WORKS.value:
            works_temp_group, _works_temp_button = SettingsModuleFeatureCard.build_filter_group(
                parent=cw,
                title_text=self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_HELPER_TITLE),
                description_text=self.lang_manager.translate(TranslationKeys.WORKS_TEMP_LAYER_HELPER_DESCRIPTION),
                group_object_name="WorksTempLayerHelperGroup",
                container_object_name="WorksTempLayerHelperContainer",
                widget_factory=lambda container: self._create_temp_layer_button(container, WORKS_TEMP_LAYER_FLOW),
            )
            self._works_temp_group = works_temp_group
            cl.addWidget(works_temp_group)

        if self.module_key == Module.PROJECT.value:
            projects_temp_group, _projects_temp_button = SettingsModuleFeatureCard.build_filter_group(
                parent=cw,
                title_text=self.lang_manager.translate(TranslationKeys.PROJECTS_TEMP_LAYER_HELPER_TITLE),
                description_text=self.lang_manager.translate(TranslationKeys.PROJECTS_TEMP_LAYER_HELPER_DESCRIPTION),
                group_object_name="ProjectsTempLayerHelperGroup",
                container_object_name="ProjectsTempLayerHelperContainer",
                widget_factory=lambda container: self._create_temp_layer_button(container, PROJECTS_TEMP_LAYER_FLOW),
            )
            cl.addWidget(projects_temp_group)

    def _build_preference_filters(self, cw: QWidget) -> QFrame:
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
                description_text=self.lang_manager.translate(TranslationKeys.SELECT_TAGS_DESCRIPTION),
                group_object_name="TagPreferencesGroup",
                container_object_name="TagsContainer",
                widget_factory=lambda container: TagsFilterWidget(
                    self.module_key,
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

        if self.supports_statuses:
            not_started_group, not_started_widget = SettingsModuleFeatureCard.build_filter_group(
                parent=options_container,
                title_text=self.lang_manager.translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_TITLE),
                description_text=self.lang_manager.translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_DESCRIPTION),
                group_object_name="ProjectBoardNotStartedStatusesGroup",
                container_object_name="ProjectBoardNotStartedStatusesContainer",
                widget_factory=lambda container: NotStartedStatusFilterWidget(
                    self.module_key,
                    container,
                    settings_logic=self.logic,
                    auto_load=False,
                ),
            )
            self._not_started_status_filter_widget = not_started_widget
            self._not_started_status_filter_widget.selectionChanged.connect(
                lambda texts=None, ids=None: self._on_not_started_status_selection_changed(
                    widget=self._not_started_status_filter_widget,
                    ids=ids,
                )
            )
            self._install_lazy_filter_loader(self._not_started_status_filter_widget)
            options_layout.addWidget(not_started_group)
        return options_container

    def _add_module_labels(self, cl: QVBoxLayout) -> None:
        if not self._module_labels:
            return
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

    def _create_geospatial_mapper_button(self, parent: QWidget) -> QPushButton:
        button = QPushButton(
            self.lang_manager.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_OPEN_BUTTON),
            parent,
        )
        button.setObjectName("GeospatialLayerMapperButton")
        button.setProperty("variant", ButtonVariant.SUCCESS)
        button.setProperty("btnSize", ButtonSize.SMALL)
        button.setAutoDefault(False)
        button.setDefault(False)
        button.clicked.connect(self._on_open_geospatial_mapper_clicked)
        return button

    def _create_layer_combobox(self, parent: QWidget) -> LayerTreePicker:
        combo = LayerTreePicker(parent)
        combo.setAllowEmptyLayer(True, self.placeholder_text)
        combo.setShowCrs(False)
        combo.setFilters(Qgis.LayerFilter.HasGeometry)
        return combo
