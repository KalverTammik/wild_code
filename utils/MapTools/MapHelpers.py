from typing import Iterable, List, Optional, Sequence, Union
from ...languages.translation_keys import TranslationKeys
from qgis.core import QgsVectorLayer, QgsFeature, QgsRectangle, QgsProject, QgsMapLayer
from qgis.utils import iface
from ...utils.url_manager import Module
from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...utils.messagesHelper import ModernMessageDialog

class MapHelpers:

    @staticmethod
    def _sql_quote(value: object) -> str:
        """Best-effort SQL literal quoting for subset strings."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        text = text.replace("'", "''")
        return f"'{text}'"

    @staticmethod
    def _quote_field(field_name: str) -> str:
        """Quote a field name for provider SQL (OGR/SQLite/Postgres, etc)."""
        name = (field_name or "").strip().replace('"', '""')
        return f'"{name}"'

    @staticmethod
    def build_subset_in_clause(field_name: str, values: Sequence[object], *, chunk_size: int = 500) -> str:
        """Build a provider subset string like: "field" IN ('a','b',...) with chunking."""
        field = MapHelpers._quote_field(field_name)
        cleaned: List[object] = []
        seen = set()
        for v in values or []:
            if v is None:
                continue
            key = str(v)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(v)

        if not cleaned:
            return ""

        chunk = max(1, int(chunk_size))
        parts: List[str] = []
        for i in range(0, len(cleaned), chunk):
            segment = cleaned[i : i + chunk]
            literals = ",".join(MapHelpers._sql_quote(v) for v in segment)
            parts.append(f"{field} IN ({literals})")
        return " OR ".join(parts)

    @staticmethod
    def _find_best_id_field(layer: QgsVectorLayer) -> Optional[str]:
        """Try to find a usable id field for subsetString filters."""
        if not layer or not layer.isValid():
            return None

        # Prefer provider primary key if it's a single attribute.
        try:
            provider = layer.dataProvider()
            pk_indexes = []
            if provider is not None and callable(getattr(provider, "pkAttributeIndexes", None)):
                pk_indexes = list(provider.pkAttributeIndexes() or [])
            if len(pk_indexes) == 1:
                idx = int(pk_indexes[0])
                field = layer.fields().field(idx)
                if field is not None:
                    return field.name()
        except Exception:
            pass

        # Common id field names across providers
        candidates = [
            "fid",
            "FID",
            "ogc_fid",
            "OGC_FID",
            "objectid",
            "OBJECTID",
            "id",
            "ID",
        ]
        try:
            fields = layer.fields()
            for name in candidates:
                if fields.indexOf(name) != -1:
                    return name
        except Exception:
            pass

        return None

    @staticmethod
    def find_layer_by_id(layer_id: Optional[str]) -> Optional[QgsMapLayer]:
        """Return the live layer for a given ID if it exists in the project."""
        if not layer_id:
            return None
        project = QgsProject.instance()
        if not project:
            return None
        try:
            return project.mapLayer(layer_id)
        except Exception:
            return None



    def _get_layer_by_tag(tag):
        # uing traceback to find where its trigered from max of three levels
        #import traceback
        #show who is calling this function for debugging
        #print("_get_layer_by_tag Called from:")
        #traceback.print_stack(limit=10)
      

        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if layer.customProperty(tag):
                #print(f"[MapHelpers] Checking layer: {layer.name()} with tag {tag}: {layer.customProperty(tag)}")  
                return layer
        return None

    @staticmethod
    def find_layer_by_name(layer_name: Optional[str], *, case_sensitive: bool = False) -> Optional[QgsMapLayer]:
        """Resolve the first layer that matches the provided name."""
        if not layer_name:
            return None
        project = QgsProject.instance()
        if not project:
            return None
        target = layer_name if case_sensitive else layer_name.lower()
        for layer in project.mapLayers().values():
            try:
                candidate = layer.name()
            except Exception:
                continue
            if not candidate:
                continue
            compare_value = candidate if case_sensitive else candidate.lower()
            if compare_value == target:
                return layer
        return None

    @staticmethod
    def resolve_layer_id(identifier: Optional[str]) -> Optional[str]:
        """Map a stored identifier (legacy ID or layer name) to a live layer ID."""
        if not identifier:
            return None
        # Legacy behaviour stored IDs directly, so prefer a direct lookup first.
        legacy_layer = MapHelpers.find_layer_by_id(identifier)
        if legacy_layer:
            return legacy_layer.id()
        layer = MapHelpers.find_layer_by_name(identifier)
        return layer.id() if layer else None

    @staticmethod
    def resolve_layer(identifier: Optional[str]) -> Optional[QgsMapLayer]:
        """Resolve a stored identifier to the current QgsMapLayer instance."""
        resolved_id = MapHelpers.resolve_layer_id(identifier)
        return MapHelpers.find_layer_by_id(resolved_id) if resolved_id else None

    @staticmethod
    def layer_name_from_id(layer_id: Optional[str]) -> str:
        """Safely return the name for a given layer id."""
        layer = MapHelpers.find_layer_by_id(layer_id)
        return layer.name() if layer else ""

    @staticmethod
    def _zoom_to_features_in_layer(
        features: List[QgsFeature],
        layer: QgsVectorLayer,
        select: bool = True,
        clear_existing: bool = True,
        padding_factor: float = 1.2,
    ) -> None:
        if not features:
            print("⚠️ No features provided for zoom operation.")
            return
        
        print(f"Zooming to {len(features)} features in layer '{layer.name()}'")

        # Build an extent from the *geometries*, so zoom works even if select=False
        extent: QgsRectangle | None = None
        for f in features:
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                continue
            bb = geom.boundingBox()
            if extent is None:
                extent = QgsRectangle(bb)
            else:
                extent.combineExtentWith(bb)

        #print(f"Computed extent for zoom: {extent}")
        if extent is None or extent.isEmpty():
            print("⚠️ Features had no valid geometry for zoom operation.")
            return

        # Optional: clear old selection (but don't do it unless you really mean it)
        if clear_existing:
            layer.removeSelection()

        # Optional: select the features
        if select:
            feature_ids = [f.id() for f in features]
            layer.selectByIds(feature_ids)

        # Apply padding + zoom
        if padding_factor and padding_factor > 0:
            extent.scale(padding_factor)

        canvas = iface.mapCanvas()
        canvas.setExtent(extent)
        canvas.refresh()


    @staticmethod
    def zoom_to_layer(layer: QgsVectorLayer) -> None:
        """Zoom to the full extent of a layer."""
        if layer and layer.isValid():
            iface.mapCanvas().setExtent(layer.extent())
            iface.mapCanvas().refresh()

    @staticmethod
    def clear_layer_filter(layer: QgsVectorLayer) -> None:
        """Clear any filter applied to a layer."""
        if layer and layer.isValid():
            layer.setSubsetString("")
            print(f"🔍 Cleared filter from layer '{layer.name()}'")

    @staticmethod
    def set_layer_filter_by_field_values(
        layer: QgsVectorLayer,
        field_name: str,
        values: Sequence[object],
        *,
        clear_if_empty: bool = True,
        chunk_size: int = 500,
    ) -> None:
        """Set subset string to keep only rows where field is in values."""
        if not layer or not layer.isValid():
            return
        clause = MapHelpers.build_subset_in_clause(field_name, values, chunk_size=chunk_size)
        if not clause:
            if clear_if_empty:
                MapHelpers.clear_layer_filter(layer)
            return
        layer.setSubsetString(clause)

    @staticmethod
    def set_layer_filter_by_features(
        layer: QgsVectorLayer,
        field_name: str,
        features: Union[Sequence[QgsFeature], Iterable[QgsFeature]],
        *,
        clear_if_empty: bool = True,
        chunk_size: int = 500,
    ) -> None:
        """Set subset string based on a field extracted from provided features."""
        if not layer or not layer.isValid():
            return
        extracted: List[object] = []
        for f in features or []:
            try:
                extracted.append(f[field_name])
            except Exception:
                continue
        MapHelpers.set_layer_filter_by_field_values(
            layer,
            field_name,
            extracted,
            clear_if_empty=clear_if_empty,
            chunk_size=chunk_size,
        )

    @staticmethod
    def set_layer_filter_to_features(
        layer: QgsVectorLayer,
        features: Union[Sequence[QgsFeature], Iterable[QgsFeature]],
        *,
        field_name: Optional[str] = None,
        clear_if_empty: bool = True,
        chunk_size: int = 500,
    ) -> None:
        """Set subset string from a list of QgsFeature objects.

        - If `field_name` is provided: uses that attribute from features.
        - Else: tries provider PK / common id fields; falls back to feature.id() when possible.
        """
        if not layer or not layer.isValid():
            return

        feats = list(features or [])
        if not feats:
            if clear_if_empty:
                MapHelpers.clear_layer_filter(layer)
            return

        if field_name:
            MapHelpers.set_layer_filter_by_features(
                layer,
                field_name,
                feats,
                clear_if_empty=clear_if_empty,
                chunk_size=chunk_size,
            )
            return

        best_field = MapHelpers._find_best_id_field(layer)
        if best_field:
            MapHelpers.set_layer_filter_by_features(
                layer,
                best_field,
                feats,
                clear_if_empty=clear_if_empty,
                chunk_size=chunk_size,
            )
            return

        # Last-resort: attempt to filter by feature ids using a guessed fid field.
        # Not all providers expose an id column for subsetString; if this doesn't work,
        # caller should prefer selection APIs.
        ids = [f.id() for f in feats if f is not None]
        if not ids:
            if clear_if_empty:
                MapHelpers.clear_layer_filter(layer)
            return
        clause = MapHelpers.build_subset_in_clause("fid", ids, chunk_size=chunk_size)
        layer.setSubsetString(clause)

    @staticmethod
    def set_layer_filter_to_selected_features(
        layer: QgsVectorLayer,
        *,
        field_name: Optional[str] = None,
        clear_if_empty: bool = True,
        chunk_size: int = 500,
    ) -> None:
        """Convenience: subsetString from `layer.selectedFeatures()`."""
        if not layer or not layer.isValid():
            return
        try:
            feats = layer.selectedFeatures() or []
        except Exception:
            feats = []
        MapHelpers.set_layer_filter_to_features(
            layer,
            feats,
            field_name=field_name,
            clear_if_empty=clear_if_empty,
            chunk_size=chunk_size,
        )

    @staticmethod
    def select_features_by_ids(layer: QgsVectorLayer, feature_ids: List[int], zoom: bool = False) -> None:
        """Select features by their IDs and optionally zoom to them."""
        if layer and layer.isValid() and feature_ids:
            layer.selectByIds(feature_ids)
            if zoom:
                iface.mapCanvas().zoomToSelected(layer)
                iface.mapCanvas().refresh()

    @staticmethod
    def ensure_layer_visible(layer: QgsVectorLayer, make_active: bool = False) -> None:
        if not layer or not layer.isValid():
            return
        root = QgsProject.instance().layerTreeRoot()
        node = root.findLayer(layer.id()) if root else None
        if node:
            node.setItemVisibilityChecked(True)

        if make_active:
            try:
                iface.setActiveLayer(layer)
            except Exception:
                pass

    @staticmethod
    def find_features_by_fields_and_values(layer: QgsVectorLayer, field_name: str, values: List[str]) -> List[QgsFeature]:
        if not layer or not layer.isValid() or not values:
            return []
        lookup = set(values)
        matches: List[QgsFeature] = []
        for feature in layer.getFeatures():
            try:
                if feature[field_name] in lookup:
                    matches.append(feature)
            except KeyError:
                continue
        return matches


class ActiveLayersHelper:

    @staticmethod
    def _get_active_property_layer():
        layer_id = SettingsService().module_main_layer_name(Module.PROPERTY.value) or ""
        active_layer = MapHelpers.resolve_layer(layer_id)
        if not active_layer:
            ModernMessageDialog.Warning_messages_modern(
                "Property layer not configured or missing from project",
                LanguageManager().translate(TranslationKeys.ERROR),
            )
            return None
        return active_layer
