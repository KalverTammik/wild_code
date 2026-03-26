from __future__ import annotations

import os
import re
from typing import Iterable
from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qgis.core import QgsDistanceArea, QgsProject, QgsUnitTypes
from qgis.utils import iface

from ...constants.button_props import ButtonVariant
from ...constants.cadastral_fields import AreaUnit
from ...constants.cadastral_fields import Katastriyksus
from ...constants.file_paths import QmlPaths, QssPaths
from ...engines.LayerCreationEngine import MailablGroupFolders
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.easements.easement_layer_service import EasementLayerService
from ...modules.easements.easement_pdf_service import EasementPdfService
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ...utils.layers import LayerProcessingService, MemoryLayerResultService
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.project_base_layers import ProjectBaseLayerKeys, ProjectBaseLayersService
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.url_manager import Module
from ...widgets.DateHelpers import DateHelpers
from ...widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog
from ...widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog
from ...widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget
from ...widgets.PropertySummaryCard import PropertySummaryCard
from ...widgets.theme_manager import ThemeManager


class EasementPreviewDialog(QDialog):
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
        ProjectBaseLayerKeys.WATERPIPES: getattr(QmlPaths, "EASEMENT_WATER", None),
        ProjectBaseLayerKeys.SEWERPIPES: getattr(QmlPaths, "EASEMENT_SEWER", None),
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: getattr(QmlPaths, "EASEMENT_PRESSURE_SEWER", None),
        ProjectBaseLayerKeys.RAINWATERPIPES: None,
        ProjectBaseLayerKeys.SEWAGE_PUMPING: getattr(QmlPaths, "EASEMENT_SEWER", None),
        ProjectBaseLayerKeys.SEWAGE_DUMP: getattr(QmlPaths, "EASEMENT_SEWER", None),
        ProjectBaseLayerKeys.SEWAGE_PLANT: getattr(QmlPaths, "EASEMENT_SEWER", None),
        ProjectBaseLayerKeys.WATER_STATION: getattr(QmlPaths, "EASEMENT_WATER", None),
        ProjectBaseLayerKeys.RAIN_PUMP: getattr(QmlPaths, "EASETMENT_DRAINAGE", None),
    }

    _FIXED_DISTANCE_BY_ROW = {
        ProjectBaseLayerKeys.SEWAGE_DUMP: 30.0,
        ProjectBaseLayerKeys.SEWAGE_PLANT: 30.0,
        ProjectBaseLayerKeys.WATER_STATION: 30.0,
    }

    _PUMP_ROWS = {ProjectBaseLayerKeys.SEWAGE_PUMPING, ProjectBaseLayerKeys.RAIN_PUMP}

    _DIAMETER_FIELD_CANDIDATES = (
        "Läbimõõt, mm",
        "Läbimõõt",
        "Siseläbimõõt",
        "Diameeter",
        "Diameter",
        "DN",
    )

    _DEPTH_FIELD_CANDIDATES = (
        "Sügavus",
        "Rajamissügavus",
        "Paigaldussügavus",
        "Lähtekõrgus",
        "Lõppkõrgus",
        "Alguskõrgus",
        "Loppkorgus",
        "Lahtekorgus",
        "Depth",
    )

    _FLOW_FIELD_CANDIDATES = (
        "Vooluhulk",
        "Vooluhulk, m3/d",
        "Vooluhulk m3/d",
        "Flow",
        "Capacity",
        "Tootlikkus",
        "Q",
    )

    _AREA_UNIT_LABELS = {
        AreaUnit.M: "m²",
        AreaUnit.H: "ha",
    }

    _DEFAULT_CURRENCY = "EUR"

    def __init__(self, *, item_data=None, lang_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item = item_data if isinstance(item_data, dict) else {}
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
        self._row_distances: dict[str, float] = {}
        self._final_preview_name = ""
        self._calculated_property_area_sqm: dict[str, float] = {}
        self._final_area_sqm = 0.0
        self._generated_pdf_path = ""

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
            title_text="Kinnistu andmed",
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

        self._rounded_caps_checkbox = QCheckBox(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROUNDED_CAPS),
            self,
        )
        self._rounded_caps_checkbox.setChecked(True)
        self._rounded_caps_checkbox.toggled.connect(self._on_geometry_style_changed)
        controls.addWidget(self._rounded_caps_checkbox)

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

        self._status_label = QLabel("", self)
        self._status_label.setWordWrap(True)
        self._status_label.setObjectName("SetupCardDescription")
        self._status_label.hide()

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
            except Exception:
                selected_count = 0
            suffix = f" ({selected_count})" if selected_count > 0 else ""
            label.setText(f"{layer.name()}{suffix}")
        self._refresh_rule_indicators()

    def _set_row_status(self, layer_key: str, text: str) -> None:
        label = self._row_status_labels.get(layer_key)
        if label is None:
            return
        label.setText(str(text or ""))

    @classmethod
    def _normalize_area_unit(cls, value: object) -> str:
        unit = str(value or "").strip().upper()
        if unit in ("M", "SQM"):
            return AreaUnit.M
        if unit == "H":
            return AreaUnit.H
        return AreaUnit.M

    @classmethod
    def _normalize_currency(cls, value: object) -> str:
        text = str(value or cls._DEFAULT_CURRENCY).strip().upper()
        return text or cls._DEFAULT_CURRENCY

    def _property_display_label(self, number: str, display_address: str = "") -> str:
        number_text = str(number or "").strip()
        address_text = str(display_address or "").strip()
        if address_text and number_text and address_text != number_text:
            return f"{address_text} — {number_text}"
        return address_text or number_text or "-"

    def _normalize_property_edge(self, edge: Optional[dict]) -> dict[str, object]:
        edge = edge or {}
        node = edge.get("node") if isinstance(edge.get("node"), dict) else {}
        area = edge.get("area") if isinstance(edge.get("area"), dict) else {}
        price = edge.get("pricePerAreaUnit") if isinstance(edge.get("pricePerAreaUnit"), dict) else {}
        total = edge.get("totalPrice") if isinstance(edge.get("totalPrice"), dict) else {}

        number = str(node.get("cadastralUnitNumber") or edge.get("cadastralUnitNumber") or "").strip()
        property_id = str(node.get("id") or edge.get("id") or "").strip()
        display_address = str(node.get("displayAddress") or edge.get("displayAddress") or "").strip()

        return {
            "id": property_id,
            "cadastralUnitNumber": number,
            "displayAddress": display_address,
            "display": self._property_display_label(number, display_address),
            "area": {
                "size": self._coerce_number(area.get("size")),
                "unit": self._normalize_area_unit(area.get("unit")),
            },
            "pricePerAreaUnit": {
                "amount": self._coerce_number(price.get("amount")),
                "currencyCode": self._normalize_currency(price.get("currencyCode")),
            },
            "totalPrice": {
                "amount": self._coerce_number(total.get("amount")),
                "currencyCode": self._normalize_currency(total.get("currencyCode")),
            },
            "isPayable": bool(edge.get("isPayable")),
            "nextPaymentDate": str(edge.get("nextPaymentDate") or "").strip(),
        }

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                EasementPreviewDialog._clear_layout(child_layout)

    def _first_property_feature(self):
        layer = self._property_layer
        if layer is None or not getattr(layer, "isValid", lambda: False)():
            return None

        try:
            selected_features = list(layer.getSelectedFeatures())
        except Exception:
            selected_features = []
        if selected_features:
            return selected_features[0]

        try:
            for feature in layer.getFeatures():
                return feature
        except Exception:
            return None
        return None

    def _refresh_property_summary_card(self) -> None:
        try:
            self._property_summary_card.set_feature(self._first_property_feature())
        except Exception:
            self._property_summary_card.clear()

    def _resolve_preview_layer_by_name(self, layer_name: str):
        if not layer_name:
            return None
        try:
            matches = QgsProject.instance().mapLayersByName(layer_name)
        except Exception:
            matches = []
        for layer in matches:
            try:
                if getattr(layer, "isValid", lambda: False)():
                    return layer
            except Exception:
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

    def _save_final_cut_to_main_layer(self, property_edges: Optional[list[dict]] = None) -> tuple[bool, str]:
        final_layer, final_status = self._ensure_final_cut_layer()
        if final_layer is None:
            return False, final_status or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        target_layer = EasementLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        if target_layer is None:
            return False, self._lang.translate(TranslationKeys.EASEMENT_LAYER_MISSING)

        ok, message = EasementLayerService.upsert_final_cut_feature(
            layer=target_layer,
            final_layer=final_layer,
            item_id=self._item_id,
            item_data=self._item,
            property_edges=property_edges,
        )
        if ok:
            return True, self._lang.translate(TranslationKeys.EASEMENT_LAYER_SAVE_SUCCESS).format(layer=message)
        return False, self._lang.translate(TranslationKeys.EASEMENT_LAYER_SAVE_FAILED).format(error=message)

    def _cleanup_generated_pdf(self) -> None:
        path = str(self._generated_pdf_path or "").strip()
        self._generated_pdf_path = ""
        if not path:
            return
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _drawing_preview_title(self) -> str:
        return f"{self._item_number or self._item_id or 'easement'}_drawing.pdf"

    def _ensure_generated_pdf(self) -> tuple[str, str]:
        final_layer, final_status = self._ensure_final_cut_layer()
        if final_layer is None:
            return "", final_status or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        self._cleanup_generated_pdf()
        ok, payload = EasementPdfService.export_final_cut_pdf(
            item_data=self._item,
            item_id=self._item_id,
            item_number=self._item_number,
            item_name=self._item_name,
            final_layer=final_layer,
            property_layer=self._property_layer,
        )
        if not ok:
            return "", self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_EXPORT_FAILED).format(
                error=str(payload or "-")
            )

        self._generated_pdf_path = str(payload or "").strip()
        return self._generated_pdf_path, ""

    def _preview_pdf_drawing(self) -> None:
        pdf_path, error = self._ensure_generated_pdf()
        if not pdf_path:
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                error or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PREVIEW_FAILED),
            )
            return

        dialog = TaskFilePreviewDialog.open_preview(
            local_file_path=pdf_path,
            local_title=self._drawing_preview_title(),
            lang_manager=self._lang,
            parent=self,
        )
        if dialog is not None:
            dialog.exec_()

    def _publish_pdf_drawing(self) -> None:
        pdf_path, error = self._ensure_generated_pdf()
        if not pdf_path:
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                error or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
            )
            return

        uploaded = APIModuleActions.upload_module_file(Module.EASEMENT.value, self._item_id, pdf_path)
        if isinstance(uploaded, dict) and str(uploaded.get("uuid") or "").strip():
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.SUCCESS),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_SUCCESS),
            )
            return

        ModernMessageDialog.show_error(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
        )

    @classmethod
    def _calculate_total_amount(cls, area_value: float, price_value: float) -> Optional[float]:
        try:
            if area_value <= 0 or price_value <= 0:
                return None
        except Exception:
            return None
        return round(float(area_value) * float(price_value), 2)

    @classmethod
    def _format_total_amount(cls, value: Optional[float], currency_code: str) -> str:
        if value is None:
            return "–"
        return f"{value:.2f} {currency_code}".strip()

    def _update_property_row_total(self, row_key: str) -> None:
        editors = self._property_row_widgets.get(row_key) or {}
        editor_widget = editors.get("editor_widget")
        if editor_widget is None:
            return

        unit_value = str(editor_widget.current_unit() or AreaUnit.M)
        square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
        area_value = square_meters / 10000.0 if unit_value == AreaUnit.H else square_meters
        total = self._calculate_total_amount(float(area_value), float(editor_widget.price_value()))
        editor_widget.set_total_display(
            self._format_total_amount(total, str(editor_widget.currency_code() or self._DEFAULT_CURRENCY))
        )

    def _format_area_display(self, square_meters: float, unit: str = AreaUnit.M) -> str:
        try:
            numeric = max(0.0, float(square_meters or 0.0))
        except Exception:
            numeric = 0.0

        if unit == AreaUnit.H:
            return f"{numeric / 10000.0:.4f} ha"
        return f"{numeric:.2f} m²"

    def _measure_geometry_area_sqm(self, geometry, layer) -> float:
        try:
            if geometry is None or geometry.isEmpty():
                return 0.0
        except Exception:
            return 0.0

        try:
            distance_area = QgsDistanceArea()
            distance_area.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
            ellipsoid = QgsProject.instance().ellipsoid()
            if ellipsoid:
                distance_area.setEllipsoid(ellipsoid)
            measured = distance_area.measureArea(geometry)
            return max(0.0, float(distance_area.convertAreaMeasurement(measured, QgsUnitTypes.AreaSquareMeters)))
        except Exception:
            try:
                return max(0.0, float(geometry.area()))
            except Exception:
                return 0.0

    def _refresh_property_area_label(self, row_key: str) -> None:
        editors = self._property_row_widgets.get(row_key) or {}
        editor_widget = editors.get("editor_widget")
        if editor_widget is None:
            return

        unit_value = str(editor_widget.current_unit() or AreaUnit.M)
        square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
        editor_widget.set_area_display(self._format_area_display(square_meters, unit_value))
        self._update_property_row_total(row_key)

    def _reset_area_calculations(self) -> None:
        self._calculated_property_area_sqm = {}
        self._final_area_sqm = 0.0
        for row_key in list(self._property_row_widgets.keys()):
            self._refresh_property_area_label(row_key)

    def _buffer_end_cap_style(self) -> int:
        return 0 if self._rounded_caps_checkbox.isChecked() else 1

    def _build_property_editor_row(self, edge: dict[str, object], *, show_title: bool = True) -> QWidget:
        row_key = str(edge.get("cadastralUnitNumber") or edge.get("id") or "")
        row = QFrame(self._property_rows_container)
        row.setProperty("easementPropertyRow", True)

        layout = QVBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        if show_title:
            title = QLabel(str(edge.get("display") or row_key or "-"), row)
            title.setWordWrap(True)
            layout.addWidget(title)

        editor_widget = EasementPropertyAreaCalculationWidget(
            lang_manager=self._lang,
            edge=edge,
            area_unit_labels=self._AREA_UNIT_LABELS,
            default_currency=self._DEFAULT_CURRENCY,
            parent=row,
        )
        layout.addWidget(editor_widget)

        self._property_row_widgets[row_key] = {
            "row": row,
            "edge": edge,
            "editor_widget": editor_widget,
        }

        editor_widget.totalsChanged.connect(lambda key=row_key: self._update_property_row_total(key))
        editor_widget.unitChanged.connect(lambda key=row_key: self._refresh_property_area_label(key))

        self._update_property_row_total(row_key)
        self._refresh_property_area_label(row_key)
        return row

    def _set_property_edges(self, edges: list[dict[str, object]]) -> None:
        self._property_edges = [self._normalize_property_edge(edge) for edge in (edges or [])]
        self._connected_property_numbers = [
            str(edge.get("cadastralUnitNumber") or "")
            for edge in self._property_edges
            if str(edge.get("cadastralUnitNumber") or "").strip()
        ]
        self._property_row_widgets.clear()
        self._clear_layout(self._property_rows_layout)

        if not self._property_edges:
            self._property_summary_card.clear()
            empty_label = QLabel(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT),
                self._property_rows_container,
            )
            empty_label.setWordWrap(True)
            empty_label.setObjectName("SetupCardDescription")
            self._property_rows_layout.addWidget(empty_label)
            self._save_properties_button.setEnabled(False)
            return

        show_titles = len(self._property_edges) > 1
        for edge in self._property_edges:
            self._property_rows_layout.addWidget(self._build_property_editor_row(edge, show_title=show_titles))

        self._property_rows_layout.addStretch(1)
        self._save_properties_button.setEnabled(True)
        self._reset_area_calculations()

    def _on_distance_changed(self, _value: float) -> None:
        self._refresh_rule_indicators()
        if self._auto_initialized and not self._automation_running:
            QTimer.singleShot(0, self._rerun_automation)

    def _on_geometry_style_changed(self, _checked: bool) -> None:
        if self._auto_initialized and not self._automation_running:
            QTimer.singleShot(0, self._rerun_automation)

    def _format_property_label(self, number: str, feature=None) -> str:
        if feature is not None:
            for fld in (
                Katastriyksus.l_aadress,
                Katastriyksus.ay_nimi,
                Katastriyksus.ov_nimi,
                Katastriyksus.mk_nimi,
            ):
                try:
                    value = feature[fld]
                    if value:
                        return f"{value} — {number}"
                except Exception:
                    continue
        return str(number or "")

    @staticmethod
    def _normalize_field_name(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())

    @classmethod
    def _coerce_number(cls, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            try:
                return abs(float(value))
            except Exception:
                return None

        text = str(value or "").strip()
        if not text:
            return None
        text = text.replace("\xa0", " ").replace(",", ".")
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return abs(float(match.group(0)))
        except Exception:
            return None

    @classmethod
    def _format_distance(cls, value: float) -> str:
        try:
            numeric = float(value)
        except Exception:
            return str(value)
        if abs(numeric - round(numeric)) < 0.001:
            return str(int(round(numeric)))
        return f"{numeric:.1f}".rstrip("0").rstrip(".")

    @classmethod
    def _find_field_names(cls, layer, candidates: tuple[str, ...]) -> list[str]:
        if layer is None:
            return []

        normalized_candidates = [cls._normalize_field_name(candidate) for candidate in candidates if candidate]
        matched: list[str] = []
        try:
            fields = layer.fields()
        except Exception:
            return matched

        for field in fields:
            field_name = field.name()
            normalized_field = cls._normalize_field_name(field_name)
            if normalized_field in normalized_candidates:
                matched.append(field_name)
                continue
            if any(candidate and candidate in normalized_field for candidate in normalized_candidates):
                matched.append(field_name)
        return matched

    def _preview_name_for(self, layer_key: str) -> str:
        layer_title = self._lang.translate(self._LAYER_LABEL_KEYS[layer_key])
        return f"Easement preview · {self._item_number or self._item_id or '-'} · {layer_title}"

    def _final_preview_layer_name(self) -> str:
        return f"Easement area preview · {self._item_number or self._item_id or '-'}"

    def _cut_preview_name_for(self, layer_key: str) -> str:
        layer_title = self._lang.translate(self._LAYER_LABEL_KEYS[layer_key])
        return f"Easement cut preview · {self._item_number or self._item_id or '-'} · {layer_title}"

    def _merged_cut_preview_name(self) -> str:
        return f"Easement cut merge · {self._item_number or self._item_id or '-'}"

    def _resolve_source_layer(self, layer_key: str):
        return ProjectBaseLayersService.resolve_layer(layer_key, include_legacy=True)

    def _feature_is_pressure_pipe(self, layer_key: str, feature, source_layer) -> bool:
        if layer_key == ProjectBaseLayerKeys.PRESSURE_SEWERPIPES:
            return True
        field_names = self._find_field_names(source_layer, ("Survetoru",))
        for field_name in field_names:
            value = feature[field_name]
            if value in (True, 1, "1", "true", "True"):
                return True
        return False

    def _calculate_flow_based_distance(self, source_layer) -> float:
        flow_fields = self._find_field_names(source_layer, self._FLOW_FIELD_CANDIDATES)
        max_flow = None
        try:
            selected_features = list(source_layer.getSelectedFeatures())
        except Exception:
            selected_features = []

        for feature in selected_features:
            flow = next(
                (self._coerce_number(feature[field_name]) for field_name in flow_fields if self._coerce_number(feature[field_name]) is not None),
                None,
            )
            if flow is None:
                continue
            max_flow = flow if max_flow is None else max(max_flow, flow)

        if max_flow is not None and max_flow > 10.0:
            return 20.0
        return 10.0

    def _suggest_distance_for_feature(self, *, layer_key: str, diameter: Optional[float], depth: Optional[float], is_pressure: bool) -> Optional[float]:
        if diameter is None:
            return None

        if is_pressure:
            if diameter < 250:
                return 2.0
            if diameter < 500:
                return 2.5
            return 3.0

        depth_value = depth if depth is not None else float(self._distance_spin.value())
        if diameter < 250:
            return 2.0 if depth_value <= 2.0 else 2.5
        if diameter < 1000:
            return 2.5 if depth_value <= 2.0 else 3.0
        return 2.5 if depth_value <= 2.0 else 5.0

    def _calculate_row_distance(self, layer_key: str, source_layer) -> Optional[float]:
        if source_layer is None:
            return None

        if layer_key in self._FIXED_DISTANCE_BY_ROW:
            distance = float(self._FIXED_DISTANCE_BY_ROW[layer_key])
            self._row_distances[layer_key] = distance
            return distance

        if layer_key in self._PUMP_ROWS:
            distance = self._calculate_flow_based_distance(source_layer)
            self._row_distances[layer_key] = distance
            return distance

        diameter_fields = self._find_field_names(source_layer, self._DIAMETER_FIELD_CANDIDATES)
        depth_fields = self._find_field_names(source_layer, self._DEPTH_FIELD_CANDIDATES)
        if not diameter_fields:
            return None

        max_distance: Optional[float] = None
        max_depth: Optional[float] = None
        max_diameter: Optional[float] = None

        try:
            selected_features = list(source_layer.getSelectedFeatures())
        except Exception:
            selected_features = []

        for feature in selected_features:
            diameter = next(
                (self._coerce_number(feature[field_name]) for field_name in diameter_fields if self._coerce_number(feature[field_name]) is not None),
                None,
            )
            depth_values = [
                numeric
                for numeric in (self._coerce_number(feature[field_name]) for field_name in depth_fields)
                if numeric is not None
            ]
            depth = max(depth_values) if depth_values else None
            is_pressure = self._feature_is_pressure_pipe(layer_key, feature, source_layer)
            distance = self._suggest_distance_for_feature(
                layer_key=layer_key,
                diameter=diameter,
                depth=depth,
                is_pressure=is_pressure,
            )
            if distance is None:
                continue
            max_distance = distance if max_distance is None else max(max_distance, distance)
            if diameter is not None:
                max_diameter = diameter if max_diameter is None else max(max_diameter, diameter)
            if depth is not None:
                max_depth = depth if max_depth is None else max(max_depth, depth)

        if max_distance is not None:
            self._row_distances[layer_key] = max_distance
        else:
            self._row_distances.pop(layer_key, None)

        return max_distance

    def _refresh_rule_indicators(self) -> None:
        for key in self._ROW_KEYS:
            layer = ProjectBaseLayersService.resolve_layer(key, include_legacy=True)
            self._calculate_row_distance(key, layer)

    def _effective_row_distance(self, layer_key: str, source_layer) -> float:
        calculated = self._calculate_row_distance(layer_key, source_layer)
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

    def _existing_property_display(self, main_layer) -> dict[str, str]:
        existing_display: dict[str, str] = {}
        existing_numbers = set(self._connected_property_numbers or [])
        if existing_numbers and main_layer is not None:
            existing_feats = MapHelpers.find_features_by_fields_and_values(
                main_layer,
                Katastriyksus.tunnus,
                list(existing_numbers),
            )
            for feat in existing_feats or []:
                try:
                    num = feat[Katastriyksus.tunnus]
                except Exception:
                    num = None
                if num and num in existing_numbers:
                    existing_display[num] = self._format_property_label(num, feat)
        for num in existing_numbers:
            existing_display.setdefault(num, self._format_property_label(num))
        return existing_display

    def _merge_selected_properties_into_editor(self, selected_numbers: list[str], selected_features: list) -> None:
        feature_by_number: dict[str, object] = {}
        for feature in selected_features or []:
            try:
                number = str(feature[Katastriyksus.tunnus] or "").strip()
            except Exception:
                number = ""
            if number:
                feature_by_number[number] = feature

        merged: list[dict[str, object]] = [dict(edge) for edge in self._property_edges]
        existing_numbers = {
            str(edge.get("cadastralUnitNumber") or "").strip()
            for edge in merged
            if str(edge.get("cadastralUnitNumber") or "").strip()
        }

        for number in selected_numbers:
            clean_number = str(number or "").strip()
            if not clean_number or clean_number in existing_numbers:
                continue
            feature = feature_by_number.get(clean_number)
            display = self._format_property_label(clean_number, feature)
            merged.append(
                self._normalize_property_edge(
                    {
                        "id": "",
                        "cadastralUnitNumber": clean_number,
                        "displayAddress": display.split(" — ", 1)[0] if " — " in display else "",
                        "isPayable": False,
                    }
                )
            )
            existing_numbers.add(clean_number)

        self._set_property_edges(merged)

    def _collect_property_payloads(self) -> tuple[list[dict[str, object]], list[str]]:
        payloads: list[dict[str, object]] = []
        invalid_dates: list[str] = []

        for row_key, editors in self._property_row_widgets.items():
            edge = editors.get("edge") or {}
            number = str(edge.get("cadastralUnitNumber") or row_key or "").strip()
            property_id = str(edge.get("id") or "").strip()
            editor_widget = editors.get("editor_widget")

            unit_value = str(editor_widget.current_unit() or AreaUnit.M) if editor_widget is not None else AreaUnit.M
            square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
            area_value = square_meters / 10000.0 if unit_value == AreaUnit.H else square_meters
            price_value = float(editor_widget.price_value()) if editor_widget is not None else 0.0
            currency_value = (
                str(editor_widget.currency_code() or self._DEFAULT_CURRENCY)
                if editor_widget is not None
                else self._DEFAULT_CURRENCY
            )
            is_payable = bool(editor_widget.is_payable()) if editor_widget is not None else False
            date_text = str(editor_widget.next_payment_text() or "") if editor_widget is not None else ""
            next_payment_date = self._date_helper.date_to_iso_string(date_text) if date_text else ""
            if date_text and not next_payment_date:
                invalid_dates.append(str(edge.get("display") or number or row_key))
                continue

            payload: dict[str, object] = {
                "id": property_id,
                "cadastralUnitNumber": number,
                "isPayable": is_payable,
            }
            if area_value > 0:
                payload["area"] = {
                    "size": round(area_value, 2),
                    "unit": unit_value,
                }
            if price_value > 0:
                payload["pricePerAreaUnit"] = {
                    "amount": round(price_value, 2),
                    "currencyCode": currency_value,
                }
            if next_payment_date:
                payload["nextPaymentDate"] = next_payment_date
            payloads.append(payload)

        return payloads, invalid_dates

    def _save_property_details(self) -> None:
        if not self._item_id:
            return

        payloads, invalid_dates = self._collect_property_payloads()
        if invalid_dates:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_INVALID_DATE).format(
                    property=invalid_dates[0]
                ),
            )
            return

        unresolved_numbers = [
            str(payload.get("cadastralUnitNumber") or "").strip()
            for payload in payloads
            if not str(payload.get("id") or "").strip() and str(payload.get("cadastralUnitNumber") or "").strip()
        ]
        resolved_map, missing = APIModuleActions.resolve_property_map_by_cadastral(unresolved_numbers)
        save_payloads: list[dict[str, object]] = []
        for payload in payloads:
            property_id = str(payload.get("id") or "").strip()
            number = str(payload.get("cadastralUnitNumber") or "").strip()
            if not property_id and number:
                property_id = resolved_map.get(number, "")
                if property_id:
                    payload["id"] = property_id
            if property_id:
                save_payload = dict(payload)
                save_payload.pop("cadastralUnitNumber", None)
                save_payloads.append(save_payload)

        if not save_payloads:
            raise_message = ", ".join(missing[:5]) or ", ".join(unresolved_numbers[:5]) or "-"
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED).format(
                    pid=self._item_id,
                    count=len(payloads),
                    preview=raise_message,
                    err="No property ids resolved for save",
                ),
            )
            return

        try:
            APIModuleActions.associate_easement_properties(self._item_id, save_payloads)
            refreshed_edges = APIModuleActions.get_easement_property_edges(self._item_id) or []
            self._set_property_edges(refreshed_edges)
            layer_saved, layer_message = self._save_final_cut_to_main_layer(refreshed_edges)

            preview_numbers = [
                str(edge.get("cadastralUnitNumber") or "")
                for edge in self._property_edges
                if str(edge.get("cadastralUnitNumber") or "").strip()
            ]
            preview_text = ", ".join(preview_numbers[:5])
            extra_note = ""
            if missing:
                missing_preview = ", ".join(missing[:5])
                extra_note = "\n\n" + self._lang.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(
                    missing=missing_preview
                )
                if len(missing) > 5:
                    extra_note += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                        count=len(missing) - 5
                    )
            if len(preview_numbers) > 5:
                preview_text += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(preview_numbers) - 5
                )
            if layer_message:
                extra_note += ("\n\n" if extra_note else "\n\n") + layer_message

            success_message = self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_SUCCESS).format(
                pid=self._item_id,
                count=len(preview_numbers),
                preview=preview_text,
                extra=extra_note,
            )
            if layer_saved:
                ModernMessageDialog.show_info(
                    self._lang.translate(TranslationKeys.SUCCESS),
                    success_message,
                )
            else:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    success_message,
                )
            self._rerun_automation()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_preview_property_save_failed",
                extra={"item_id": self._item_id},
            )
            preview = ", ".join(
                str(payload.get("cadastralUnitNumber") or "")
                for payload in payloads[:5]
                if str(payload.get("cadastralUnitNumber") or "").strip()
            ) or "-"
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED).format(
                    pid=self._item_id,
                    count=len(payloads),
                    preview=preview,
                    err=str(exc),
                ),
            )

    def _finish_property_selection(self) -> None:
        try:
            if self._property_selection_orchestrator is not None:
                self._property_selection_orchestrator.cancel()
        except Exception:
            pass
        self._property_selection_orchestrator = None

    def _open_property_link_review_dialog(self, selected_numbers: list[str], selected_features: list, main_layer) -> None:
        existing_display = self._existing_property_display(main_layer)
        selected_display: dict[str, str] = {}
        for feat in selected_features or []:
            try:
                num = feat[Katastriyksus.tunnus]
            except Exception:
                num = None
            if num:
                selected_display[str(num)] = self._format_property_label(str(num), feat)
        for num in selected_numbers:
            selected_display.setdefault(num, self._format_property_label(num))

        dialog = PropertyLinkReviewDialog(existing_display, selected_display, self._lang)
        result = dialog.exec_()
        if dialog.reselect_requested:
            QTimer.singleShot(0, self._start_define_properties_flow)
            return
        if result != QDialog.Accepted:
            self._finish_property_selection()
            return

        try:
            self._merge_selected_properties_into_editor(selected_numbers, selected_features)
            self._define_properties_button.setVisible(False)
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_HINT)
            )
            QTimer.singleShot(0, lambda: self._initialize_connected_property_flow(refresh_from_backend=False))
            return
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_preview_property_link_failed",
                extra={"item_id": self._item_id},
            )
            summary = ", ".join(selected_numbers[:5])
            if len(selected_numbers) > 5:
                summary += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(selected_numbers) - 5
                )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LINK_FAILED).format(
                    pid=self._item_id,
                    count=len(selected_numbers),
                    preview=summary,
                    err=str(exc),
                ),
            )
        finally:
            self._finish_property_selection()

    def _start_define_properties_flow(self) -> None:
        if not self._item_id:
            return

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
        if main_layer is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING),
            )
            return

        try:
            main_layer.removeSelection()
        except Exception:
            pass

        if self._property_selection_orchestrator is not None:
            self._finish_property_selection()

        self._property_selection_orchestrator = MapSelectionOrchestrator(parent=self)

        def _on_selected(_layer, features: Iterable):
            self._exit_property_selection_mode()
            cadastral_numbers: list[str] = []
            selected_features = list(features or [])
            for feature in selected_features:
                try:
                    tunnus = feature[Katastriyksus.tunnus]
                except Exception:
                    tunnus = None
                if tunnus:
                    cadastral_numbers.append(str(tunnus))

            if not cadastral_numbers:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.MAP_SELECTION_NONE),
                )
                self._finish_property_selection()
                return

            self._open_property_link_review_dialog(cadastral_numbers, selected_features, main_layer)

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

    def _create_preview(self, layer_key: str) -> None:
        source_layer = self._resolve_source_layer(layer_key)
        if source_layer is None:
            self._set_row_status(layer_key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING))
            return

        try:
            selected_count = int(source_layer.selectedFeatureCount() or 0)
        except Exception:
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
                distance=self._format_distance(distance),
            ),
        )
        self._move_property_preview_to_bottom()
        self._status_label.setText(
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CREATED).format(
                preview=preview_layer.name(),
                source=source_layer.name(),
                count=f"{selected_count} · {self._format_distance(distance)} m",
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
            except Exception:
                pass

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

        try:
            final_features = list(final_layer.getFeatures())
        except Exception:
            final_features = []

        final_geometries = []
        total_final_area = 0.0
        for feature in final_features:
            try:
                geometry = feature.geometry()
            except Exception:
                geometry = None
            if geometry is None:
                continue
            final_geometries.append(geometry)
            total_final_area += self._measure_geometry_area_sqm(geometry, final_layer)

        calculated: dict[str, float] = {}
        try:
            property_features = list(self._property_layer.getSelectedFeatures())
        except Exception:
            property_features = []

        for feature in property_features:
            try:
                row_key = str(feature[Katastriyksus.tunnus] or "").strip()
            except Exception:
                row_key = ""
            if not row_key:
                continue

            try:
                property_geometry = feature.geometry()
            except Exception:
                property_geometry = None
            if property_geometry is None:
                calculated[row_key] = 0.0
                continue

            property_area = 0.0
            for final_geometry in final_geometries:
                try:
                    if not final_geometry.intersects(property_geometry):
                        continue
                    clipped = final_geometry.intersection(property_geometry)
                except Exception:
                    clipped = None
                if clipped is None:
                    continue
                property_area += self._measure_geometry_area_sqm(clipped, final_layer)

            calculated[row_key] = property_area

        self._calculated_property_area_sqm = calculated
        self._final_area_sqm = total_final_area
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
        except Exception:
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
                    if getattr(layer, "isValid", lambda: False)()
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
            style_path=getattr(QmlPaths, "EASEMENT_FINAL", None),
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

    def _run_connected_property_preview_flow(self) -> None:
        if not self._connected_property_numbers:
            self._define_properties_button.setVisible(True)
            self._property_summary_card.clear()
            for key in self._ROW_KEYS:
                self._set_row_status(key, self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED))
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT)
            )
            return

        self._define_properties_button.setVisible(False)

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

        self._property_preview_name = f"Easement properties preview · {self._item_number or self._item_id or '-'}"
        property_preview = LayerProcessingService.buffer_selected_features(
            property_layer,
            distance=float(self._distance_spin.value()),
            result_layer_name=self._property_preview_name,
            group_name=MailablGroupFolders.SANDBOXING,
            style_path=QmlPaths.EASEMENT_PROPERTIES,
            replace_existing=True,
            end_cap_style=self._buffer_end_cap_style(),
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

    def _initialize_connected_property_flow(self, *, refresh_from_backend: bool = True) -> None:
        if not self._item_id:
            return

        if refresh_from_backend:
            self._set_property_edges(APIModuleActions.get_easement_property_edges(self._item_id) or [])

        self._run_connected_property_preview_flow()

    def _clear_auto_selections(self) -> None:
        self._finish_property_selection()
        if self._property_layer is not None:
            try:
                self._property_layer.removeSelection()
            except Exception:
                pass
        for key in self._ROW_KEYS:
            layer = ProjectBaseLayersService.resolve_layer(key, include_legacy=True)
            if layer is None:
                continue
            try:
                layer.removeSelection()
            except Exception:
                pass
