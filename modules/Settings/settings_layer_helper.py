from qgis.core import QgsProject
from qgis.gui import QgsMapLayerComboBox

from ...utils.MapTools.MapHelpers import MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module


class SettingsLayerHelper:
    @staticmethod
    def set_combo_project(
        combo: QgsMapLayerComboBox | None,
        project,
    ) -> None:
        if combo is None:
            return
        try:
            current = combo.project() if hasattr(combo, "project") else None
            if current is project:
                return
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_layer_combo_project_query_failed",
            )
        combo.setProject(project)

    @staticmethod
    def restore_combo_selection(
        combo: QgsMapLayerComboBox | None,
        stored_name: str,
    ) -> None:
        if not combo:
            return
        try:
            resolved_id = MapHelpers.resolve_layer_id(stored_name)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_module_resolve_layer_failed",
            )
            resolved_id = None

        project = QgsProject.instance() if QgsProject else None
        layer = project.mapLayer(resolved_id) if (project and resolved_id) else None

        try:
            combo.blockSignals(True)
            combo.setLayer(layer)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_module_set_layer_failed",
            )
            combo.setLayer(None)
        finally:
            combo.blockSignals(False)

    @staticmethod
    def clear_combo_selection(combo: QgsMapLayerComboBox | None) -> None:
        if not combo:
            return
        try:
            combo.blockSignals(True)
            combo.setLayer(None)
        finally:
            combo.blockSignals(False)

    @staticmethod
    def connect_project_layer_signals(
        *,
        project,
        handler,
        layer_will_be_removed_handler=None,
    ) -> bool:
        if project is None:
            return False
        try:
            project.layersAdded.connect(handler)
            project.layersRemoved.connect(handler)
            if layer_will_be_removed_handler is not None:
                project.layerWillBeRemoved.connect(layer_will_be_removed_handler)
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_module_layer_signal_connect_failed",
            )
            return False

    @staticmethod
    def disconnect_project_layer_signals(
        *,
        project,
        handler,
        layer_will_be_removed_handler=None,
    ) -> None:
        if project is None:
            return
        try:
            project.layersAdded.disconnect(handler)
            project.layersRemoved.disconnect(handler)
            if layer_will_be_removed_handler is not None:
                project.layerWillBeRemoved.disconnect(layer_will_be_removed_handler)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="settings_module_layer_signal_disconnect_failed",
            )
