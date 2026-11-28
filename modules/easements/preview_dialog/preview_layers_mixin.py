from __future__ import annotations
from qgis.core import QgsProject
from ....constants.file_paths import QmlPaths
from ....engines.LayerCreationEngine import MailablGroupFolders
from ....languages.translation_keys import TranslationKeys
from ....utils.MapTools.item_selector_tools import PropertiesSelectors
from ....utils.layers import LayerProcessingService, MemoryLayerResultService
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.project_base_layers import ProjectBaseLayersService
from ....constants.module_names import Module
from ..easement_distance_rules import (
    format_distance, row_distance,
)
from ..easement_property_edges import (
    property_cut_areas,
)


class EasementPreviewLayersMixin:
    """The preview layers on the map: one buffer per network row, the property buffer, the
    final cut and their removal. Mixed into EasementPreviewDialog, whose __init__ creates
    the state used here.
    """

    def _resolve_preview_layer_by_name(self, layer_name: str):
        if not layer_name:
            return None
        matches = QgsProject.instance().mapLayersByName(layer_name)
        for layer in matches:
            try:
                if layer.isValid():
                    return layer
            except RuntimeError:
                continue
        return None

    def _resolve_final_preview_layer(self):
        return self._resolve_preview_layer_by_name(self._final_preview_name or self._final_preview_layer_name())

    def _ensure_final_cut_layer(self):
        final_layer = self._resolve_final_preview_layer()
        if final_layer is not None:
            return final_layer, ""

        final_status = self._create_final_cut_preview(remove_other_previews_on_success=False)
        final_layer = self._resolve_final_preview_layer()
        return final_layer, str(final_status or "")

    # native:buffer values: END_CAP_STYLE 0 round, 1 flat; JOIN_STYLE 0 round, 1 miter.
    def _buffer_end_cap_style(self) -> int:
        return 0 if self._round_ends_checkbox.isChecked() else 1

    def _buffer_join_style(self) -> int:
        return 0 if self._rounded_corners_checkbox.isChecked() else 1

    def _preview_name_for(self, layer_key: str) -> str:
        layer_title = self._lang.translate(self._LAYER_LABEL_KEYS[layer_key])
        return f"{self._lang.translate(TranslationKeys.PREVIEW_EASEMENT)} · {self._item_number or self._item_id or '-'} · {layer_title}"

    def _final_preview_layer_name(self) -> str:
        return f"{self._lang.translate(TranslationKeys.PREVIEW_EASEMENT_AREA)} · {self._item_number or self._item_id or '-'}"

    def _cut_preview_name_for(self, layer_key: str) -> str:
        layer_title = self._lang.translate(self._LAYER_LABEL_KEYS[layer_key])
        return f"{self._lang.translate(TranslationKeys.PREVIEW_EASEMENT_CUT)} · {self._item_number or self._item_id or '-'} · {layer_title}"

    def _merged_cut_preview_name(self) -> str:
        return f"{self._lang.translate(TranslationKeys.PREVIEW_EASEMENT_CUT_MERGE)} · {self._item_number or self._item_id or '-'}"

    def _resolve_source_layer(self, layer_key: str):
        return ProjectBaseLayersService.resolve_layer(layer_key, include_legacy=True)

    def _effective_row_distance(self, layer_key: str, source_layer) -> float:
        calculated = row_distance(layer_key, source_layer, default_depth=float(self._distance_spin.value()))
        if calculated is not None:
            return float(calculated)
        return float(self._distance_spin.value())

    def _move_property_preview_to_bottom(self) -> None:
        if not self._property_preview_name:
            return
        matches = MemoryLayerResultService._project().mapLayersByName(self._property_preview_name)
        if not matches:
            return
        property_layer = matches[0]
        MemoryLayerResultService.move_layer_to_group_end(
            property_layer,
            group_name=MailablGroupFolders.SANDBOXING,
        )

    def _rerun_automation(self) -> None:
        if self._automation_running:
            return

        self._automation_running = True
        try:
            removed = 0
            self._clear_auto_selections()
            for preview_name in list(self._preview_layer_names):
                removed += MemoryLayerResultService.remove_existing(preview_name, only_memory=True)
            self._preview_layer_names.clear()
            if self._property_preview_name:
                removed += MemoryLayerResultService.remove_existing(self._property_preview_name, only_memory=True)
            if self._final_preview_name:
                removed += MemoryLayerResultService.remove_existing(self._final_preview_name, only_memory=True)
            for key in self._ROW_KEYS:
                self._set_row_status(key, "")
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CLEARED).format(count=removed)
            )
            self._reset_area_calculations()
            self._initialize_connected_property_flow(refresh_from_backend=False)
        finally:
            self._automation_running = False

    def _create_preview(self, layer_key: str) -> None:
        source_layer = self._resolve_source_layer(layer_key)
        if source_layer is None:
            self._set_row_status(layer_key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING))
            return

        try:
            selected_count = int(source_layer.selectedFeatureCount() or 0)
        except (AttributeError, RuntimeError):
            selected_count = 0
        if selected_count <= 0:
            self._set_row_status(layer_key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED))
            return

        preview_name = self._preview_name_for(layer_key)
        style_path = self._STYLE_PATHS.get(layer_key)
        distance = self._effective_row_distance(layer_key, source_layer)

        preview_layer = LayerProcessingService.buffer_selected_features(
            source_layer,
            distance=float(distance),
            result_layer_name=preview_name,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=style_path,
            replace_existing=True,
            end_cap_style=self._buffer_end_cap_style(),
            join_style=self._buffer_join_style(),
            custom_properties={
                "kavitro/easement_preview": "true",
                "kavitro/easement_id": self._item_id,
                "kavitro/easement_layer_key": layer_key,
            },
            make_visible=True,
            make_active=False,
        )
        if preview_layer is None:
            self._set_row_status(layer_key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_FAILED))
            return

        self._preview_layer_names.add(preview_name)
        self._set_row_status(
            layer_key,
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_CREATED).format(
                count=selected_count,
                distance=format_distance(distance),
            ),
        )
        self._move_property_preview_to_bottom()
        self._status_label.setText(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CREATED).format(
                preview=preview_layer.name(),
                source=source_layer.name(),
                count=f"{selected_count} · {format_distance(distance)} m",
            )
        )

    def _remove_preview(self, layer_key: str) -> int:
        preview_name = self._preview_name_for(layer_key)
        removed = MemoryLayerResultService.remove_existing(preview_name, only_memory=True)
        if removed > 0:
            self._preview_layer_names.discard(preview_name)
        self._refresh_layer_labels()
        return removed

    def _clear_previews(self) -> None:
        removed = 0
        self._clear_auto_selections()
        for preview_name in list(self._preview_layer_names):
            removed += MemoryLayerResultService.remove_existing(preview_name, only_memory=True)
        self._preview_layer_names.clear()
        if self._property_preview_name:
            removed += MemoryLayerResultService.remove_existing(self._property_preview_name, only_memory=True)
            self._property_preview_name = ""
        if self._final_preview_name:
            removed += MemoryLayerResultService.remove_existing(self._final_preview_name, only_memory=True)
            self._final_preview_name = ""
        self._reset_area_calculations()
        for key in self._ROW_KEYS:
            self._set_row_status(key, "")
        self._status_label.setText(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CLEARED).format(count=removed)
        )
        self._refresh_layer_labels()
        self._refresh_property_summary_card()

    def _cleanup_named_layers(self, layer_names: list[str]) -> None:
        for layer_name in layer_names or []:
            if not layer_name:
                continue
            try:
                MemoryLayerResultService.remove_existing(layer_name, only_memory=True)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.EASEMENT.value,
                    event="easement_named_layers_cleanup_failed",
                    extra={"layer_name": str(layer_name)},
                )

    def _remove_non_final_preview_layers(self) -> int:
        removed = 0
        for preview_name in list(self._preview_layer_names):
            removed += MemoryLayerResultService.remove_existing(preview_name, only_memory=True)
        self._preview_layer_names.clear()

        if self._property_preview_name:
            removed += MemoryLayerResultService.remove_existing(self._property_preview_name, only_memory=True)
            self._property_preview_name = ""

        return removed

    def _create_final_cut_from_button(self) -> None:
        final_status = self._create_final_cut_preview(remove_other_previews_on_success=True)
        if final_status:
            self._status_label.setText(final_status)

    def _apply_final_cut_area_calculations(self, final_layer) -> None:
        if final_layer is None or not final_layer.isValid() or self._property_layer is None or not self._property_layer.isValid():
            self._reset_area_calculations()
            return

        self._calculated_property_area_sqm, self._final_area_sqm = property_cut_areas(final_layer, self._property_layer)
        for row_key in list(self._property_row_widgets.keys()):
            self._refresh_property_area_label(row_key)

    def _create_final_cut_preview(self, *, remove_other_previews_on_success: bool = False) -> str:
        if self._property_layer is None or not self._property_layer.isValid():
            if self._final_preview_name:
                MemoryLayerResultService.remove_existing(self._final_preview_name, only_memory=True)
                self._final_preview_name = ""
            self._reset_area_calculations()
            return ""

        final_name = self._final_preview_layer_name()
        merged_name = self._merged_cut_preview_name()
        temp_intersection_names: list[str] = []
        temp_intersection_layers = []

        MemoryLayerResultService.remove_existing(final_name, only_memory=True)
        MemoryLayerResultService.remove_existing(merged_name, only_memory=True)

        property_selected_only = False
        try:
            property_selected_only = int(self._property_layer.selectedFeatureCount() or 0) > 0
        except (AttributeError, RuntimeError):
            property_selected_only = False

        for key in self._ROW_KEYS:
            preview_name = self._preview_name_for(key)
            preview_matches = MemoryLayerResultService._project().mapLayersByName(preview_name)
            if not preview_matches:
                continue

            preview_layer = next(
                (
                    layer
                    for layer in preview_matches
                    if layer.isValid()
                ),
                None,
            )
            if preview_layer is None:
                continue

            intersection_name = self._cut_preview_name_for(key)
            intersection_layer = LayerProcessingService.intersect_layers(
                preview_layer,
                self._property_layer,
                result_layer_name=intersection_name,
                input_selected_only=False,
                overlay_selected_only=property_selected_only,
                group_name=MailablGroupFolders.SANDBOXING,
                style_path=None,
                replace_existing=True,
                custom_properties={
                    "kavitro/easement_preview": "true",
                    "kavitro/easement_id": self._item_id,
                    "kavitro/easement_layer_key": f"cut:{key}",
                },
                make_visible=False,
                make_active=False,
            )
            if intersection_layer is None:
                continue

            temp_intersection_names.append(intersection_name)
            temp_intersection_layers.append(intersection_layer)

        if not temp_intersection_layers:
            self._cleanup_named_layers(temp_intersection_names + [merged_name])
            if self._final_preview_name:
                MemoryLayerResultService.remove_existing(self._final_preview_name, only_memory=True)
            self._final_preview_name = ""
            self._reset_area_calculations()
            self._move_property_preview_to_bottom()
            return self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_SKIPPED)

        merged_layer = LayerProcessingService.merge_layers(
            temp_intersection_layers,
            result_layer_name=merged_name,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=None,
            replace_existing=True,
            custom_properties={
                "kavitro/easement_preview": "true",
                "kavitro/easement_id": self._item_id,
                "kavitro/easement_layer_key": "cut-merge",
            },
            make_visible=False,
            make_active=False,
        )
        if merged_layer is None:
            self._cleanup_named_layers(temp_intersection_names + [merged_name])
            self._reset_area_calculations()
            return self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        final_layer = LayerProcessingService.dissolve_layer(
            merged_layer,
            result_layer_name=final_name,
            selected_only=False,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=QmlPaths.EASEMENT_FINAL,
            replace_existing=True,
            field_names=[],
            custom_properties={
                "kavitro/easement_preview": "true",
                "kavitro/easement_id": self._item_id,
                "kavitro/easement_layer_key": "final-cut",
            },
            make_visible=True,
            make_active=False,
        )
        self._cleanup_named_layers(temp_intersection_names + [merged_name])
        if final_layer is None:
            self._final_preview_name = ""
            self._reset_area_calculations()
            return self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        self._final_preview_name = final_name
        self._apply_final_cut_area_calculations(final_layer)
        final_message = self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_CREATED).format(
            preview=final_layer.name(),
            count=len(temp_intersection_layers),
        )
        if remove_other_previews_on_success:
            removed = self._remove_non_final_preview_layers()
            self._refresh_layer_labels()
            if removed > 0:
                final_message = f"{final_message}\n{self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CLEARED).format(count=removed)}"
        self._move_property_preview_to_bottom()
        return final_message

    def _run_connected_property_preview_flow(self) -> None:
        # A final cut made for the earlier properties or buffers must not supply the areas of these.
        MemoryLayerResultService.remove_existing(
            self._final_preview_name or self._final_preview_layer_name(), only_memory=True
        )
        self._final_preview_name = ""

        if not self._connected_property_numbers:
            self._property_summary_card.clear()
            for key in self._ROW_KEYS:
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED))
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT)
            )
            return


        property_layer = PropertiesSelectors.show_connected_properties_on_map(
            self._connected_property_numbers,
            module=Module.PROPERTY.value,
        )
        self._property_layer = property_layer
        if property_layer is None:
            self._property_summary_card.clear()
            for key in self._ROW_KEYS:
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING))
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING)
            )
            return

        self._refresh_property_summary_card()

        self._property_preview_name = f"{self._lang.translate(TranslationKeys.PREVIEW_EASEMENT_PROPERTIES)} · {self._item_number or self._item_id or '-'}"
        property_preview = LayerProcessingService.buffer_selected_features(
            property_layer,
            distance=float(self._distance_spin.value()),
            result_layer_name=self._property_preview_name,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=QmlPaths.EASEMENT_PROPERTIES,
            replace_existing=True,
            end_cap_style=self._buffer_end_cap_style(),
            join_style=self._buffer_join_style(),
            custom_properties={
                "kavitro/easement_preview": "true",
                "kavitro/easement_id": self._item_id,
                "kavitro/easement_layer_key": "properties",
            },
            make_visible=True,
            make_active=False,
        )
        if property_preview is None:
            for key in self._ROW_KEYS:
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_FAILED))
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_NO_CONNECTED_PROPERTIES)
            )
            return
        self._move_property_preview_to_bottom()

        auto_selected_parts = []
        for key in self._ROW_KEYS:
            layer = self._resolve_source_layer(key)
            if layer is None:
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING))
                continue
            selected_count = LayerProcessingService.select_features_intersecting_layer(
                layer,
                property_preview,
                predicate=[0],
                method=0,
                make_visible=True,
                make_active=False,
            )
            if selected_count > 0:
                auto_selected_parts.append(
                    self._lang.translate(self._LAYER_LABEL_KEYS[key]) + f"={selected_count}"
                )
                self._create_preview(key)
            else:
                self._remove_preview(key)
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED))

        self._refresh_layer_labels()
        self._move_property_preview_to_bottom()
        auto_selected_text = ", ".join(auto_selected_parts) if auto_selected_parts else "0"
        self._status_label.setText(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_AUTO_SELECTED).format(
            count=len(self._connected_property_numbers),
            layers=auto_selected_text,
            )
        )
        self._reset_area_calculations()

    def _clear_auto_selections(self) -> None:
        self._finish_property_selection()
        if self._property_layer is not None:
            try:
                self._property_layer.removeSelection()
            except RuntimeError:
                pass
        for key in self._ROW_KEYS:
            layer = ProjectBaseLayersService.resolve_layer(key, include_legacy=True)
            if layer is None:
                continue
            try:
                layer.removeSelection()
            except RuntimeError:
                pass
