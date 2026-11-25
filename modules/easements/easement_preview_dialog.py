from __future__ import annotations


from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qgis.utils import iface

from ...constants.button_props import ButtonVariant
from ...constants.cadastral_fields import AreaUnit
from ...constants.file_paths import QmlPaths, QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors
from ...utils.project_base_layers import ProjectBaseLayerKeys, ProjectBaseLayersService
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.date_helpers import DateHelpers
from ...widgets.PropertySummaryCard import PropertySummaryCard
from ...ui.theme_manager import ThemeManager
from .preview_dialog.final_save_mixin import EasementFinalSaveMixin
from .preview_dialog.preview_layers_mixin import EasementPreviewLayersMixin
from .preview_dialog.property_editor_mixin import EasementPropertyEditorMixin


class _StatusLabel(QLabel):
    """The dialog's status line: shown while it has text, so a new status is never set on a hidden label."""

    def setText(self, text) -> None:  # noqa: N802 - Qt name
        super().setText(text)
        self.setVisible(bool(str(text or "").strip()))


class EasementPreviewDialog(EasementPreviewLayersMixin, EasementPropertyEditorMixin, EasementFinalSaveMixin, QDialog):
    """Preview an easement on the map, link its properties and save the final cut.

    This class owns the widgets, the window state and the start-up flow. Preview layers,
    the property editor and saving live in the mixins under ``preview_dialog/``; the
    distance and property rules are plain functions in ``easement_distance_rules`` and
    ``easement_property_edges``.
    """

    _ROW_KEYS = (
        ProjectBaseLayerKeys.WATERPIPES,
        ProjectBaseLayerKeys.SEWERPIPES,
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES,
        ProjectBaseLayerKeys.RAINWATERPIPES,
        ProjectBaseLayerKeys.SEWAGE_PUMPING,
        ProjectBaseLayerKeys.SEWAGE_DUMP,
        ProjectBaseLayerKeys.SEWAGE_PLANT,
        ProjectBaseLayerKeys.WATER_STATION,
        ProjectBaseLayerKeys.RAIN_PUMP,
    )

    _LAYER_LABEL_KEYS = {
        ProjectBaseLayerKeys.WATERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_WATERPIPES,
        ProjectBaseLayerKeys.SEWERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_SEWERPIPES,
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_PRESSURE_SEWERPIPES,
        ProjectBaseLayerKeys.RAINWATERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_RAINWATERPIPES,
        ProjectBaseLayerKeys.SEWAGE_PUMPING: TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_PUMPING,
        ProjectBaseLayerKeys.SEWAGE_DUMP: TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_DUMP,
        ProjectBaseLayerKeys.SEWAGE_PLANT: TranslationKeys.SETTINGS_BASE_LAYER_SEWAGE_PLANT,
        ProjectBaseLayerKeys.WATER_STATION: TranslationKeys.SETTINGS_BASE_LAYER_WATER_STATION,
        ProjectBaseLayerKeys.RAIN_PUMP: TranslationKeys.SETTINGS_BASE_LAYER_RAIN_PUMP,
    }

    _STYLE_PATHS = {
        ProjectBaseLayerKeys.WATERPIPES: QmlPaths.EASEMENT_WATER,
        ProjectBaseLayerKeys.SEWERPIPES: QmlPaths.EASEMENT_SEWER,
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: QmlPaths.EASEMENT_PRESSURE_SEWER,
        ProjectBaseLayerKeys.RAINWATERPIPES: None,
        ProjectBaseLayerKeys.SEWAGE_PUMPING: QmlPaths.EASEMENT_SEWER,
        ProjectBaseLayerKeys.SEWAGE_DUMP: QmlPaths.EASEMENT_SEWER,
        ProjectBaseLayerKeys.SEWAGE_PLANT: QmlPaths.EASEMENT_SEWER,
        ProjectBaseLayerKeys.WATER_STATION: QmlPaths.EASEMENT_WATER,
        ProjectBaseLayerKeys.RAIN_PUMP: QmlPaths.EASEMENT_DRAINAGE,
    }

    _AREA_UNIT_LABELS = {
        AreaUnit.M: "m²",
        AreaUnit.H: "ha",
    }

    def __init__(self, *, item_data=None, parent=None, on_status_changed=None) -> None:
        super().__init__(parent)
        self._lang = LanguageManager()
        self._item = item_data if isinstance(item_data, dict) else {}
        self._on_status_changed = on_status_changed
        self._service = ProjectBaseLayersService()
        self._preview_layer_names: set[str] = set()
        self._layer_name_labels: dict[str, QLabel] = {}
        self._row_status_labels: dict[str, QLabel] = {}
        self._parent_window = None
        self._restore_parent_on_close = False
        self._connected_property_numbers: list[str] = []
        self._property_layer = None
        self._property_preview_name = ""
        self._property_selection_orchestrator = None
        self._property_edges: list[dict[str, object]] = []
        self._property_row_widgets: dict[str, dict[str, object]] = {}
        self._date_helper = DateHelpers()
        self._auto_initialized = False
        self._automation_running = False
        self._final_preview_name = ""
        self._calculated_property_area_sqm: dict[str, float] = {}
        self._final_area_sqm = 0.0
        self._generated_pdf_path = ""
        self._publish_in_progress = False

        self._item_id = DataDisplayExtractors.extract_item_id(self._item) or ""
        self._item_number = DataDisplayExtractors.extract_item_number(self._item) or self._item_id
        self._item_name = DataDisplayExtractors.extract_item_name(self._item) or self._item_number or "-"

        self.setObjectName("EasementPreviewDialog")
        self.setModal(False)
        self.setWindowTitle(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DIALOG_TITLE))
        self.resize(980, 720)

        self._build_ui()
        self._refresh_layer_labels()
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])
        self._distance_spin.valueChanged.connect(self._on_distance_changed)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        intro = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_INTRO).format(
                name=self._item_name,
                number=self._item_number or "-",
            ),
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        instructions = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_INSTRUCTIONS),
            self,
        )
        instructions.setWordWrap(True)
        instructions.setObjectName("SetupCardDescription")
        layout.addWidget(instructions)

        self._property_summary_card = PropertySummaryCard(
            self,
            show_title=True,
            title_text=self._lang.translate(TranslationKeys.PROPERTY_SUMMARY_TITLE),
        )
        layout.addWidget(self._property_summary_card)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)

        distance_label = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_BUFFER_DISTANCE),
            self,
        )
        controls.addWidget(distance_label)

        self._distance_spin = QDoubleSpinBox(self)
        self._distance_spin.setDecimals(1)
        self._distance_spin.setRange(0.1, 500.0)
        self._distance_spin.setSingleStep(0.5)
        self._distance_spin.setValue(2.0)
        self._distance_spin.setSuffix(" m")
        self._distance_spin.setMaximumWidth(120)
        controls.addWidget(self._distance_spin)

        # Corners are the buffer's join style; ends are its end cap and only change line buffers.
        self._rounded_corners_checkbox = QCheckBox(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROUNDED_CAPS),
            self,
        )
        self._rounded_corners_checkbox.setChecked(True)
        self._rounded_corners_checkbox.toggled.connect(self._on_geometry_style_changed)
        controls.addWidget(self._rounded_corners_checkbox)

        self._round_ends_checkbox = QCheckBox(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROUND_ENDS),
            self,
        )
        self._round_ends_checkbox.setChecked(True)
        self._round_ends_checkbox.toggled.connect(self._on_geometry_style_changed)
        controls.addWidget(self._round_ends_checkbox)

        self._define_properties_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES),
            self,
        )
        self._define_properties_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._define_properties_button.setAutoDefault(False)
        self._define_properties_button.setDefault(False)
        self._define_properties_button.clicked.connect(self._start_define_properties_flow)
        controls.addWidget(self._define_properties_button)

        self._create_final_cut_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CREATE_FINAL_CUT),
            self,
        )
        self._create_final_cut_button.setProperty("variant", ButtonVariant.SUCCESS)
        self._create_final_cut_button.setAutoDefault(False)
        self._create_final_cut_button.setDefault(False)
        self._create_final_cut_button.clicked.connect(self._create_final_cut_from_button)
        controls.addWidget(self._create_final_cut_button)

        self._preview_drawing_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PREVIEW),
            self,
        )
        self._preview_drawing_button.setProperty("variant", ButtonVariant.GHOST)
        self._preview_drawing_button.setAutoDefault(False)
        self._preview_drawing_button.setDefault(False)
        self._preview_drawing_button.clicked.connect(self._preview_pdf_drawing)
        controls.addWidget(self._preview_drawing_button)

        self._publish_drawing_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH),
            self,
        )
        self._publish_drawing_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._publish_drawing_button.setAutoDefault(False)
        self._publish_drawing_button.setDefault(False)
        self._publish_drawing_button.clicked.connect(self._publish_pdf_drawing)
        controls.addWidget(self._publish_drawing_button)

        controls.addStretch(1)
        layout.addLayout(controls)

        rows_frame = QFrame(self)
        rows_layout = QGridLayout(rows_frame)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setHorizontalSpacing(8)
        rows_layout.setVerticalSpacing(8)

        header_label = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LAYER_NAME), rows_frame)
        rows_layout.addWidget(header_label, 0, 1)

        action_header = QLabel(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_STATUS), rows_frame)
        rows_layout.addWidget(action_header, 0, 2)

        for row_index, key in enumerate(self._ROW_KEYS, start=1):
            title = QLabel(self._lang.translate(self._LAYER_LABEL_KEYS[key]), rows_frame)
            rows_layout.addWidget(title, row_index, 0)

            layer_name_label = QLabel("", rows_frame)
            layer_name_label.setWordWrap(True)
            rows_layout.addWidget(layer_name_label, row_index, 1)
            self._layer_name_labels[key] = layer_name_label

            status_label = QLabel("", rows_frame)
            status_label.setWordWrap(True)
            rows_layout.addWidget(status_label, row_index, 2)
            self._row_status_labels[key] = status_label

        layout.addWidget(rows_frame, 1)

        property_frame = QFrame(self)
        property_frame.setObjectName("EasementPropertyEditorFrame")
        property_layout = QVBoxLayout(property_frame)
        property_layout.setContentsMargins(0, 0, 0, 0)
        property_layout.setSpacing(8)

        property_hint = QLabel(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_HINT),
            property_frame,
        )
        property_hint.setWordWrap(True)
        property_hint.setObjectName("SetupCardDescription")
        property_layout.addWidget(property_hint)

        self._property_scroll = QScrollArea(property_frame)
        self._property_scroll.setWidgetResizable(True)
        self._property_scroll.setFrameShape(QFrame.NoFrame)

        self._property_rows_container = QWidget(self._property_scroll)
        self._property_rows_layout = QVBoxLayout(self._property_rows_container)
        self._property_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._property_rows_layout.setSpacing(8)
        self._property_scroll.setWidget(self._property_rows_container)
        property_layout.addWidget(self._property_scroll, 1)

        property_buttons = QHBoxLayout()
        property_buttons.setContentsMargins(0, 0, 0, 0)
        property_buttons.setSpacing(8)
        property_buttons.addStretch(1)

        self._save_properties_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE),
            property_frame,
        )
        self._save_properties_button.setProperty("variant", ButtonVariant.SUCCESS)
        self._save_properties_button.setAutoDefault(False)
        self._save_properties_button.setDefault(False)
        self._save_properties_button.clicked.connect(self._save_property_details)
        property_buttons.addWidget(self._save_properties_button)

        property_layout.addLayout(property_buttons)
        layout.addWidget(property_frame, 2)

        self._status_label = _StatusLabel("", self)
        self._status_label.setWordWrap(True)
        self._status_label.setObjectName("SetupCardDescription")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)

        clear_button = QPushButton(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CLEAR_ACTION),
            self,
        )
        clear_button.setProperty("variant", ButtonVariant.GHOST)
        clear_button.setAutoDefault(False)
        clear_button.setDefault(False)
        clear_button.clicked.connect(self._clear_previews)
        buttons.addWidget(clear_button)

        buttons.addStretch(1)

        close_button = QPushButton(self._lang.translate(TranslationKeys.CLOSE), self)
        close_button.setProperty("variant", ButtonVariant.SUCCESS)
        close_button.setAutoDefault(False)
        close_button.setDefault(False)
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

    def _refresh_layer_labels(self) -> None:
        for key, label in self._layer_name_labels.items():
            layer = self._resolve_source_layer(key)
            if layer is None:
                label.setText(self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING))
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING))
                continue
            try:
                selected_count = int(layer.selectedFeatureCount() or 0)
            except (AttributeError, RuntimeError):
                selected_count = 0
            suffix = f" ({selected_count})" if selected_count > 0 else ""
            label.setText(f"{layer.name()}{suffix}")

    def _set_row_status(self, layer_key: str, text: str) -> None:
        label = self._row_status_labels.get(layer_key)
        if label is None:
            return
        label.setText(str(text or ""))

    def _on_distance_changed(self, _value: float) -> None:
        if self._auto_initialized and not self._automation_running:
            QTimer.singleShot(0, self._rerun_automation)

    def _on_geometry_style_changed(self, _checked: bool) -> None:
        if self._auto_initialized and not self._automation_running:
            QTimer.singleShot(0, self._rerun_automation)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._enter_map_view_mode()
        if not self._auto_initialized:
            self._auto_initialized = True
            QTimer.singleShot(0, self._initialize_connected_property_flow)

    def reject(self) -> None:
        self._clear_previews()
        self._cleanup_generated_pdf()
        self._exit_property_selection_mode()
        self._exit_map_view_mode()
        super().reject()

    def closeEvent(self, event) -> None:
        self._clear_previews()
        self._cleanup_generated_pdf()
        self._exit_property_selection_mode()
        self._exit_map_view_mode()
        super().closeEvent(event)

    def _enter_property_selection_mode(self) -> None:
        parent_window = self._resolve_parent_window()
        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
        )

    def _exit_property_selection_mode(self) -> None:
        parent_window = self._resolve_parent_window()
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
            bring_front=True,
        )

    def _enter_map_view_mode(self) -> None:
        if self._restore_parent_on_close:
            return
        parent_window = self._resolve_parent_window()
        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=None,
        )
        self._parent_window = parent_window
        self._restore_parent_on_close = parent_window is not None

    def _exit_map_view_mode(self) -> None:
        if not self._restore_parent_on_close:
            return
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._resolve_parent_window() or self._parent_window,
            dialogs=None,
            bring_front=True,
        )
        self._restore_parent_on_close = False

    def _resolve_parent_window(self):
        window = self.parentWidget()
        if window is None:
            return None
        return DialogHelpers.resolve_safe_parent_window(
            window.window(),
            iface_obj=iface,
            module="easement",
            qgis_main_error_event="easement_preview_qgis_main_failed",
        )

    def _initialize_connected_property_flow(self, *, refresh_from_backend: bool = True) -> None:
        if not self._item_id:
            return

        if refresh_from_backend:
            self._set_property_edges(APIModuleActions.get_easement_property_edges(self._item_id) or [])

        self._run_connected_property_preview_flow()
