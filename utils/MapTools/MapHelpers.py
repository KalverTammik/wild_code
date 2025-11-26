
from typing import List, Optional
from qgis.core import QgsVectorLayer, QgsFeature, QgsRectangle, QgsProject, QgsMapLayer
from qgis.utils import iface


class MapHelpers:

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
    def _zoom_to_features_in_layer(features: List[QgsFeature], layer: QgsVectorLayer, select: bool = True, filter_layer: bool = False) -> None:
        """
        Selects the given features in a layer and zooms the map canvas to them.
        Optionally filters the layer to show only selected features.

        Args:
            features (List[QgsFeature]): A list of QgsFeature objects to zoom to.
            layer (QgsVectorLayer): The layer that contains the features.
            select (bool): Whether to select the features on the map. Default True.
            filter_layer (bool): Whether to filter the layer to show only selected features. Default False.

        Returns:
            None
        """
        if not features:
            print("⚠️ No features provided for zoom operation.")
            return

        feature_ids = [feature.id() for feature in features]
        
        # Select features if requested
        if select:
            layer.selectByIds(feature_ids)
        
        # Zoom to selected features and center the map
        iface.mapCanvas().zoomToSelected(layer)
        
        # Filter layer to show only selected features if requested
        if filter_layer and feature_ids:
            # Create a filter expression for the selected feature IDs
            id_list = ','.join(str(fid) for fid in feature_ids)
            filter_expression = f"$id IN ({id_list})"
            layer.setSubsetString(filter_expression)
            #print(f"🔍 Applied filter to layer '{layer.name()}': {filter_expression}")
        elif not filter_layer:
            # Clear any existing filter
            layer.setSubsetString("")
            #print(f"🔍 Cleared filter from layer '{layer.name()}'")


        # Ensure map extent is updated and centered
        if layer.selectedFeatureCount() > 0:
            # Get the extent of selected features
            selected_extent = layer.boundingBoxOfSelected()
            if not selected_extent.isEmpty():
                # Add some padding around the selected features
                selected_extent.scale(1.2)  # 20% padding
                iface.mapCanvas().setExtent(selected_extent)
                iface.mapCanvas().refresh()


    @staticmethod
    def _zoom_to_features_extent(features: List[QgsFeature], buffer_precent: float = 1.1) -> None:
        """
        Zooms to the combined extent of the given features without selecting them.

        Args:
            features (List[QgsFeature]): Features to zoom to.

        Returns:
            None
        """
        if not features:
            print("⚠️ No features provided.")
            return

        extent = QgsRectangle()
        extent.setMinimal()

        valid_feature_found = False

        #print(f"🔍 Received {len(features)} features.")
        
        for i, feature in enumerate(features):
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                bbox = geom.boundingBox()
                #print(f"  Feature {i} → BBox: {bbox.toString()}")
                extent.combineExtentWith(bbox)
                valid_feature_found = True
            else:
                print(f"⚠️ Feature {i} has no geometry!")

        if not valid_feature_found:
            print("❌ No valid geometries found in features.")
            return

        extent.scale(buffer_precent)  # Apply buffer
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()

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
    def select_features_by_ids(layer: QgsVectorLayer, feature_ids: List[int], zoom: bool = False) -> None:
        """Select features by their IDs and optionally zoom to them."""
        if layer and layer.isValid() and feature_ids:
            layer.selectByIds(feature_ids)
            if zoom:
                iface.mapCanvas().zoomToSelected(layer)
                iface.mapCanvas().refresh()

    @staticmethod
    def ensure_layer_visible(layer: QgsVectorLayer) -> None:
        if not layer or not layer.isValid():
            return
        root = QgsProject.instance().layerTreeRoot()
        node = root.findLayer(layer.id()) if root else None
        if node:
            node.setItemVisibilityChecked(True)

    @staticmethod
    def find_features_by_values(layer: QgsVectorLayer, field_name: str, values: List[str]) -> List[QgsFeature]:
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

    @staticmethod
    def select_and_zoom_features(layer: QgsVectorLayer, features: List[QgsFeature], filter_layer: bool = False) -> None:
        if not layer or not layer.isValid() or not features:
            return
        MapHelpers._zoom_to_features_in_layer(features, layer, select=True, filter_layer=filter_layer)