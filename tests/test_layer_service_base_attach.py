"""The shared layer edit of the module layer services: adding fields, finding a feature, attaching and saving."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils.layers.module_layer_service_base import AttachableLayerServiceBase, ModuleLayerServiceBase
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

POLYGON = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
ATTACHABLE = (AsBuiltLayerService, ProjectsLayerService, EasementLayerService)
ID_FIELD = {AsBuiltLayerService: "ext_job_id", ProjectsLayerService: "ext_project_id", EasementLayerService: "ext_easement_id"}
# The second key find_feature matches on, and the item key it comes from.
OTHER_KEY = {
    AsBuiltLayerService: ("ext_job_name", "item_name", "name"),
    ProjectsLayerService: ("ext_project_number", "item_number", "projectNumber"),
    EasementLayerService: ("ext_easement_number", "item_number", "number"),
}
MESSAGES = {
    AsBuiltLayerService: {
        "invalid": "Invalid As-built layer",
        "missing_id": "Missing backend As-built id",
        "not_found": "Selected As-built feature was not found",
        "start": "Could not start editing As-built layer",
        "update": "Could not update selected As-built feature",
        "commit": "Could not commit As-built layer changes",
        "verify": "Updated As-built feature could not be verified on the configured main layer",
        "fields_start": "Could not start editing As-built layer to add external fields",
        "fields_add": "Could not add external As-built fields to layer",
        "fields_commit": "Could not commit new As-built layer fields",
        "events": ("asbuilt_attach_existing_save_failed", "asbuilt_attach_existing_rollback_failed"),
        "field_events": ("asbuilt_layer_ensure_fields_failed", "asbuilt_layer_ensure_fields_rollback_failed"),
    },
    ProjectsLayerService: {
        "invalid": "Invalid Projects layer",
        "missing_id": "Missing backend project id",
        "not_found": "Selected project area feature was not found",
        "start": "Could not start editing Projects layer",
        "update": "Could not update selected Projects feature",
        "commit": "Could not commit Projects layer changes",
        "verify": "Updated project area feature could not be verified on the configured main layer",
        "fields_start": "Could not start editing Projects layer to add external fields",
        "fields_add": "Could not add external project fields to layer",
        "fields_commit": "Could not commit new Projects layer fields",
        "events": ("project_attach_existing_save_failed", "project_attach_rollback_failed"),
        "field_events": ("project_layer_ensure_fields_failed", "project_layer_ensure_fields_rollback_failed"),
    },
    EasementLayerService: {
        "invalid": "Invalid easement main layer",
        "missing_id": "Missing backend easement id",
        "not_found": "Selected easement feature was not found",
        "start": "Could not start editing easement layer",
        "update": "Could not update selected easement feature",
        "commit": "Could not commit easement layer changes",
        "verify": "Updated easement feature could not be verified on the configured main layer",
        "fields_start": "Could not start editing easement layer to add external fields",
        "fields_add": "Could not add external easement fields to layer",
        "fields_commit": "Could not commit new easement layer fields",
        "events": ("easement_attach_existing_save_failed", "easement_attach_rollback_failed"),
        "field_events": ("easement_layer_ensure_fields_failed", "easement_layer_ensure_fields_rollback_failed"),
    },
}
# The fields each service adds to its layer.
CUSTOM_FIELDS = {
    AsBuiltLayerService: (
        ("ext_job_id", "string"), ("ext_system", "string"), ("ext_job_name", "string"), ("ext_job_type", "string"),
        ("ext_job_state", "integer"), ("added_by", "string"), ("added_date", "datetime"), ("updated_by", "string"),
        ("update_date", "datetime"),
    ),
    ProjectsLayerService: (
        ("ext_project_id", "string"), ("ext_system", "string"), ("ext_project_name", "string"),
        ("ext_project_number", "string"), ("detailed", "string"), ("active", "boolean"), ("added_by", "string"),
        ("added_date", "datetime"), ("updated_by", "string"), ("update_date", "datetime"),
    ),
    EasementLayerService: (("ext_easement_id", "string"), ("ext_system", "string"), ("ext_easement_number", "string")),
}


def layer_for(service, rows=(), *, with_fields=True, extra_fields=""):
    fields = "&".join(f"field={name}:{kind}" for name, kind in CUSTOM_FIELDS[service]) if with_fields else ""
    uri = "&".join(part for part in ("Polygon?crs=EPSG:3301", fields, extra_fields) if part)
    layer = QgsVectorLayer(uri, "kiht", "memory")
    for attrs in rows:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(POLYGON))
        for key, value in attrs.items():
            feature.setAttribute(key, value)
        layer.dataProvider().addFeature(feature)
    return layer


def not_number_text(feature_id) -> str:
    return LanguageManager().translate(TranslationKeys.LAYER_FEATURE_ID_NOT_NUMBER).format(feature_id=feature_id)


def feature_ids(layer) -> list[int]:
    return [int(feature.id()) for feature in layer.getFeatures()]


def draw_feature(layer, attrs=None) -> int:
    """A feature drawn in the edit session: QGIS gives it a temporary negative id until the commit."""
    if not layer.isEditable():
        layer.startEditing()
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt(POLYGON))
    for key, value in (attrs or {}).items():
        feature.setAttribute(key, value)
    layer.addFeature(feature)
    return min(feature_ids(layer))


class _Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.events: list[str] = []
        log = patch.object(PythonFailLogger, "log", side_effect=lambda event, **_kw: self.events.append(event))
        log.start()
        self.addCleanup(log.stop)
        for service in (*ATTACHABLE, WorksLayerService):
            user = patch.object(service, "current_username", return_value="kasutaja")
            user.start()
            self.addCleanup(user.stop)
        mapping = patch.object(EasementLayerService, "load_status_mapping_rows", return_value=[])
        mapping.start()
        self.addCleanup(mapping.stop)


class EnsureCustomFieldsTest(_Case):
    def test_missing_fields_are_added_and_committed(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, with_fields=False)
                self.assertEqual(service._ensure_custom_fields(layer), (True, ""))
                self.assertEqual(sorted(f.name() for f in layer.fields()), sorted(name for name, _kind in CUSTOM_FIELDS[service]))
                self.assertFalse(layer.isEditable())

    def test_easement_text_fields_keep_their_length(self) -> None:
        layer = layer_for(EasementLayerService, with_fields=False)
        EasementLayerService._ensure_custom_fields(layer)
        lengths = {f.name(): f.length() for f in layer.fields()}
        self.assertEqual(lengths, {"ext_easement_id": 64, "ext_system": 32, "ext_easement_number": 64})

    def test_nothing_missing_opens_no_edit_session(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                with patch.object(QgsVectorLayer, "startEditing") as start:
                    self.assertEqual(service._ensure_custom_fields(layer_for(service)), (True, ""))
                start.assert_not_called()

    def test_in_the_users_edit_session_the_fields_go_to_the_provider(self) -> None:
        # As-built added them to the edit buffer, so the user's rollback or undo removed them again.
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, with_fields=False)
                layer.startEditing()
                self.assertEqual(service._ensure_custom_fields(layer), (True, ""))
                self.assertTrue(layer.isEditable())
                self.assertFalse(layer.isModified())
                layer.rollBack()
                self.assertEqual(sorted(f.name() for f in layer.fields()), sorted(name for name, _kind in CUSTOM_FIELDS[service]))
                self.assertEqual(len(layer.dataProvider().fields()), len(CUSTOM_FIELDS[service]))

    def test_works_adds_its_fields_to_the_provider_too(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        layer.startEditing()
        self.assertEqual(WorksLayerService._prepare_required_fields(layer), (True, ""))
        layer.rollBack()
        self.assertEqual(len(layer.fields()), len(WorksLayerService.CUSTOM_FIELDS()))

    def test_failures_return_their_message(self) -> None:
        for service in ATTACHABLE:
            texts = MESSAGES[service]
            with self.subTest(service=service.__name__, step="start"):
                with patch.object(QgsVectorLayer, "startEditing", return_value=False):
                    self.assertEqual(service._ensure_custom_fields(layer_for(service, with_fields=False)), (False, texts["fields_start"]))
            with self.subTest(service=service.__name__, step="commit"):
                layer = layer_for(service, with_fields=False)
                with patch.object(QgsVectorLayer, "commitChanges", return_value=False):
                    self.assertEqual(service._ensure_custom_fields(layer), (False, texts["fields_commit"]))
                self.assertFalse(layer.isEditable())
            with self.subTest(service=service.__name__, step="add"):
                layer = layer_for(service, with_fields=False)
                provider = type(layer.dataProvider())
                with patch.object(provider, "addAttributes", return_value=False):
                    self.assertEqual(service._ensure_custom_fields(layer), (False, texts["fields_add"]))
                self.assertFalse(layer.isEditable())
            with self.subTest(service=service.__name__, step="invalid"):
                self.assertEqual(service._ensure_custom_fields(None), (False, texts["invalid"]))

    def test_an_error_rolls_back_only_the_session_opened_here(self) -> None:
        for service in ATTACHABLE:
            for users_session in (False, True):
                with self.subTest(service=service.__name__, users_session=users_session):
                    self.events.clear()
                    layer = layer_for(service, with_fields=False)
                    if users_session:
                        layer.startEditing()
                    with patch.object(QgsVectorLayer, "updateFields", side_effect=RuntimeError("boom")):
                        self.assertEqual(service._ensure_custom_fields(layer), (False, "boom"))
                    self.assertEqual(layer.isEditable(), users_session)
                    self.assertEqual(self.events, [MESSAGES[service]["field_events"][0]])

    def test_works_required_fields_use_the_same_steps(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        self.assertEqual(WorksLayerService._prepare_required_fields(layer), (True, ""))
        self.assertEqual(len(layer.fields()), len(WorksLayerService.CUSTOM_FIELDS()))
        self.assertFalse(layer.isEditable())

        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        layer.startEditing()
        with patch.object(QgsVectorLayer, "updateFields", side_effect=RuntimeError("boom")):
            self.assertEqual(WorksLayerService._prepare_required_fields(layer), (False, "boom"))
        self.assertTrue(layer.isEditable())
        self.assertEqual(self.events, ["works_layer_prepare_required_fields_failed"])

        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        with patch.object(QgsVectorLayer, "commitChanges", return_value=False):
            self.assertEqual(WorksLayerService._prepare_required_fields(layer), (False, "Could not commit new Works layer fields"))
        self.assertFalse(layer.isEditable())


class FindFeatureTest(_Case):
    def find(self, service, layer, **keys):
        feature = service.find_feature(layer, **keys)
        return None if feature is None else int(feature.id())

    def test_id_matches_after_trimming_both_sides(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                id_field = ID_FIELD[service]
                layer = layer_for(service, [{id_field: "7"}, {id_field: " 8 "}])
                first, second = feature_ids(layer)
                self.assertEqual(self.find(service, layer, item_id=" 7 "), first)
                self.assertEqual(self.find(service, layer, item_id="8"), second)
                self.assertIsNone(self.find(service, layer, item_id="9"))
                self.assertIsNone(self.find(service, layer, item_id=""))

    def test_the_id_wins_over_an_earlier_feature_with_the_number_or_name(self) -> None:
        # The first feature in layer order won, so a feature with only the same number or name was linked instead.
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                other_field, keyword, _item_key = OTHER_KEY[service]
                rows = [{other_field: "N-1"}, {ID_FIELD[service]: "7"}, {ID_FIELD[service]: "7"}, {other_field: "N-1"}]
                layer = layer_for(service, rows)
                first, second, _third, _fourth = feature_ids(layer)
                self.assertEqual(self.find(service, layer, item_id="7", **{keyword: "N-1"}), second)
                self.assertEqual(self.find(service, layer, item_id="8", **{keyword: "N-1"}), first)
                self.assertEqual(self.find(service, layer, item_id="", **{keyword: "N-1"}), first)
                dup = layer_for(service, [{ID_FIELD[service]: "7"}, {ID_FIELD[service]: "7"}])
                self.assertEqual(self.find(service, dup, item_id="7"), feature_ids(dup)[0])

    def test_in_edit_mode_the_drawn_feature_comes_before_an_older_one_with_the_same_id(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{ID_FIELD[service]: "7"}])
                drawn = draw_feature(layer, {ID_FIELD[service]: "7"})
                self.assertEqual(self.find(service, layer, item_id="7"), drawn)

    def test_projects_match_number_then_name(self) -> None:
        layer = layer_for(ProjectsLayerService, [{"ext_project_name": "Nimi"}, {"ext_project_number": "N-1"}])
        name_feature, number_feature = feature_ids(layer)
        self.assertEqual(self.find(ProjectsLayerService, layer, item_id="", item_number="N-1"), number_feature)
        self.assertEqual(self.find(ProjectsLayerService, layer, item_id="", item_name="Nimi"), name_feature)
        # The number wins over an earlier feature with only the name.
        self.assertEqual(self.find(ProjectsLayerService, layer, item_id="9", item_number="N-1", item_name="Nimi"),
                         number_feature)

    def test_the_drawn_feature_with_the_id_wins_over_an_older_number_match(self) -> None:
        for service in (ProjectsLayerService, EasementLayerService):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{OTHER_KEY[service][0]: "N-1"}])
                drawn = draw_feature(layer, {ID_FIELD[service]: "7"})
                self.assertEqual(self.find(service, layer, item_id="7", item_number="N-1"), drawn)
                layer.rollBack()

    def test_easement_finds_the_id_in_a_legacy_field(self) -> None:
        layer = layer_for(EasementLayerService, with_fields=False, extra_fields="field=easement_id:string")
        layer.dataProvider().addFeature(QgsFeature(layer.fields()))
        feature = QgsFeature(layer.fields())
        feature.setAttribute("easement_id", "5")
        layer.dataProvider().addFeature(feature)
        self.assertEqual(self.find(EasementLayerService, layer, item_id="5"), feature_ids(layer)[1])

    def test_a_failing_read_is_logged_and_finds_nothing(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                self.events.clear()
                layer = layer_for(service, [{ID_FIELD[service]: "7"}])
                with patch.object(QgsVectorLayer, "getFeatures", side_effect=RuntimeError("deleted")):
                    self.assertIsNone(self.find(service, layer, item_id="7"))
                self.assertEqual(self.events, [f"{service.MODULE.value}_layer_find_feature_failed"])

    def test_works_task_id(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        for task_id in (5, 5, 6):
            feature = QgsFeature(layer.fields())
            feature.setAttribute("ext_job_id", task_id)
            layer.dataProvider().addFeature(feature)
        first = feature_ids(layer)[0]
        self.assertEqual(int(WorksLayerService.find_feature_by_task_id(layer, " 5 ").id()), first)
        self.assertIsNone(WorksLayerService.find_feature_by_task_id(layer, "9"))
        self.assertIsNone(WorksLayerService.find_feature_by_task_id(layer, ""))
        self.assertIsNone(WorksLayerService.find_feature_by_task_id(QgsVectorLayer("Point", "t", "memory"), "5"))
        with patch.object(QgsVectorLayer, "getFeatures", side_effect=RuntimeError("deleted")):
            self.assertIsNone(WorksLayerService.find_feature_by_task_id(layer, "5"))
        self.assertEqual(self.events, ["works_layer_find_feature_failed"])


class AttachTest(_Case):
    ITEM = {"name": "Nimi", "number": "N-1", "projectNumber": "N-1"}

    def attach(self, service, layer, feature_id, item_id="7", item=None):
        return service.attach_backend_item_to_feature(
            layer=layer, feature_id=feature_id, item_id=item_id, item_data=self.ITEM if item is None else item
        )

    @staticmethod
    def label(service, layer) -> str:
        return service._layer_target_label(layer)

    def test_link_is_saved_and_committed(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}])
                fid = feature_ids(layer)[0]
                self.assertEqual(self.attach(service, layer, fid), (True, self.label(service, layer)))
                self.assertFalse(layer.isEditable())
                saved = layer.getFeature(fid)
                self.assertEqual((saved[ID_FIELD[service]], saved["ext_system"]), ("7", "Kavitro"))

    def test_an_older_feature_with_the_same_link_does_not_fail_the_check(self) -> None:
        # The user got "Updated easement feature could not be verified" after the save had gone through.
        for service in ATTACHABLE:
            for older in ({"id": "7"}, {"other": "N-1"}):
                with self.subTest(service=service.__name__, older=older):
                    other_field = OTHER_KEY[service][0]
                    value = "Nimi" if other_field == "ext_job_name" else "N-1"
                    attrs = {ID_FIELD[service]: "7"} if "id" in older else {other_field: value}
                    layer = layer_for(service, [attrs, {}])
                    fid = feature_ids(layer)[1]
                    self.assertEqual(self.attach(service, layer, fid), (True, self.label(service, layer)))
                    self.assertEqual(layer.getFeature(fid)[ID_FIELD[service]], "7")

    def test_drawn_feature_stays_in_the_edit_session(self) -> None:
        for service in ATTACHABLE:
            for with_older in (False, True):
                with self.subTest(service=service.__name__, with_older=with_older):
                    layer = layer_for(service, [{ID_FIELD[service]: "7"}] if with_older else [])
                    fid = draw_feature(layer)
                    self.assertLess(fid, 0)
                    self.assertEqual(self.attach(service, layer, fid), (True, self.label(service, layer)))
                    self.assertTrue(layer.isEditable())
                    self.assertEqual(layer.getFeature(fid)[ID_FIELD[service]], "7")

    def test_a_link_the_layer_could_not_store_fails_the_check(self) -> None:
        # The id field holds whole numbers, so the text id is written empty and the link is not on the feature.
        for service in (AsBuiltLayerService, EasementLayerService):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, with_fields=False, extra_fields=f"field={ID_FIELD[service]}:integer")
                service._ensure_custom_fields(layer)
                layer.dataProvider().addFeature(QgsFeature(layer.fields()))
                fid = feature_ids(layer)[0]
                self.assertEqual(self.attach(service, layer, fid, item_id="abc"), (False, MESSAGES[service]["verify"]))

    def test_projects_check_needs_the_id_on_the_saved_feature(self) -> None:
        # Projects accepted any feature with the same number or name, so a link the layer dropped looked saved.
        layer = layer_for(ProjectsLayerService, with_fields=False, extra_fields="field=ext_project_id:integer")
        ProjectsLayerService._ensure_custom_fields(layer)
        layer.dataProvider().addFeature(QgsFeature(layer.fields()))
        fid = feature_ids(layer)[0]
        self.assertEqual(self.attach(ProjectsLayerService, layer, fid, item_id="abc"),
                         (False, MESSAGES[ProjectsLayerService]["verify"]))

    def test_failed_steps_return_their_message_and_leave_nothing_open(self) -> None:
        for service in ATTACHABLE:
            texts = MESSAGES[service]
            for step, method, kwargs, expected in (
                ("start", "startEditing", {"return_value": False}, texts["start"]),
                ("update", "updateFeature", {"return_value": False}, texts["update"]),
                ("commit", "commitChanges", {"return_value": False}, texts["commit"]),
                ("error", "updateFeature", {"side_effect": RuntimeError("boom")}, "boom"),
            ):
                with self.subTest(service=service.__name__, step=step):
                    self.events.clear()
                    layer = layer_for(service, [{}])
                    fid = feature_ids(layer)[0]
                    with patch.object(QgsVectorLayer, method, **kwargs):
                        self.assertEqual(self.attach(service, layer, fid), (False, expected))
                    self.assertFalse(layer.isEditable())
                    self.assertTrue(layer.getFeature(fid)[ID_FIELD[service]] in (None, "") or
                                    QVariant(layer.getFeature(fid)[ID_FIELD[service]]).isNull())
                    self.assertEqual(self.events, [texts["events"][0]] if step == "error" else [])

    def test_an_error_keeps_the_users_own_edit_session(self) -> None:
        # Easement rolled the whole session back, dropping the user's other unsaved edits.
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}, {}])
                first, second = feature_ids(layer)
                layer.startEditing()
                layer.changeGeometry(second, QgsGeometry.fromWkt("POLYGON((0 0, 5 0, 5 5, 0 0))"))
                with patch.object(QgsVectorLayer, "updateFeature", side_effect=RuntimeError("boom")):
                    self.assertEqual(self.attach(service, layer, first), (False, "boom"))
                self.assertTrue(layer.isEditable())
                self.assertTrue(layer.isModified())

    def test_failed_rollback_is_logged_after_the_error(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                self.events.clear()
                layer = layer_for(service, [{}])
                fid = feature_ids(layer)[0]
                with patch.object(QgsVectorLayer, "updateFeature", side_effect=RuntimeError("boom")), patch.object(
                    QgsVectorLayer, "rollBack", side_effect=RuntimeError("rollback boom")
                ):
                    self.assertEqual(self.attach(service, layer, fid), (False, "boom"))
                self.assertEqual(self.events, [MESSAGES[service]["events"][1], MESSAGES[service]["events"][0]])
                layer.rollBack()

    def test_inputs_that_stop_before_the_edit(self) -> None:
        for service in ATTACHABLE:
            texts = MESSAGES[service]
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}])
                self.assertEqual(self.attach(service, layer, 999), (False, texts["not_found"]))
                self.assertEqual(self.attach(service, layer, feature_ids(layer)[0], item_id=" "), (False, texts["missing_id"]))
                self.assertEqual(self.attach(service, QgsVectorLayer("Polygon", "x", "nope"), 1), (False, texts["invalid"]))
                self.assertEqual(self.attach(service, None, 1), (False, texts["invalid"]))

    def test_a_feature_id_that_is_not_a_number_is_a_normal_failure(self) -> None:
        # int("abc") raised ValueError out of the service into the map click handler.
        for service in ATTACHABLE:
            for bad_id in ("abc", None, "1.5"):
                with self.subTest(service=service.__name__, feature_id=bad_id):
                    self.events.clear()
                    layer = layer_for(service, [{}])
                    self.assertEqual(self.attach(service, layer, bad_id), (False, not_number_text(bad_id)))
                    self.assertEqual(self.events, [f"{service.MODULE.value}_feature_id_not_number"])
                    self.assertFalse(layer.isEditable())

    def test_a_layer_without_the_fields_gets_them_first(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}], with_fields=False)
                fid = feature_ids(layer)[0]
                self.assertTrue(self.attach(service, layer, fid)[0])
                self.assertEqual(layer.getFeature(fid)[ID_FIELD[service]], "7")

    def test_fields_that_cannot_be_added_stop_the_attach(self) -> None:
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}], with_fields=False)
                with patch.object(QgsVectorLayer, "startEditing", return_value=False):
                    self.assertEqual(self.attach(service, layer, feature_ids(layer)[0]), (False, MESSAGES[service]["fields_start"]))

    def test_who_added_the_feature_is_kept_on_a_second_link(self) -> None:
        for service, by_field in ((AsBuiltLayerService, "added_by"), (ProjectsLayerService, "added_by")):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{by_field: "esimene"}, {}])
                kept, filled = feature_ids(layer)
                self.assertTrue(self.attach(service, layer, kept)[0])
                self.assertTrue(self.attach(service, layer, filled, item_id="8")[0])
                self.assertEqual(layer.getFeature(kept)[by_field], "esimene")
                self.assertEqual(layer.getFeature(filled)[by_field], "kasutaja")
                self.assertFalse(QVariant(layer.getFeature(filled)["added_date"]).isNull())

    def test_every_attachable_module_reloads_the_layer_after_a_save(self) -> None:
        # As-built only repainted, so the layer extent and the canvas stayed as before the save.
        for service in ATTACHABLE:
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}])
                with patch.object(QgsVectorLayer, "reload") as reload, patch.object(
                    QgsVectorLayer, "updateExtents"
                ) as extents:
                    self.assertTrue(self.attach(service, layer, feature_ids(layer)[0])[0])
                reload.assert_called_once_with()
                extents.assert_called_once_with()

    def test_works_still_only_repaints(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long", "tood", "memory")
        with patch.object(QgsVectorLayer, "reload") as reload:
            self.assertTrue(WorksLayerService.insert_work_feature(layer=layer, point=QgsPointXY(1, 1), task_id="5",
                                                                  title="T")[0])
        reload.assert_not_called()


class WorksWriteTest(_Case):
    @staticmethod
    def layer(rows=()):
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long&field=ext_job_name:string", "tood", "memory")
        for task_id in rows:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
            feature.setAttribute("ext_job_id", task_id)
            layer.dataProvider().addFeature(feature)
        return layer

    def insert(self, layer):
        return WorksLayerService.insert_work_feature(layer=layer, point=QgsPointXY(1, 1), task_id="5", title="Töö")

    def update(self, layer, feature_id):
        return WorksLayerService.update_existing_work_feature(layer=layer, feature_id=feature_id, task_id="5", title="Töö")

    def test_insert_and_update_save_the_values(self) -> None:
        layer = self.layer()
        self.assertEqual(self.insert(layer), (True, ""))
        self.assertEqual([(f["ext_job_id"], f["ext_job_name"]) for f in layer.getFeatures()], [(5, "Töö")])
        self.assertFalse(layer.isEditable())

        layer = self.layer([1])
        fid = feature_ids(layer)[0]
        self.assertEqual(self.update(layer, fid), (True, ""))
        self.assertEqual((layer.getFeature(fid)["ext_job_id"], layer.getFeature(fid)["ext_job_name"]), (5, "Töö"))
        self.assertEqual(self.update(layer, 99), (False, "Feature not found"))
        self.assertEqual(self.insert(QgsVectorLayer("Point?crs=EPSG:3301", "t", "memory")), (False, "Task id field missing"))

    def test_failed_steps_return_their_message(self) -> None:
        for name, run, method, kwargs, expected, events in (
            ("insert commit", lambda layer: self.insert(layer), "commitChanges", {"return_value": False},
             "Could not commit works layer changes", []),
            ("insert add", lambda layer: self.insert(layer), "addFeature", {"return_value": False},
             "Could not add feature to works layer", []),
            ("insert error", lambda layer: self.insert(layer), "addFeature", {"side_effect": RuntimeError("boom")},
             "boom", ["works_layer_insert_failed"]),
            ("update commit", lambda layer: self.update(layer, feature_ids(layer)[0]), "commitChanges",
             {"return_value": False}, "Could not commit works layer changes", []),
            ("update error", lambda layer: self.update(layer, feature_ids(layer)[0]), "updateFeature",
             {"side_effect": RuntimeError("boom")}, "boom", ["works_layer_update_existing_failed"]),
            ("start", lambda layer: self.insert(layer), "startEditing", {"return_value": False},
             "Could not start editing works layer", []),
        ):
            with self.subTest(step=name):
                self.events.clear()
                layer = self.layer([1])
                with patch.object(QgsVectorLayer, method, **kwargs):
                    self.assertEqual(run(layer), (False, expected))
                self.assertFalse(layer.isEditable())
                self.assertEqual(self.events, events)

    def test_an_insert_error_keeps_the_users_own_edit_session(self) -> None:
        layer = self.layer([1])
        layer.startEditing()
        layer.changeAttributeValue(feature_ids(layer)[0], 1, "muudetud")
        with patch.object(QgsVectorLayer, "addFeature", side_effect=RuntimeError("boom")):
            self.assertEqual(self.insert(layer), (False, "boom"))
        self.assertTrue(layer.isEditable())
        self.assertTrue(layer.isModified())


class UpsertTest(_Case):
    @staticmethod
    def source():
        layer = QgsVectorLayer("Polygon?crs=EPSG:3301", "eelvaade", "memory")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(POLYGON))
        layer.dataProvider().addFeature(feature)
        return layer

    def upsert(self, service, layer, item_id="7", item=None):
        if service is ProjectsLayerService:
            return service.upsert_generated_area_feature(
                layer=layer, preview_layer=self.source(), item_id=item_id, item_data=item or {"name": "Nimi"})
        return service.upsert_final_cut_feature(
            layer=layer, final_layer=self.source(), item_id=item_id, item_data=item or {"number": "N-1"})

    def test_new_and_existing_feature(self) -> None:
        for service in (ProjectsLayerService, EasementLayerService):
            for rows in ([], [{ID_FIELD[service]: "7"}]):
                with self.subTest(service=service.__name__, existing=bool(rows)):
                    layer = layer_for(service, rows)
                    self.assertEqual(self.upsert(service, layer), (True, service._layer_target_label(layer)))
                    self.assertEqual(layer.featureCount(), 1)
                    self.assertFalse(layer.isEditable())

    def test_an_error_keeps_the_users_own_edit_session(self) -> None:
        for service, event in ((ProjectsLayerService, "project_generated_area_save_failed"),
                               (EasementLayerService, "easement_layer_save_failed")):
            with self.subTest(service=service.__name__):
                self.events.clear()
                layer = layer_for(service, [{}])
                layer.startEditing()
                layer.changeGeometry(feature_ids(layer)[0], QgsGeometry.fromWkt("POLYGON((0 0, 5 0, 5 5, 0 0))"))
                with patch.object(QgsVectorLayer, "addFeature", side_effect=RuntimeError("boom")):
                    self.assertEqual(self.upsert(service, layer), (False, "boom"))
                self.assertTrue(layer.isEditable())
                self.assertTrue(layer.isModified())
                self.assertEqual(self.events, [event])

    def test_a_saved_feature_without_the_id_fails_the_check(self) -> None:
        # The id field holds whole numbers, so the text id is written empty. The old check found the saved feature by
        # its number or name and reported success.
        for service, verify in (
            (ProjectsLayerService, "Saved project area feature could not be verified on the configured main layer"),
            (EasementLayerService, "Saved easement feature could not be verified on the configured main layer"),
        ):
            for existing in (False, True):
                with self.subTest(service=service.__name__, existing=existing):
                    layer = layer_for(service, with_fields=False, extra_fields=f"field={ID_FIELD[service]}:integer")
                    service._ensure_custom_fields(layer)
                    if existing:
                        older = QgsFeature(layer.fields())
                        older.setAttribute(OTHER_KEY[service][0], "N-1")
                        layer.dataProvider().addFeature(older)
                    item = {"name": "Nimi", "projectNumber": "N-1", "number": "N-1"}
                    self.assertEqual(self.upsert(service, layer, item_id="abc", item=item), (False, verify))
                    self.assertEqual(layer.featureCount(), 1)

    def test_an_older_feature_with_the_same_id_does_not_count_for_the_new_one(self) -> None:
        # The saved feature is checked by the id the commit gave it, not by searching the layer for the id.
        for service in (ProjectsLayerService, EasementLayerService):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{ID_FIELD[service]: "7"}])
                layer.dataProvider().addFeature(QgsFeature(layer.fields()))
                with patch.object(service, "_written_feature_id", return_value=feature_ids(layer)[1]):
                    self.assertFalse(self.upsert(service, layer, item_id="8")[0])

    def test_a_new_feature_gets_its_id_from_the_commit(self) -> None:
        for service in (ProjectsLayerService, EasementLayerService):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{ID_FIELD[service]: "7"}])
                with patch.object(QgsVectorLayer, "commitChanges", return_value=True):
                    # A commit that reports no added feature leaves nothing to check.
                    self.assertFalse(self.upsert(service, layer, item_id="8")[0])
                layer.rollBack()
                self.assertEqual(self.upsert(service, layer, item_id="8"), (True, service._layer_target_label(layer)))
                self.assertEqual(sorted(f[ID_FIELD[service]] for f in layer.getFeatures()), ["7", "8"])

    def test_a_new_feature_in_the_users_session_is_checked_by_its_temporary_id(self) -> None:
        for service in (ProjectsLayerService, EasementLayerService):
            with self.subTest(service=service.__name__):
                layer = layer_for(service, [{}])
                layer.startEditing()
                self.assertEqual(self.upsert(service, layer), (True, service._layer_target_label(layer)))
                self.assertTrue(layer.isEditable())
                self.assertEqual([f[ID_FIELD[service]] for f in layer.getFeatures() if f.id() < 0], ["7"])
                layer.rollBack()

    def test_failed_add_and_commit(self) -> None:
        for service, add_text in ((ProjectsLayerService, "Could not add project area feature"),
                                  (EasementLayerService, "Could not add easement feature")):
            with self.subTest(service=service.__name__):
                with patch.object(QgsVectorLayer, "addFeature", return_value=False):
                    self.assertEqual(self.upsert(service, layer_for(service)), (False, add_text))
                commit = "Could not commit Projects layer changes" if service is ProjectsLayerService else "Could not commit easement layer changes"
                with patch.object(QgsVectorLayer, "commitChanges", return_value=False):
                    self.assertEqual(self.upsert(service, layer_for(service)), (False, commit))


class EasementDeleteArchiveTest(_Case):
    @staticmethod
    def layer():
        return layer_for(EasementLayerService, [{}, {}], extra_fields="field=Staatus:string")

    @staticmethod
    def delete(layer, feature_id):
        return EasementLayerService.delete_feature_by_id(layer=layer, feature_id=feature_id)

    @staticmethod
    def archive(layer, feature_id):
        return EasementLayerService.archive_feature_by_id(layer=layer, feature_id=feature_id)

    def steps(self):
        return (("delete", self.delete, "deleteFeature", "easement_delete_feature_failed"),
                ("archive", self.archive, "updateFeature", "easement_archive_feature_failed"))

    def test_both_work(self) -> None:
        layer = self.layer()
        first, second = feature_ids(layer)
        self.assertEqual(self.archive(layer, first), (True, EasementLayerService._layer_target_label(layer)))
        self.assertEqual(layer.getFeature(first)["Staatus"], "(puudub)")
        self.assertEqual(self.delete(layer, second), (True, EasementLayerService._layer_target_label(layer)))
        self.assertEqual(feature_ids(layer), [first])
        self.assertFalse(layer.isEditable())

    def test_an_error_keeps_the_users_own_edit_session(self) -> None:
        # The whole session was rolled back, dropping the user's other unsaved edits.
        for name, run, method, event in self.steps():
            with self.subTest(step=name):
                self.events.clear()
                layer = self.layer()
                first, second = feature_ids(layer)
                layer.startEditing()
                layer.changeGeometry(second, QgsGeometry.fromWkt("POLYGON((0 0, 5 0, 5 5, 0 0))"))
                with patch.object(QgsVectorLayer, method, side_effect=RuntimeError("boom")):
                    self.assertEqual(run(layer, first), (False, "boom"))
                self.assertTrue(layer.isEditable())
                self.assertTrue(layer.isModified())
                self.assertEqual(self.events, [event])
                layer.rollBack()

    def test_an_error_rolls_back_the_session_opened_here(self) -> None:
        for name, run, method, _event in self.steps():
            with self.subTest(step=name):
                layer = self.layer()
                with patch.object(QgsVectorLayer, method, side_effect=RuntimeError("boom")):
                    self.assertEqual(run(layer, feature_ids(layer)[0]), (False, "boom"))
                self.assertFalse(layer.isEditable())
                self.assertEqual(len(feature_ids(layer)), 2)

    def test_a_feature_id_that_is_not_a_number_is_a_normal_failure(self) -> None:
        # int("abc") raised ValueError: archive straight out of its first read, delete out of its own error log.
        for name, run, _method, _event in self.steps():
            for bad_id in ("abc", None):
                with self.subTest(step=name, feature_id=bad_id):
                    self.events.clear()
                    layer = self.layer()
                    self.assertEqual(run(layer, bad_id), (False, not_number_text(bad_id)))
                    self.assertEqual(self.events, ["easement_feature_id_not_number"])
                    self.assertFalse(layer.isEditable())
                    self.assertEqual(len(feature_ids(layer)), 2)


class OneOwnerTest(unittest.TestCase):
    def test_the_edit_steps_live_only_on_the_base(self) -> None:
        shared = ("attach_backend_item_to_feature", "_ensure_custom_fields", "_write_feature", "_add_missing_fields",
                  "_find_first_feature", "_rollback_own_edit", "_fill_added_fields_if_empty", "_refresh_saved_layer")
        for service in (*ATTACHABLE, WorksLayerService):
            for name in shared:
                with self.subTest(service=service.__name__, name=name):
                    self.assertNotIn(name, vars(service))
        self.assertIn("attach_backend_item_to_feature", vars(AttachableLayerServiceBase))
        self.assertIn("_write_feature", vars(ModuleLayerServiceBase))


if __name__ == "__main__":
    unittest.main()
