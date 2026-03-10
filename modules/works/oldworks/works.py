from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsRectangle,
    QgsFeatureRequest,
    QgsGeometry,
    QgsVectorLayer,
    edit
)
from qgis.utils import iface

from .worksHelpers import worksHelpers
from ...KeelelisedMuutujad.modules import Module
from ...Functions.AsBuilt.ASBuilt import TaskMain
from ...config.settings_new import PluginSettings
from ...core.module.statusManager import ModuleStatuses


class PointCaptureTool(QgsMapTool):
    def __init__(self, canvas, callback, cancel_callback=None):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.cancel_callback = cancel_callback
        self.setCursor(Qt.CrossCursor)
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self.callback(point)
        elif event.button() == Qt.RightButton:
            print("❌ Reposition cancelled via right click")
            if self.cancel_callback:
                self.cancel_callback()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("❌ Reposition cancelled via ESC")
            if self.cancel_callback:
                self.cancel_callback()

_tool_instance = None  # avoid GC

def start_work_capture(plugin_instance):
    plugin_instance.setWindowState(Qt.WindowMinimized)
    global _tool_instance

    def handle_point_selected(point: QgsPointXY):
        #print(f"📍 Point selected in works module: {point}")
        # Restore default pan tool or whatever tool was before
        module = Module.WORKS

        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )

        works_layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]
        if not works_layer:
            raise ValueError(f"No layer found with the name {works_layer_name}")
        

        worksHelpers.insert_work_feature(point, plugin_instance)        # Now you have the 'tunnus' of the property at that location.
        
        iface.mapCanvas().unsetMapTool(_tool_instance)
        iface.actionPan().trigger()  # activate pan tool again
        # You can now open a dialog, insert feature, etc.

    canvas = iface.mapCanvas()
    _tool_instance = PointCaptureTool(canvas, handle_point_selected)
    canvas.setMapTool(_tool_instance)


# ----------------------------
# FeatureSelectTool – click to select a feature by geometry
# ----------------------------
class FeatureSelectTool(QgsMapTool):
    def __init__(self, canvas, layer: QgsVectorLayer, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.callback = callback

    def canvasReleaseEvent(self, event):
        print("canvasReleaseEvent")
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            feature_id = self._identify_feature(point)
            if feature_id is not None:
                self.callback(feature_id)


    def _identify_feature(self, point: QgsPointXY):
        print("_identify_feature")
        search_rect = QgsRectangle(
            point.x() - 5, point.y() - 5,
            point.x() + 5, point.y() + 5
        )
        print("search_rect", search_rect)
        request = QgsFeatureRequest().setFilterRect(search_rect)

        closest_feature = None
        closest_distance = float("inf")

        for feature in self.layer.getFeatures(request):
            geom = feature.geometry()
            if not geom:
                continue
            dist = geom.distance(QgsGeometry.fromPointXY(point))
            if dist < 5 and dist < closest_distance:
                closest_feature = feature
                closest_distance = dist

        if closest_feature:
            feature_id = closest_feature.id()
            print(f"✅ Closest feature found with ID: {feature_id}, distance: {closest_distance}")

            # Highlight (select) it on the layer
            self.layer.removeSelection()
            self.layer.selectByIds([feature_id])

            return feature_id

        print("❌ No nearby point feature found.")
        return None


    @staticmethod
    def start_feature_select(layer: QgsVectorLayer, on_selected_callback):
        print("start_feature_select")
        global _tool_instance
        canvas = iface.mapCanvas()
        _tool_instance = FeatureSelectTool(canvas, layer, on_selected_callback)
        canvas.setMapTool(_tool_instance)



class WorksManipulator:
    @staticmethod
    def reposition_feature(layer: QgsVectorLayer, feature_id: int, new_point: QgsPointXY) -> bool:
        if not layer.isEditable():
            layer.startEditing()

        feature = next(layer.getFeatures(QgsFeatureRequest(feature_id)), None)
        if not feature:
            print(f"❌ Feature with ID {feature_id} not found.")
            return False

        new_geom = QgsGeometry.fromPointXY(new_point)
        success = layer.changeGeometry(feature_id, new_geom)

        if success:
            print(f"✅ Moved feature {feature_id} to {new_point}")
        else:
            print(f"❌ Failed to move feature {feature_id}")
        return success

    
class WorkMapHelper:
    @staticmethod
    def begin_reposition_work_feature(task_id: str):
        module = Module.WORKS
        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )
        layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]

        #print("🔍 Searching for feature with Mailabl_id:", task_id)

        # Find the feature with Mailabl_id = task_id
        matching_feature = None
        for feature in layer.getFeatures():
            if str(feature["Mailabl_id"]) == str(task_id):
                matching_feature = feature
                break

        if not matching_feature:
            print(f"❌ No feature found with Mailabl_id = {task_id}")
            return

        fid = matching_feature.id()
        #print(f"✅ Feature with Mailabl_id {task_id} found, FID: {fid}")

        # Zoom to and select the feature
        layer.removeSelection()
        layer.selectByIds([fid])
        canvas = iface.mapCanvas()
        canvas.setExtent(matching_feature.geometry().boundingBox())
        canvas.refresh()

        # Set up reposition tool
        def on_new_location_chosen(new_point: QgsPointXY):
            WorksManipulator.reposition_feature(layer, fid, new_point)
            layer.commitChanges()
            iface.mapCanvas().unsetMapTool(_tool_instance)
            iface.actionPan().trigger()

        def on_cancel_reposition():
            print("🚫 Reposition cancelled")
            layer.removeSelection()
            iface.mapCanvas().unsetMapTool(_tool_instance)
            iface.actionPan().trigger()

        WorkMapHelper.start_point_capture_for_reposition(on_new_location_chosen, on_cancel_reposition)


    @staticmethod
    def start_point_capture_for_reposition(callback, cancel_callback=None):
        global _tool_instance
        canvas = iface.mapCanvas()
        _tool_instance = PointCaptureTool(canvas, callback, cancel_callback)
        canvas.setMapTool(_tool_instance)

    @staticmethod
    def update_fature_statuses_by_closing_map_fetures():
        module = Module.WORKS
        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )
        layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]
        if not layer.isEditable():
            layer.startEditing()

        feature_column = "Mailabl_id"
        status_column = "status"


        for feature in layer.getFeatures():
            status_value = feature[status_column]

            # Safely check if status is exactly True (ignores None, False, 0, etc.)
            if isinstance(status_value, bool) and status_value is True:
                task_id = feature[feature_column]
                print(f"✅ Feature ID {task_id} is active (status = True)")
            
                details =TaskMain.load_task_data(task_id)
                
                status_type = details["data"]["task"]["status"]["type"]
                if status_type == "CLOSED":
                    active_state = False
                else:
                    active_state = True
                feature.setAttribute("status", active_state)
                layer.changeAttributeValue(feature.id(), layer.fields().indexFromName("status"), active_state)

        layer.commitChanges()

    def update_map_based_on_open_task_in_mylabl():
        module = Module.TASK

        types_ids = PluginSettings.load_setting(
                module=Module.WORKS,
                context=PluginSettings.CONTEXT_PREFERRED,
                subcontext=PluginSettings.OPTION_TYPE,
                key_type=PluginSettings.SUB_CONTEXT_IDs,
            )
                
        #print("types_ids", types_ids)
        status_manager = ModuleStatuses(module)
        statuses = status_manager._get_all_statuses_for_module(module)
        #print("All statuses", statuses)
        open_statuses = [id for _, id, status_type in statuses if status_type == "OPEN"]

        fetched_data =TaskMain.load_task_open_stauses(open_statuses, types_ids, module=module)
        for edge in fetched_data:  # Use just fetched_data here to avoid duplicates
                task = edge["node"]
                task_id = task["id"]
                status_type = task["status"]["type"]
                task_type = task["type"]["name"]
                priority = task.get("priority", "None")
        # ✅ Extract all task IDs where the status.type is OPEN
        open_task_ids = {
            edge["node"]["id"]
            for edge in fetched_data
            if edge["node"]["status"]["type"] == "OPEN"
        }

        print("✅ Open Task IDs:", open_task_ids)
        module = Module.WORKS
        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )
        layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]
        if not layer.isEditable():
            layer.startEditing()

        feature_column = "Mailabl_id"
        status_column = "status"
        status_idx = layer.fields().indexFromName(status_column)
        for feature in layer.getFeatures():
            task_id = str(feature[feature_column])  # Ensure string for comparison

            active_state = task_id in open_task_ids
            current_status = feature[status_column]

            if current_status != active_state:
                #print(f"🔄 Updating feature {feature.id()} (Mailabl_id={task_id}): {current_status} → {active_state}")
                layer.changeAttributeValue(feature.id(), status_idx, active_state)

        layer.updateFields()  # Optional, if schema changed
        layer.commitChanges()

    @staticmethod
    def update_fature_statuses_by_closing_map_fetures():
        module = Module.WORKS
        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )
        layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]
        if not layer.isEditable():
            layer.startEditing()

        feature_column = "Mailabl_id"
        status_column = "status"

        for feature in layer.getFeatures():
            status_value = feature[status_column]

            # Safely check if status is exactly True (ignores None, False, 0, etc.)
            if isinstance(status_value, bool) and status_value is True:
                task_id = feature[feature_column]
                #print(f"✅ Feature ID {task_id} is active (status = True)")
            
                details =TaskMain.load_task_data(task_id)
                if not details or "data" not in details or not details["data"].get("task"):
                    print(f"⚠️ Could not fetch task details for ID: {task_id}")
                    continue  # skip this feature if task data couldn't be loaded

                status_type = details["data"]["task"]["status"]["type"]
                if status_type == "CLOSED":
                    active_state = False
                else:
                    active_state = True
                feature.setAttribute("status", active_state)
                layer.changeAttributeValue(feature.id(), layer.fields().indexFromName("status"), active_state)

        layer.commitChanges()
        iface.mapCanvas().refresh()