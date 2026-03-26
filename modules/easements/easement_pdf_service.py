from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import (
    QgsDistanceArea,
    QgsLayoutExporter,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsPrintLayout,
    QgsProject,
    QgsReadWriteContext,
    QgsRectangle,
    QgsUnitTypes,
)
from qgis.utils import iface

from ...constants.cadastral_fields import Katastriyksus
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.responses import DataDisplayExtractors


class EasementPdfService:
    TEMPLATE_RELATIVE_PATH = Path("QGIS_styles") / "Layouts" / "MailablEasementLayoutTemp.qpt"
    MAP_ITEM_ID = "Map 1"
    AREA_ITEM_ID = "Area"
    SCALE_ITEM_ID = "Scale"
    PROPERTY_ITEM_ID = "Propertie"
    NUMBER_ITEM_ID = "EasementNr"

    @classmethod
    def export_final_cut_pdf(
        cls,
        *,
        item_data: Optional[dict],
        item_id: str,
        item_number: str,
        item_name: str,
        final_layer,
        property_layer=None,
    ) -> tuple[bool, str]:
        try:
            if final_layer is None or not getattr(final_layer, "isValid", lambda: False)():
                return False, "Invalid final cut layer"

            final_features = cls._layer_features(final_layer, selected_only=False)
            if not final_features:
                return False, "Final cut layer has no features"

            project = QgsProject.instance()
            template_path = cls._template_path()
            if not template_path.exists():
                return False, f"Template not found: {template_path}"

            layout = cls._load_template_layout(project, template_path)
            if layout is None:
                return False, "Could not load easement PDF template"

            map_item = cls._resolve_map_item(layout)
            if map_item is None:
                return False, "Template map item was not found"

            cls._configure_map_item(
                map_item,
                final_layer=final_layer,
                property_layer=property_layer,
            )
            cls._configure_legend(layout, map_item)

            total_area_sqm = cls._measure_total_area_sqm(final_layer, final_features)
            cls._set_label_text(layout, cls.AREA_ITEM_ID, f"Pindala kokku: {total_area_sqm:.2f} m²")
            cls._set_label_text(layout, cls.SCALE_ITEM_ID, f"Mõõtkava: 1:{int(round(map_item.scale()))}")
            cls._set_label_text(
                layout,
                cls.PROPERTY_ITEM_ID,
                cls._property_summary_text(property_layer=property_layer, fallback_name=item_name),
            )
            cls._set_label_text(
                layout,
                cls.NUMBER_ITEM_ID,
                f"Lepingu nr: {item_number or item_id or DataDisplayExtractors.extract_item_number(item_data) or '-'}",
            )

            pdf_path = cls._output_pdf_path(item_number=item_number, item_id=item_id)
            exporter = QgsLayoutExporter(layout)
            settings = QgsLayoutExporter.PdfExportSettings()
            result = exporter.exportToPdf(str(pdf_path), settings)
            if result != QgsLayoutExporter.Success:
                return False, f"PDF export failed with code {result}"

            return True, str(pdf_path)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="easement",
                event="easement_pdf_export_failed",
                extra={"item_id": str(item_id or "").strip()},
            )
            return False, str(exc)

    @classmethod
    def _template_path(cls) -> Path:
        return Path(__file__).resolve().parents[2] / cls.TEMPLATE_RELATIVE_PATH

    @classmethod
    def _load_template_layout(cls, project: QgsProject, template_path: Path) -> Optional[QgsPrintLayout]:
        try:
            template_xml = template_path.read_text(encoding="utf-8")
        except Exception:
            return None

        document = QDomDocument()
        try:
            set_content_result = document.setContent(template_xml)
            if isinstance(set_content_result, tuple):
                if not bool(set_content_result[0]):
                    return None
            elif not set_content_result:
                return None
        except Exception:
            return None

        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName("Kitsendus")
        try:
            layout.loadFromTemplate(document, QgsReadWriteContext())
        except Exception:
            return None
        return layout

    @classmethod
    def _resolve_map_item(cls, layout: QgsPrintLayout) -> Optional[QgsLayoutItemMap]:
        item = layout.itemById(cls.MAP_ITEM_ID)
        if isinstance(item, QgsLayoutItemMap):
            return item
        for candidate in layout.items():
            if isinstance(candidate, QgsLayoutItemMap):
                return candidate
        return None

    @classmethod
    def _configure_map_item(cls, map_item: QgsLayoutItemMap, *, final_layer, property_layer=None) -> None:
        layers = cls._map_layers(final_layer=final_layer, property_layer=property_layer)
        try:
            map_item.setKeepLayerSet(True)
            map_item.setLayers(layers)
        except Exception:
            pass

        extent = cls._combined_extent(final_layer=final_layer, property_layer=property_layer)
        if extent is not None:
            try:
                map_item.zoomToExtent(extent)
            except Exception:
                try:
                    map_item.setExtent(extent)
                except Exception:
                    pass

        try:
            map_item.refresh()
        except Exception:
            pass

    @classmethod
    def _configure_legend(cls, layout: QgsPrintLayout, map_item: QgsLayoutItemMap) -> None:
        for item in layout.items():
            if not isinstance(item, QgsLayoutItemLegend):
                continue
            try:
                item.setLinkedMap(map_item)
            except Exception:
                pass
            try:
                item.setAutoUpdateModel(True)
            except Exception:
                pass
            try:
                item.updateLegend()
            except Exception:
                pass
            try:
                item.refresh()
            except Exception:
                pass

    @classmethod
    def _set_label_text(cls, layout: QgsPrintLayout, item_id: str, text: str) -> None:
        item = layout.itemById(item_id)
        if not isinstance(item, QgsLayoutItemLabel):
            return
        try:
            item.setText(str(text or ""))
            item.refresh()
        except Exception:
            pass

    @classmethod
    def _map_layers(cls, *, final_layer, property_layer=None) -> list:
        ordered_layers = []
        seen_ids: set[str] = set()

        try:
            canvas_layers = list(iface.mapCanvas().layers()) if iface is not None else []
        except Exception:
            canvas_layers = []

        preferred_layers = list(canvas_layers)
        if property_layer is not None:
            preferred_layers = [layer for layer in preferred_layers if layer != property_layer] + [property_layer]
        if final_layer is not None:
            preferred_layers = [layer for layer in preferred_layers if layer != final_layer] + [final_layer]

        for layer in preferred_layers:
            try:
                if layer is None or not layer.isValid():
                    continue
                layer_id = str(layer.id() or "")
            except Exception:
                continue
            if not layer_id or layer_id in seen_ids:
                continue
            seen_ids.add(layer_id)
            ordered_layers.append(layer)

        return ordered_layers

    @classmethod
    def _combined_extent(cls, *, final_layer, property_layer=None) -> Optional[QgsRectangle]:
        extent = cls._extent_from_layer(final_layer, selected_only=False)

        property_extent = cls._extent_from_layer(property_layer, selected_only=True)
        if property_extent is None:
            property_extent = cls._extent_from_layer(property_layer, selected_only=False)

        if extent is None and property_extent is None:
            return None
        if extent is None:
            extent = QgsRectangle(property_extent)
        elif property_extent is not None:
            extent.combineExtentWith(property_extent)

        return cls._buffered_extent(extent)

    @classmethod
    def _extent_from_layer(cls, layer, *, selected_only: bool) -> Optional[QgsRectangle]:
        if layer is None or not getattr(layer, "isValid", lambda: False)():
            return None

        features = cls._layer_features(layer, selected_only=selected_only)
        if not features:
            return None

        combined_extent: Optional[QgsRectangle] = None
        for feature in features:
            try:
                geometry = feature.geometry()
            except Exception:
                geometry = None
            if geometry is None or geometry.isEmpty():
                continue

            try:
                bbox = geometry.boundingBox()
            except Exception:
                bbox = None
            if bbox is None or bbox.isEmpty():
                continue

            if combined_extent is None:
                combined_extent = QgsRectangle(bbox)
            else:
                combined_extent.combineExtentWith(bbox)

        return combined_extent

    @classmethod
    def _buffered_extent(cls, extent: Optional[QgsRectangle]) -> Optional[QgsRectangle]:
        if extent is None:
            return None

        try:
            buffered = QgsRectangle(extent)
            width = buffered.width()
            height = buffered.height()
        except Exception:
            return extent

        pad_x = max(width * 0.12, 5.0)
        pad_y = max(height * 0.12, 5.0)

        if width <= 0:
            pad_x = 10.0
        if height <= 0:
            pad_y = 10.0

        try:
            buffered.setXMinimum(buffered.xMinimum() - pad_x)
            buffered.setXMaximum(buffered.xMaximum() + pad_x)
            buffered.setYMinimum(buffered.yMinimum() - pad_y)
            buffered.setYMaximum(buffered.yMaximum() + pad_y)
        except Exception:
            return extent
        return buffered

    @classmethod
    def _layer_features(cls, layer, *, selected_only: bool) -> list:
        if layer is None or not getattr(layer, "isValid", lambda: False)():
            return []
        try:
            if selected_only:
                selected = list(layer.getSelectedFeatures())
                if selected:
                    return selected
                return []
            return list(layer.getFeatures())
        except Exception:
            return []

    @classmethod
    def _measure_total_area_sqm(cls, layer, features: list) -> float:
        distance_area = QgsDistanceArea()
        try:
            distance_area.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
            ellipsoid = QgsProject.instance().ellipsoid()
            if ellipsoid:
                distance_area.setEllipsoid(ellipsoid)
        except Exception:
            pass

        total = 0.0
        for feature in features:
            try:
                geometry = feature.geometry()
            except Exception:
                geometry = None
            if geometry is None or geometry.isEmpty():
                continue
            try:
                measured = distance_area.measureArea(geometry)
                total += float(distance_area.convertAreaMeasurement(measured, QgsUnitTypes.AreaSquareMeters))
            except Exception:
                try:
                    total += float(geometry.area())
                except Exception:
                    continue
        return max(0.0, total)

    @classmethod
    def _property_summary_text(cls, *, property_layer=None, fallback_name: str = "") -> str:
        labels: list[str] = []
        for feature in cls._layer_features(property_layer, selected_only=True) or cls._layer_features(property_layer, selected_only=False):
            label = cls._property_label(feature)
            if label and label not in labels:
                labels.append(label)

        if not labels:
            return str(fallback_name or "-")
        if len(labels) > 2:
            remaining = len(labels) - 2
            return f"{labels[0]}; {labels[1]} (+{remaining})"
        return "; ".join(labels)

    @classmethod
    def _property_label(cls, feature) -> str:
        if feature is None:
            return ""

        def _attr(name: str) -> str:
            try:
                return str(feature[name] or "").strip()
            except Exception:
                return ""

        address_parts = [
            _attr(Katastriyksus.mk_nimi),
            _attr(Katastriyksus.ov_nimi),
            _attr(Katastriyksus.ay_nimi),
            _attr(Katastriyksus.l_aadress),
        ]
        address = ", ".join(part for part in address_parts if part)
        number = _attr(Katastriyksus.tunnus)
        if address and number and number not in address:
            return f"{address} — {number}"
        return address or number

    @classmethod
    def _output_pdf_path(cls, *, item_number: str, item_id: str) -> Path:
        base_name = cls._safe_file_name(item_number or item_id or "easement_drawing")
        temp_root = Path(tempfile.gettempdir()) / "kavitro_easement_drawings"
        temp_root.mkdir(parents=True, exist_ok=True)
        return temp_root / f"{base_name}.pdf"

    @staticmethod
    def _safe_file_name(value: str) -> str:
        text = str(value or "").strip() or "easement_drawing"
        sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in text)
        return sanitized.strip("._") or "easement_drawing"