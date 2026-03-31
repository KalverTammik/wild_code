from __future__ import annotations

from typing import Iterable, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QCheckBox, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from qgis.core import QgsProject, QgsVectorLayer
from qgis.utils import iface

from ...constants.button_props import ButtonVariant
from ...constants.cadastral_fields import Katastriyksus
from ...constants.file_paths import QssPaths
from ...engines.LayerCreationEngine import MailablGroupFolders
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ...utils.layers import LayerProcessingService, MemoryLayerResultService
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog
from ...widgets.PropertySummaryCard import PropertySummaryCard
from ...widgets.theme_manager import ThemeManager
from ...Logs.python_fail_logger import PythonFailLogger
from .projects_layer_service import ProjectsLayerService


class ProjectPreviewDialog(QDialog):
    def __init__(self, *, item_data=None, lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item = item_data if isinstance(item_data, dict) else {}
        self._connected_property_numbers: list[str] = []
        self._property_layer: Optional[QgsVectorLayer] = None
        self._property_selection_orchestrator: Optional[MapSelectionOrchestrator] = None
        self._auto_initialized = False
        self._parent_window = None
        self._restore_parent_on_close = False

        self._item_id = DataDisplayExtractors.extract_item_id(self._item) or ""
        self._item_number = (
            DataDisplayExtractors.extract_project_number(self._item)
            or DataDisplayExtractors.extract_item_number(self._item)
            or self._item_id
        )
        self._item_name = DataDisplayExtractors.extract_item_name(self._item) or self._item_number or "-"

        self.setObjectName("ProjectPreviewDialog")
        self.setModal(False)
        self.setWindowTitle(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_DIALOG_TITLE))
        self.resize(820, 520)

        self._build_ui()
        self._refresh_target_layer_label()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])
        self._update_corner_radius_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        intro = QLabel(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_INTRO).format(
                name=self._item_name,
                number=self._item_number or "-",
            ),
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        instructions = QLabel(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_INSTRUCTIONS), self)
        instructions.setWordWrap(True)
        instructions.setObjectName("SetupCardDescription")
        layout.addWidget(instructions)

        info_row = QHBoxLayout()
        info_row.setContentsMargins(0, 0, 0, 0)
        info_row.setSpacing(12)

        self._target_layer_label = QLabel("-", self)
        self._target_layer_label.setWordWrap(True)
        info_row.addWidget(
            self._wrap_info_label(
                self._lang.translate(TranslationKeys.PROJECT_PREVIEW_LAYER_NAME),
                self._target_layer_label,
            )
        )

        self._connected_properties_label = QLabel("-", self)
        self._connected_properties_label.setWordWrap(True)
        info_row.addWidget(
            self._wrap_info_label(
                self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CONNECTED_PROPERTIES),
                self._connected_properties_label,
            )
        )

        layout.addLayout(info_row)

        self._property_summary_card = PropertySummaryCard(
            self,
            show_title=True,
            title_text=self._lang.translate(TranslationKeys.PROJECT_PREVIEW_PROPERTY_CARD_TITLE),
        )
        layout.addWidget(self._property_summary_card)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)

        buffer_label = QLabel(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_BUFFER_DISTANCE), self)
        controls.addWidget(buffer_label)

        self._buffer_distance_spin = QDoubleSpinBox(self)
        self._buffer_distance_spin.setDecimals(1)
        self._buffer_distance_spin.setRange(0.0, 500.0)
        self._buffer_distance_spin.setSingleStep(0.5)
        self._buffer_distance_spin.setValue(0.0)
        self._buffer_distance_spin.setSuffix(" m")
        self._buffer_distance_spin.setMaximumWidth(120)
        self._buffer_distance_spin.valueChanged.connect(self._on_preview_options_changed)
        controls.addWidget(self._buffer_distance_spin)

        self._rounded_corners_checkbox = QCheckBox(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_ROUNDED_CORNERS),
            self,
        )
        self._rounded_corners_checkbox.setChecked(True)
        self._rounded_corners_checkbox.toggled.connect(self._on_rounded_corners_toggled)
        controls.addWidget(self._rounded_corners_checkbox)

        corner_label = QLabel(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CORNER_RADIUS), self)
        controls.addWidget(corner_label)

        self._corner_radius_spin = QDoubleSpinBox(self)
        self._corner_radius_spin.setDecimals(1)
        self._corner_radius_spin.setRange(0.0, 250.0)
        self._corner_radius_spin.setSingleStep(0.5)
        self._corner_radius_spin.setValue(2.0)
        self._corner_radius_spin.setSuffix(" m")
        self._corner_radius_spin.setMaximumWidth(120)
        self._corner_radius_spin.valueChanged.connect(self._on_preview_options_changed)
        controls.addWidget(self._corner_radius_spin)

        controls.addStretch(1)
        layout.addLayout(controls)

        self._status_label = QLabel("", self)
        self._status_label.setWordWrap(True)
        self._status_label.setObjectName("SetupCardDescription")
        layout.addWidget(self._status_label)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)

        self._assign_properties_button = QPushButton(
            self._lang.translate(TranslationKeys.CONNECT_PROPERTIES),
            self,
        )
        self._assign_properties_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._assign_properties_button.setAutoDefault(False)
        self._assign_properties_button.setDefault(False)
        self._assign_properties_button.clicked.connect(self._start_define_properties_flow)
        buttons.addWidget(self._assign_properties_button)

        self._create_preview_button = QPushButton(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CREATE_ACTION),
            self,
        )
        self._create_preview_button.setProperty("variant", ButtonVariant.GHOST)
        self._create_preview_button.setAutoDefault(False)
        self._create_preview_button.setDefault(False)
        self._create_preview_button.clicked.connect(lambda: self._load_connected_property_preview(refresh_from_backend=True))
        buttons.addWidget(self._create_preview_button)

        self._save_button = QPushButton(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_SAVE_ACTION),
            self,
        )
        self._save_button.setProperty("variant", ButtonVariant.SUCCESS)
        self._save_button.setAutoDefault(False)
        self._save_button.setDefault(False)
        self._save_button.clicked.connect(self._save_preview_to_main_layer)
        buttons.addWidget(self._save_button)

        self._clear_button = QPushButton(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CLEAR_ACTION),
            self,
        )
        self._clear_button.setProperty("variant", ButtonVariant.GHOST)
        self._clear_button.setAutoDefault(False)
        self._clear_button.setDefault(False)
        self._clear_button.clicked.connect(self._clear_preview)
        buttons.addWidget(self._clear_button)

        buttons.addStretch(1)

        close_button = QPushButton(self._lang.translate(TranslationKeys.CLOSE), self)
        close_button.setProperty("variant", ButtonVariant.SUCCESS)
        close_button.setAutoDefault(False)
        close_button.setDefault(False)
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

    def _wrap_info_label(self, title: str, value_label: QLabel) -> QWidget:
        container = QWidget(self)
        wrapper = QVBoxLayout(container)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(3)
        title_label = QLabel(title, container)
        title_label.setObjectName("InfoLabel")
        wrapper.addWidget(title_label)
        wrapper.addWidget(value_label)
        return container

    def _preview_layer_name(self) -> str:
        return f"Project area preview · {self._item_number or self._item_id or '-'}"

    def _base_preview_layer_name(self) -> str:
        return f"Project area preview base · {self._item_number or self._item_id or '-'}"

    def _rounded_preview_layer_name(self) -> str:
        return f"Project area preview rounded · {self._item_number or self._item_id or '-'}"

    def _refresh_target_layer_label(self) -> None:
        layer = ProjectsLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        self._target_layer_label.setText(getattr(layer, "name", lambda: "")() if layer is not None else "-")

    def _refresh_connected_properties_label(self) -> None:
        count = len(self._connected_property_numbers)
        preview = ", ".join(self._connected_property_numbers[:5])
        if len(self._connected_property_numbers) > 5:
            preview = f"{preview}, +{len(self._connected_property_numbers) - 5}" if preview else f"+{len(self._connected_property_numbers) - 5}"
        text = self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CONNECTED_PROPERTIES_VALUE).format(
            count=count,
            preview=preview or "-",
        )
        self._connected_properties_label.setText(text)

    def _clear_preview(self) -> None:
        removed = 0
        for layer_name in (
            self._preview_layer_name(),
            self._base_preview_layer_name(),
            self._rounded_preview_layer_name(),
        ):
            removed += MemoryLayerResultService.remove_existing(layer_name, only_memory=True)
        if removed > 0:
            self._status_label.setText(
                self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CLEARED).format(count=removed)
            )

    def _clear_intermediate_preview_layers(self) -> None:
        for layer_name in (
            self._base_preview_layer_name(),
            self._rounded_preview_layer_name(),
        ):
            MemoryLayerResultService.remove_existing(layer_name, only_memory=True)

    def _preview_layer(self) -> Optional[QgsVectorLayer]:
        matches = QgsProject.instance().mapLayersByName(self._preview_layer_name())
        return next((layer for layer in matches if isinstance(layer, QgsVectorLayer) and layer.isValid()), None)

    def _set_property_summary(self, layer: Optional[QgsVectorLayer]) -> None:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            self._property_summary_card.clear()
            return
        try:
            selected_features = list(layer.selectedFeatures() or [])
            feature = selected_features[0] if selected_features else next(layer.getFeatures(), None)
        except Exception:
            feature = None
        self._property_summary_card.set_feature(feature)

    def _buffer_distance(self) -> float:
        return float(self._buffer_distance_spin.value() or 0.0)

    def _rounded_corner_radius(self) -> float:
        if not self._rounded_corners_checkbox.isChecked():
            return 0.0
        return float(self._corner_radius_spin.value() or 0.0)

    def _update_corner_radius_state(self) -> None:
        enabled = bool(self._rounded_corners_checkbox.isChecked())
        self._corner_radius_spin.setEnabled(enabled)

    def _on_rounded_corners_toggled(self, _checked: bool) -> None:
        self._update_corner_radius_state()
        self._on_preview_options_changed()

    def _on_preview_options_changed(self, *_args) -> None:
        if self._auto_initialized and self._connected_property_numbers:
            self._load_connected_property_preview(refresh_from_backend=False)

    def _create_preview_layer(self, property_layer: QgsVectorLayer) -> Optional[QgsVectorLayer]:
        base_layer = LayerProcessingService.dissolve_layer(
            property_layer,
            result_layer_name=self._base_preview_layer_name(),
            selected_only=True,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=None,
            replace_existing=False,
            custom_properties={
                "kavitro/project_preview": "true",
                "kavitro/project_id": self._item_id,
                "kavitro/project_stage": "base",
            },
            make_visible=False,
            make_active=False,
            register_result=False,
        )
        if base_layer is None:
            return None

        current_layer = base_layer
        buffer_distance = self._buffer_distance()
        if buffer_distance > 0:
            current_layer = LayerProcessingService.buffer_layer(
                current_layer,
                distance=buffer_distance,
                result_layer_name=self._preview_layer_name(),
                selected_only=False,
                group_name=MailablGroupFolders.SANDBOXING,
                style_path=None,
                replace_existing=False,
                dissolve=True,
                join_style=0 if self._rounded_corners_checkbox.isChecked() else 1,
                end_cap_style=0 if self._rounded_corners_checkbox.isChecked() else 1,
                custom_properties={
                    "kavitro/project_preview": "true",
                    "kavitro/project_id": self._item_id,
                    "kavitro/project_stage": "buffered",
                },
                make_visible=False,
                make_active=False,
                register_result=False,
            )
            if current_layer is None:
                return None

        corner_radius = self._rounded_corner_radius()
        if corner_radius > 0:
            rounded_out = LayerProcessingService.buffer_layer(
                current_layer,
                distance=corner_radius,
                result_layer_name=self._rounded_preview_layer_name(),
                selected_only=False,
                group_name=MailablGroupFolders.SANDBOXING,
                style_path=None,
                replace_existing=False,
                dissolve=True,
                join_style=0,
                end_cap_style=0,
                custom_properties={
                    "kavitro/project_preview": "true",
                    "kavitro/project_id": self._item_id,
                    "kavitro/project_stage": "rounded_out",
                },
                make_visible=False,
                make_active=False,
                register_result=False,
            )
            if rounded_out is None:
                self._clear_intermediate_preview_layers()
                return None

            current_layer = LayerProcessingService.buffer_layer(
                rounded_out,
                distance=-corner_radius,
                result_layer_name=self._preview_layer_name(),
                selected_only=False,
                group_name=MailablGroupFolders.SANDBOXING,
                style_path=None,
                replace_existing=False,
                dissolve=True,
                join_style=0,
                end_cap_style=0,
                custom_properties={
                    "kavitro/project_preview": "true",
                    "kavitro/project_id": self._item_id,
                    "kavitro/project_stage": "rounded_final",
                },
                make_visible=True,
                make_active=False,
                register_result=False,
            )
            if current_layer is None:
                self._clear_intermediate_preview_layers()
                return None

        prepared = MemoryLayerResultService.prepare_result_layer(
            current_layer,
            layer_name=self._preview_layer_name(),
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=None,
            replace_existing=True,
            custom_properties={
                "kavitro/project_preview": "true",
                "kavitro/project_id": self._item_id,
                "kavitro/project_stage": "final",
            },
            make_visible=True,
            make_active=False,
        )
        self._clear_intermediate_preview_layers()
        return prepared

    def _load_connected_property_preview(self, *, refresh_from_backend: bool) -> None:
        if not self._item_id:
            return

        if refresh_from_backend:
            self._connected_property_numbers = APIModuleActions.get_module_item_connected_properties(
                Module.PROJECT.value,
                self._item_id,
            ) or []
        self._refresh_connected_properties_label()
        self._refresh_target_layer_label()
        self._clear_preview()

        if not self._connected_property_numbers:
            self._property_layer = None
            self._property_summary_card.clear()
            self._status_label.setText(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_NO_CONNECTED_PROPERTIES))
            return

        property_layer = PropertiesSelectors.show_connected_properties_on_map(
            self._connected_property_numbers,
            module=Module.PROJECT.value,
        )
        self._property_layer = property_layer if isinstance(property_layer, QgsVectorLayer) and property_layer.isValid() else None
        self._set_property_summary(self._property_layer)

        if self._property_layer is None:
            self._status_label.setText(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_LAYER_SELECTION_FAILED))
            return

        preview_layer = self._create_preview_layer(self._property_layer)
        if preview_layer is None:
            self._status_label.setText(self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CREATE_FAILED))
            return

        try:
            selected_count = int(self._property_layer.selectedFeatureCount() or 0)
        except Exception:
            selected_count = 0
        self._status_label.setText(
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_CREATED).format(
                preview=preview_layer.name(),
                count=selected_count,
                distance=f"{self._buffer_distance():.1f}",
                radius=f"{self._rounded_corner_radius():.1f}",
            )
        )

    def _existing_property_display(self, main_layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        existing_display: dict[str, str] = {}
        if not self._connected_property_numbers:
            return existing_display
        if main_layer is None:
            for number in self._connected_property_numbers:
                existing_display[number] = number
            return existing_display

        existing_features = MapHelpers.find_features_by_fields_and_values(
            main_layer,
            Katastriyksus.tunnus,
            list(self._connected_property_numbers),
        )
        for feature in existing_features or []:
            try:
                number = str(feature[Katastriyksus.tunnus] or "").strip()
            except Exception:
                number = ""
            if number:
                existing_display[number] = self._format_property_label(number, feature)

        for number in self._connected_property_numbers:
            existing_display.setdefault(number, self._format_property_label(number))
        return existing_display

    def _format_property_label(self, number: str, feature=None) -> str:
        if feature is not None:
            for field_name in (
                Katastriyksus.l_aadress,
                Katastriyksus.ay_nimi,
                Katastriyksus.ov_nimi,
                Katastriyksus.mk_nimi,
            ):
                try:
                    value = feature[field_name]
                except Exception:
                    value = None
                if value:
                    return f"{value} - {number}"
        return str(number or "").strip()

    def _persist_property_links(self, selected_numbers: list[str]) -> tuple[bool, list[str], dict[str, object]]:
        property_ids, missing = APIModuleActions.resolve_property_ids_by_cadastral(selected_numbers)
        if not property_ids:
            raise RuntimeError(f"No property ids resolved for selection: {missing}")
        response = APIModuleActions.associate_properties(Module.PROJECT.value, self._item_id, property_ids)
        refreshed = APIModuleActions.get_module_item_connected_properties(Module.PROJECT.value, self._item_id) or []
        return True, refreshed, {"missing": missing, "raw": response}

    def _open_property_link_review_dialog(self, selected_numbers: list[str], selected_features: list, main_layer: QgsVectorLayer) -> None:
        existing_display = self._existing_property_display(main_layer)
        selected_display: dict[str, str] = {}
        for feature in selected_features or []:
            try:
                number = str(feature[Katastriyksus.tunnus] or "").strip()
            except Exception:
                number = ""
            if number:
                selected_display[number] = self._format_property_label(number, feature)
        for number in selected_numbers:
            selected_display.setdefault(number, self._format_property_label(number))

        dialog = PropertyLinkReviewDialog(existing_display, selected_display, self._lang)
        result = dialog.exec_()
        if dialog.reselect_requested:
            QTimer.singleShot(0, self._start_define_properties_flow)
            return
        if result != QDialog.Accepted:
            self._finish_property_selection()
            return

        try:
            _ok, refreshed, response = self._persist_property_links(selected_numbers)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_preview_property_link_failed",
                extra={"item_id": self._item_id},
            )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.LINK_PROPERTIES_ERROR).format(
                    pid=self._item_id,
                    count=len(selected_numbers),
                    preview=", ".join(selected_numbers[:5]),
                    err=str(exc),
                ),
            )
            self._finish_property_selection()
            return

        self._connected_property_numbers = list(refreshed)
        missing = (response or {}).get("missing") if isinstance(response, dict) else []
        preview_text = ", ".join(self._connected_property_numbers[:5])
        if len(self._connected_property_numbers) > 5:
            preview_text += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                count=len(self._connected_property_numbers) - 5,
            )
        extra_note = ""
        if missing:
            missing_preview = ", ".join(missing[:5])
            extra_note = "\n\n" + self._lang.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(
                missing=missing_preview,
            )
            if len(missing) > 5:
                extra_note += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(missing) - 5,
                )

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.LINK_PROPERTIES_SUCCESS).format(
                pid=self._item_id,
                count=len(self._connected_property_numbers),
                preview=preview_text,
                extra=extra_note,
            ),
        )
        self._finish_property_selection()
        self._load_connected_property_preview(refresh_from_backend=False)

    def _start_define_properties_flow(self) -> None:
        if not self._item_id:
            return

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if main_layer is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.MAP_SELECTION_START_FAILED),
            )
            return

        try:
            main_layer.removeSelection()
        except Exception:
            pass

        if self._property_selection_orchestrator is not None:
            self._finish_property_selection()

        self._property_selection_orchestrator = MapSelectionOrchestrator(parent=self)

        def _on_selected(_layer, features: Iterable) -> None:
            self._exit_property_selection_mode()
            selected_features = list(features or [])
            selected_numbers: list[str] = []
            for feature in selected_features:
                try:
                    number = str(feature[Katastriyksus.tunnus] or "").strip()
                except Exception:
                    number = ""
                if number:
                    selected_numbers.append(number)

            if not selected_numbers:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.MAP_SELECTION_NONE),
                )
                self._finish_property_selection()
                return

            self._open_property_link_review_dialog(selected_numbers, selected_features, main_layer)

        started = self._property_selection_orchestrator.start_selection_for_layer(
            main_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=False,
            keep_existing_selection=bool(self._connected_property_numbers),
            before_start=self._enter_property_selection_mode,
        )
        if not started:
            self._exit_property_selection_mode()
            self._finish_property_selection()
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.MAP_SELECTION_START_FAILED),
            )

    def _finish_property_selection(self) -> None:
        orchestrator = self._property_selection_orchestrator
        self._property_selection_orchestrator = None
        if orchestrator is None:
            return
        try:
            orchestrator.cancel()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_preview_property_selection_cancel_failed",
            )

    def _save_preview_to_main_layer(self) -> None:
        preview_layer = self._preview_layer()
        if preview_layer is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.PROJECT_PREVIEW_SAVE_NO_PREVIEW),
            )
            return

        target_layer = ProjectsLayerService.resolve_main_layer(lang_manager=self._lang, silent=False)
        if target_layer is None:
            return

        success, message = ProjectsLayerService.upsert_generated_area_feature(
            layer=target_layer,
            preview_layer=preview_layer,
            item_id=self._item_id,
            item_data=self._item,
        )
        if success:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.SUCCESS),
                self._lang.translate(TranslationKeys.PROJECT_PREVIEW_SAVE_SUCCESS).format(
                    item_id=self._item_id,
                    layer=message or getattr(target_layer, "name", lambda: "")() or "-",
                ),
            )
            return

        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.PROJECT_PREVIEW_SAVE_FAILED).format(
                item_id=self._item_id,
                error=message or self._lang.translate(TranslationKeys.ERROR),
            ),
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._auto_initialized:
            self._auto_initialized = True
            QTimer.singleShot(0, lambda: self._load_connected_property_preview(refresh_from_backend=True))

    def reject(self) -> None:
        self._clear_preview()
        self._finish_property_selection()
        self._exit_property_selection_mode()
        try:
            if self._property_layer is not None and self._property_layer.isValid():
                self._property_layer.removeSelection()
        except Exception:
            pass
        super().reject()

    def closeEvent(self, event) -> None:
        self._clear_preview()
        self._finish_property_selection()
        self._exit_property_selection_mode()
        try:
            if self._property_layer is not None and self._property_layer.isValid():
                self._property_layer.removeSelection()
        except Exception:
            pass
        super().closeEvent(event)

    def _enter_property_selection_mode(self) -> None:
        parent_window = self._resolve_parent_window()
        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
        )
        if parent_window is not None:
            self._parent_window = parent_window
            self._restore_parent_on_close = True

    def _exit_property_selection_mode(self) -> None:
        if not self._restore_parent_on_close:
            return
        parent_window = self._resolve_parent_window() or self._parent_window
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
            bring_front=True,
        )
        self._restore_parent_on_close = False

    def _resolve_parent_window(self):
        try:
            top = self.window()
            while top is not None and top.parent() not in (None, top):
                top = top.parent()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_preview_resolve_parent_failed",
            )
            top = None
        return top