"""Map layer and Kavitro stay the same, and the dialogs say what happened.

Found in the button audits, fixed 2026-11-23:
- project board: links of other modules were read from the first page of 30 only;
- project preview save never sent the area to Kavitro;
- drawing a project area again added a second feature with the same id;
- easement final save and as-built drawing: a failed Kavitro update could not be sent again;
- easement preview: the status line was hidden for good and "Define properties from map" vanished
  once the easement had links;
- an as-built status change synced the Works layer instead of the as-built layer.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer

from Kavitro_dev.constants.module_names import Module
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements import easement_preview_dialog as easement_preview_module
from Kavitro_dev.modules.easements.preview_dialog import final_save_mixin as final_save_module
from Kavitro_dev.modules.easements.preview_dialog import preview_layers_mixin as preview_layers_module
from Kavitro_dev.modules.Property import query_coordinator
from Kavitro_dev.modules.projects import project_preview_dialog as project_preview_module
from Kavitro_dev.modules.projects import projects_feature_map_controller as projects_controller_module
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.ui.map_tools import kavitro_sync_retry
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.utils.project_base_layers import ProjectBaseLayersService

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager()


def first_button(*_args, **kwargs):
    return kwargs["buttons"][0]


def square(x0: float, size: float = 10.0) -> QgsGeometry:
    return QgsGeometry.fromWkt(f"POLYGON(({x0} 0, {x0 + size} 0, {x0 + size} {size}, {x0} {size}, {x0} 0))")


class DialogStubCase(unittest.TestCase):
    def setUp(self) -> None:
        # A real message window would wait for a click that never comes.
        for name in ("show_warning", "show_info", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)


class RetryHelperTest(DialogStubCase):
    def offer(self, sync):
        return kavitro_sync_retry.offer_kavitro_sync_retry(
            sync, failure_message=lambda detail: f"failed: {detail}", title="E", log_module="test",
            first_detail="first",
        )

    def test_try_again_until_kavitro_takes_it(self) -> None:
        self.ask_choice_modern.side_effect = first_button
        sync = Mock(side_effect=[(False, "second"), (True, "")])

        self.assertTrue(self.offer(sync))

        self.assertEqual(sync.call_count, 2)
        texts = [c.args[1] for c in self.ask_choice_modern.call_args_list]
        self.assertTrue(texts[0].startswith("failed: first\n\n"))
        self.assertTrue(texts[1].startswith("failed: second\n\n"))
        self.assertIn(LANG.translate(TranslationKeys.KAVITRO_SYNC_DIFFERS_NOTE), texts[0])

    def test_leaving_it_sends_nothing_more(self) -> None:
        self.ask_choice_modern.side_effect = lambda *_a, **kw: kw["buttons"][1]
        sync = Mock(return_value=(True, ""))

        self.assertFalse(self.offer(sync))
        sync.assert_not_called()

    def test_closing_the_question_leaves_it(self) -> None:
        self.ask_choice_modern.return_value = None
        self.assertFalse(self.offer(Mock()))

    def test_a_raising_update_counts_as_failed(self) -> None:
        self.ask_choice_modern.side_effect = [LANG.translate(TranslationKeys.KAVITRO_SYNC_RETRY), None]
        sync = Mock(side_effect=RuntimeError("network gone"))

        self.assertFalse(self.offer(sync))
        self.assertTrue(self.ask_choice_modern.call_args_list[1].args[1].startswith("failed: network gone"))


class EasementFinalSaveTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        dialog = easement_preview_module.EasementPreviewDialog.__new__(easement_preview_module.EasementPreviewDialog)
        dialog._lang = LANG
        dialog._item_id = "42"
        dialog._item = {"id": "42"}
        dialog._on_status_changed = None
        dialog._ensure_final_cut_layer = Mock(return_value=(object(), ""))
        dialog._easement_form_initial_values = Mock(return_value={})
        dialog._sync_saved_easement_geometry_to_backend = Mock(side_effect=[False, True])
        self.dialog = dialog
        self.layer = Mock(isEditable=Mock(return_value=False))
        self.layer.name.return_value = "Servituudid"
        for target, name, value in (
            (final_save_module.EasementLayerService, "resolve_main_layer", self.layer),
            (final_save_module.EasementGeometryFormDialog, "prompt", {}),
            (final_save_module.EasementLayerService, "upsert_final_cut_feature", (True, "Servituudid")),
        ):
            patcher = patch.object(target, name, return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def save(self):
        return easement_preview_module.EasementPreviewDialog._save_final_cut_to_main_layer(self.dialog, [], [])

    def test_a_failed_geometry_update_can_be_sent_again(self) -> None:
        self.ask_choice_modern.side_effect = first_button

        ok, _message = self.save()

        self.assertTrue(ok)
        self.assertEqual(self.dialog._sync_saved_easement_geometry_to_backend.call_count, 2)

    def test_leaving_it_reports_the_difference(self) -> None:
        self.ask_choice_modern.return_value = None

        ok, message = self.save()

        self.assertFalse(ok)
        self.assertEqual(message, LANG.translate(TranslationKeys.EASEMENT_FINAL_GEOMETRY_SYNC_FAILED))

    def test_a_layer_in_edit_mode_is_refused_before_the_form(self) -> None:
        self.layer.isEditable.return_value = True

        ok, message = self.save()

        self.assertFalse(ok)
        self.assertIn("Servituudid", message)
        self.prompt.assert_not_called()
        self.upsert_final_cut_feature.assert_not_called()


class ProjectPreviewSaveTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        dialog = project_preview_module.ProjectPreviewDialog.__new__(project_preview_module.ProjectPreviewDialog)
        dialog._lang = LANG
        dialog._item_id = "5"
        dialog._item = {"id": "5"}
        dialog._preview_layer = Mock(return_value=object())
        dialog._send_area_to_kavitro = Mock(side_effect=[(False, "refused"), (True, "")])
        self.dialog = dialog
        self.layer = Mock(isEditable=Mock(return_value=False))
        self.layer.name.return_value = "Projektid"
        service = project_preview_module.ProjectsLayerService
        for name, value in (("resolve_main_layer", self.layer), ("upsert_generated_area_feature", (True, "Projektid"))):
            patcher = patch.object(service, name, return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_the_saved_area_goes_to_kavitro_and_can_be_sent_again(self) -> None:
        self.ask_choice_modern.side_effect = first_button

        self.dialog._save_preview_to_main_layer()

        self.assertEqual(self.dialog._send_area_to_kavitro.call_count, 2)
        self.assertIn("refused", self.ask_choice_modern.call_args.args[1])
        self.show_info.assert_called_once()
        self.show_warning.assert_not_called()

    def test_leaving_it_shows_no_success(self) -> None:
        self.ask_choice_modern.return_value = None

        self.dialog._save_preview_to_main_layer()

        self.show_info.assert_not_called()
        self.show_warning.assert_not_called()

    def test_a_layer_in_edit_mode_is_refused(self) -> None:
        self.layer.isEditable.return_value = True

        self.dialog._save_preview_to_main_layer()

        self.upsert_generated_area_feature.assert_not_called()
        self.dialog._send_area_to_kavitro.assert_not_called()
        self.assertIn("Projektid", self.show_warning.call_args.args[1])

    def test_the_area_on_the_layer_is_what_kavitro_gets(self) -> None:
        layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3301&field=ext_project_id:string", "p", "memory")
        feature = QgsFeature(layer.fields())
        feature.setAttributes(["5"])
        feature.setGeometry(square(0))
        layer.dataProvider().addFeatures([feature])
        dialog = project_preview_module.ProjectPreviewDialog.__new__(project_preview_module.ProjectPreviewDialog)
        dialog._item_id, dialog._item = "5", {"id": "5"}

        with patch.object(project_preview_module.APIModuleActions, "update_project_geometry", return_value=True) as send:
            self.assertEqual(dialog._send_area_to_kavitro(layer), (True, ""))

        item_id, payload = send.call_args.args
        self.assertEqual(item_id, "5")
        self.assertIn("Polygon", str(payload.get("type")))


class ProjectAreaTest(DialogStubCase):
    def layer(self, kind: str = "MultiPolygon") -> QgsVectorLayer:
        layer = QgsVectorLayer(f"{kind}?crs=EPSG:3301&field=ext_project_id:string", "Projektid", "memory")
        old = QgsFeature(layer.fields())
        old.setAttributes(["5"])
        old.setGeometry(square(0))
        other = QgsFeature(layer.fields())
        other.setAttributes(["6"])
        other.setGeometry(square(50))
        layer.dataProvider().addFeatures([old, other])
        return layer

    @staticmethod
    def draw(layer: QgsVectorLayer) -> int:
        """The draw flow's state: a new feature with the project id, in an open session."""
        layer.startEditing()
        drawn = QgsFeature(layer.fields())
        drawn.setAttributes(["5"])
        drawn.setGeometry(square(20))
        layer.addFeature(drawn)
        return drawn.id()

    def areas(self, layer: QgsVectorLayer, item_id: str = "5") -> list[float]:
        return sorted(f.geometry().area() for f in layer.getFeatures() if f["ext_project_id"] == item_id)

    def test_replace_leaves_only_the_drawn_area(self) -> None:
        layer = self.layer()
        drawn_id = self.draw(layer)

        ok, _error = ProjectsLayerService.fold_existing_areas(
            layer, keep_feature_id=drawn_id, item_id="5", mode=ProjectsLayerService.AREA_REPLACE)
        self.assertTrue(ok)
        self.assertTrue(layer.commitChanges())

        self.assertEqual(self.areas(layer), [100.0])
        kept = next(f for f in layer.getFeatures() if f["ext_project_id"] == "5")
        self.assertTrue(kept.geometry().intersects(square(20)))
        self.assertEqual(self.areas(layer, "6"), [100.0])  # another project's area stays

    def test_add_part_joins_the_areas_into_one_feature(self) -> None:
        layer = self.layer()
        drawn_id = self.draw(layer)

        ok, _error = ProjectsLayerService.fold_existing_areas(
            layer, keep_feature_id=drawn_id, item_id="5", mode=ProjectsLayerService.AREA_ADD_PART)
        self.assertTrue(ok)
        self.assertTrue(layer.commitChanges())

        self.assertEqual(self.areas(layer), [200.0])
        kept = next(f for f in layer.getFeatures() if f["ext_project_id"] == "5")
        self.assertTrue(kept.geometry().isMultipart())

    def test_a_single_part_layer_cannot_take_a_second_part(self) -> None:
        layer = self.layer("Polygon")
        drawn_id = self.draw(layer)

        ok, _error = ProjectsLayerService.fold_existing_areas(
            layer, keep_feature_id=drawn_id, item_id="5", mode=ProjectsLayerService.AREA_ADD_PART)

        self.assertFalse(ok)
        layer.rollBack()

    def test_kavitro_gets_the_linked_feature_not_an_older_area(self) -> None:
        # Linking an existing feature: an older area of the same project comes first in layer order.
        layer = self.layer()
        linked = QgsFeature(layer.fields())
        linked.setAttributes(["5"])
        linked.setGeometry(square(20))
        layer.dataProvider().addFeatures([linked])
        linked_id = max(f.id() for f in layer.getFeatures() if f["ext_project_id"] == "5")

        payload = projects_controller_module.ProjectsFeatureMapController._geometry_payload_for_item(
            layer, {"id": "5"}, linked_id)

        expected = ProjectsLayerService.backend_geometry_payload_from_geometry(square(20), layer)
        self.assertEqual(payload, expected)

    def mode(self, layer, choice_index: int):
        controller = projects_controller_module.ProjectsFeatureMapController.__new__(
            projects_controller_module.ProjectsFeatureMapController)
        controller._lang = LANG
        self.ask_choice_modern.side_effect = lambda *_a, **kw: kw["buttons"][choice_index]
        return controller._existing_area_mode(layer, "5")

    def test_drawing_again_asks_replace_or_add(self) -> None:
        layer = self.layer()
        self.assertEqual(self.mode(layer, 0), ProjectsLayerService.AREA_REPLACE)
        self.assertEqual(self.mode(layer, 1), ProjectsLayerService.AREA_ADD_PART)
        self.assertIsNone(self.mode(layer, 2))
        self.assertEqual(len(self.ask_choice_modern.call_args.kwargs["buttons"]), 3)

    def test_a_single_part_layer_offers_only_replace(self) -> None:
        layer = self.layer("Polygon")
        self.assertEqual(self.mode(layer, 0), ProjectsLayerService.AREA_REPLACE)
        self.assertIsNone(self.mode(layer, 1))
        self.assertEqual(len(self.ask_choice_modern.call_args.kwargs["buttons"]), 2)

    def test_a_project_without_an_area_is_not_asked(self) -> None:
        layer = self.layer()
        controller = projects_controller_module.ProjectsFeatureMapController.__new__(
            projects_controller_module.ProjectsFeatureMapController)
        controller._lang = LANG
        self.assertEqual(controller._existing_area_mode(layer, "7"), "")
        self.ask_choice_modern.assert_not_called()


class EasementPreviewWidgetsTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        resolve = patch.object(ProjectBaseLayersService, "resolve_layer", return_value=None)
        resolve.start()
        self.addCleanup(resolve.stop)
        self.dialog = easement_preview_module.EasementPreviewDialog(item_data={"id": "1", "number": "S-1"})
        self.addCleanup(self.dialog.deleteLater)

    def test_the_status_line_is_in_the_dialog_and_shows_its_text(self) -> None:
        label = self.dialog._status_label
        self.assertGreaterEqual(self.dialog.layout().indexOf(label), 0)
        label.setText("Lõplik lõige loodud")
        self.assertFalse(label.isHidden())
        label.setText("")
        self.assertTrue(label.isHidden())

    def test_define_properties_stays_when_the_easement_has_links(self) -> None:
        self.dialog._connected_property_numbers = ["1:1"]
        with patch.object(preview_layers_module.PropertiesSelectors, "show_connected_properties_on_map",
                          return_value=None):
            self.dialog._run_connected_property_preview_flow()
        self.assertFalse(self.dialog._define_properties_button.isHidden())


class AsBuiltStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.layer = QgsVectorLayer(
            "LineString?crs=EPSG:3301&field=ext_job_id:string&field=ext_job_state:integer", "Teostus", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(["77", 1])
        feature.setGeometry(QgsGeometry.fromWkt("LINESTRING(0 0, 10 0)"))
        self.layer.dataProvider().addFeatures([feature])
        resolve = patch.object(AsBuiltLayerService, "resolve_main_layer", return_value=self.layer)
        resolve.start()
        self.addCleanup(resolve.stop)
        log = patch.object(PythonFailLogger, "log")
        self.log = log.start()
        self.addCleanup(log.stop)

    def state(self):
        return next(self.layer.getFeatures())["ext_job_state"]

    def test_the_new_status_reaches_the_asbuilt_feature(self) -> None:
        self.assertTrue(AsBuiltLayerService.sync_status_from_task("77", {"status": {"id": "5"}}))
        self.assertEqual(self.state(), 5)
        self.assertFalse(self.layer.isEditable())

    def test_a_layer_the_user_edits_is_left_alone(self) -> None:
        self.layer.startEditing()
        self.addCleanup(self.layer.rollBack)

        self.assertFalse(AsBuiltLayerService.sync_status_from_task("77", {"status": {"id": "5"}}))

        self.assertTrue(self.layer.isEditable())
        self.assertEqual(self.state(), 1)
        self.assertEqual(self.log.call_args.args[0], "asbuilt_status_sync_skipped_layer_editable")

    def test_an_item_not_on_the_map_changes_nothing(self) -> None:
        self.assertFalse(AsBuiltLayerService.sync_status_from_task("78", {"status": {"id": "5"}}))
        self.assertEqual(self.state(), 1)


class ConnectedPagesTest(unittest.TestCase):
    def test_every_module_reads_all_pages(self) -> None:
        sent = []

        def send_query(_query, variables=None, return_raw=False):
            sent.append(dict(variables))
            after = variables.get("after")
            nodes = [{"id": "c1"}, {"id": "c2"}] if after is None else [{"id": "c3"}]
            return {"data": {"property": {"contracts": {
                "pageInfo": {"hasNextPage": after is None, "endCursor": "cur1" if after is None else None},
                "edges": [{"node": node} for node in nodes],
            }}}}

        with patch.object(query_coordinator, "APIClient", return_value=Mock(send_query=send_query)):
            nodes = query_coordinator.PropertiesConnectedElementsQueries().fetch_module_data(Module.CONTRACT.value, "p1")

        self.assertEqual([node["id"] for node in nodes], ["c1", "c2", "c3"])
        self.assertEqual([v["after"] for v in sent], [None, "cur1"])
        self.assertTrue(all(v["orderBy"] and v["id"] == "p1" for v in sent))


if __name__ == "__main__":
    unittest.main()
