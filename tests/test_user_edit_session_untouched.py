"""A layer the user is already editing: the plugin refuses instead of saving the user's edits.

QGIS saves a whole edit session at once (commitChanges), so a plugin action that saves into a
session the user opened would also save the user's unrelated pending edits. Found 2026-11-23 in
the property delete, the work reposition and the drawing flows.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

from Kavitro_dev.modules.Property.FlowControllers import property_action_service as actions
from Kavitro_dev.modules.works import works_reposition_controller as reposition
from Kavitro_dev.utils.MapTools.MapHelpers import FeatureActions


class UserEditSessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self):
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301&field=tunnus:string", "kinnistud", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(["1:1"])
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
        self.layer.dataProvider().addFeatures([feature])
        self.assertTrue(self.layer.startEditing())
        pending = QgsFeature(self.layer.fields())
        pending.setAttributes(["2:2"])
        pending.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(2, 2)))
        self.assertTrue(self.layer.addFeature(pending))
        self.addCleanup(lambda: self.layer.isEditable() and self.layer.rollBack())

    def assert_session_untouched(self):
        self.assertTrue(self.layer.isEditable())
        self.assertEqual(self.layer.featureCount(), 2)  # saved one + the user's pending one
        self.assertEqual(self.layer.dataProvider().featureCount(), 1)  # nothing was saved

    def test_deleting_map_features_refuses_a_layer_in_edit_mode(self):
        ok, ids, error = FeatureActions.delete_features_by_field_values(self.layer, "tunnus", ["1:1"])
        self.assertFalse(ok)
        self.assertIn("kinnistud", error)
        self.assert_session_untouched()

    def test_deleting_properties_stops_before_kavitro_when_the_layer_is_in_edit_mode(self):
        with patch.object(actions.BackendPropertyActions, "delete_properties_by_tunnused") as backend_delete:
            result = actions.PropertyActionService.run_action("delete", ["1:1"], main_layer=self.layer)
        self.assertFalse(result.ok)
        self.assertIn("kinnistud", result.message)
        backend_delete.assert_not_called()
        self.assert_session_untouched()

    def test_a_work_reposition_does_not_start_on_a_layer_in_edit_mode(self):
        controller = reposition.WorksRepositionController()
        with patch.object(reposition.WorksLayerService, "resolve_main_layer", return_value=self.layer), \
                patch.object(reposition.WorksLayerService, "find_feature_by_task_id") as find, \
                patch.object(reposition, "ModernMessageDialog") as dialogs, \
                patch.object(reposition, "iface", Mock()):
            started = controller.start_reposition(task_id="7")
        self.assertFalse(started)
        dialogs.show_warning.assert_called_once()
        self.assertIn("kinnistud", dialogs.show_warning.call_args.args[1])
        find.assert_not_called()
        self.assert_session_untouched()


if __name__ == "__main__":
    unittest.main()
