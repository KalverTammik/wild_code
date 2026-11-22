"""After a save that left some fields empty, the user is told once which fields, what was rejected and what to do.

A value that does not fit its field no longer fails the save (the field is written empty), so without this note
the user would not know that a width, a date or a yes/no field on the map is missing.
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

from qgis.core import NULL, QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt import asbuilt_feature_map_controller as asbuilt_module
from Kavitro_dev.modules.easements import easement_preview_dialog as easement_preview_module
from Kavitro_dev.modules.projects import project_preview_dialog as project_preview_module
from Kavitro_dev.modules.works import works_create_controller as works_module
from Kavitro_dev.utils.layers import field_value_problems as notice
from Kavitro_dev.utils.layers.module_layer_service_base import FieldValueProblem
from Kavitro_dev.utils.MapTools import module_feature_controllers as controllers_module
from Kavitro_dev.utils.MapTools.module_feature_controllers import (
    FeatureLinkResult,
    ModuleFeatureAttachController,
    ModuleFeatureDrawController,
)
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

ET = LanguageManager(language="et")
WIDTH = FieldValueProblem("laius", "Kaitsevööndi laius", "2 meetrit", "str", FieldValueProblem.NUMBER)
SCALE = FieldValueProblem("Mõõtkava", "Mõõtkava", "1:500", "str", FieldValueProblem.INTEGER)
TITLE = "Salvestatud, aga mõni väli jäi tühjaks"


def field(name: str, alias: str = "") -> QgsField:
    result = QgsField(name, QVariant.Double)
    result.setAlias(alias)
    return result


class DialogStubCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        # A real message window would wait for a click that never comes.
        for name in ("show_warning", "show_info", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log_exception", "log"):
            patcher = patch.object(PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def one_warning(self) -> tuple[str, str]:
        self.show_info.assert_not_called()
        self.show_warning.assert_called_once()
        return self.show_warning.call_args.args[:2]


class NoteTextTest(unittest.TestCase):
    def test_note_names_field_value_expected_kind_and_what_to_do(self) -> None:
        text = notice.field_value_problems_note([WIDTH, SCALE], ET)

        self.assertEqual(
            text.split("\n"),
            [
                "Need väljad jäid tühjaks, sest väärtus ei sobinud välja tüübiga:",
                "• Kaitsevööndi laius: „2 meetrit“ – peab olema arv",
                "• Mõõtkava: „1:500“ – peab olema täisarv",
                "Paranda väärtus kaardikihil objekti atribuutides või vormis ja salvesta uuesti.",
            ],
        )

    def test_every_expected_kind_has_its_own_word_in_both_languages(self) -> None:
        kinds = (
            FieldValueProblem.NUMBER,
            FieldValueProblem.INTEGER,
            FieldValueProblem.YES_NO,
            FieldValueProblem.DATE,
            FieldValueProblem.DATE_TIME,
        )
        for language, words in (
            ("et", ["arv", "täisarv", "jah/ei", "kuupäev", "kuupäev ja kellaaeg"]),
            ("en", ["a number", "a whole number", "yes/no", "a date", "a date and time"]),
        ):
            lang = LanguageManager(language=language)
            for kind, word in zip(kinds, words):
                with self.subTest(language=language, kind=kind):
                    text = notice.field_value_problems_note([FieldValueProblem("f", "F", "x", "str", kind)], lang)
                    self.assertTrue(text.split("\n")[1].endswith(" " + word), text)

    def test_field_label_is_the_alias_of_the_layer_field(self) -> None:
        problem = FieldValueProblem.for_field(field("kv_laius", "Kaitsevööndi laius"), "lai", FieldValueProblem.NUMBER)
        self.assertIn("• Kaitsevööndi laius: ", notice.field_value_problems_note([problem], ET))

    def test_no_problems_give_no_note_and_leave_the_message_alone(self) -> None:
        self.assertEqual(notice.field_value_problems_note([], ET), "")
        self.assertEqual(notice.with_field_value_problems("Salvestati.", [], ET), "Salvestati.")

    def test_same_field_and_value_written_twice_is_listed_once(self) -> None:
        text = notice.field_value_problems_note([WIDTH, WIDTH, SCALE], ET)
        self.assertEqual(text.count("Kaitsevööndi laius"), 1)

    def test_long_list_is_cut_with_a_count_of_the_rest(self) -> None:
        problems = [FieldValueProblem(f"f{i}", f"Väli {i}", "x", "str", FieldValueProblem.NUMBER) for i in range(13)]
        lines = notice.field_value_problems_note(problems, ET).split("\n")

        self.assertEqual(len(lines), 1 + notice.MAX_LISTED + 1)
        self.assertTrue(lines[notice.MAX_LISTED].endswith("(+3 veel)"), lines[notice.MAX_LISTED])

    def test_braces_in_a_rejected_value_are_shown_as_typed(self) -> None:
        problem = FieldValueProblem("f", "F", "{item_id}", "str", FieldValueProblem.NUMBER)
        self.assertIn("„{item_id}“", notice.with_field_value_problems("Salvestati.", [problem], ET))


class ShowSavedTest(unittest.TestCase):
    def test_without_problems_the_plain_success_message_is_shown(self) -> None:
        dialogs = Mock()
        notice.show_saved(dialogs, title="Õnnestus", message="Salvestati.", problems=[], lang=ET)

        dialogs.show_info.assert_called_once_with("Õnnestus", "Salvestati.")
        dialogs.show_warning.assert_not_called()

    def test_with_problems_one_warning_says_saved_and_lists_the_fields(self) -> None:
        dialogs = Mock()
        notice.show_saved(dialogs, title="Õnnestus", message="Salvestati.", problems=[WIDTH], lang=ET)

        dialogs.show_info.assert_not_called()
        title, text = dialogs.show_warning.call_args.args
        self.assertEqual(title, TITLE)
        self.assertEqual(text, "Salvestati.\n\n" + notice.field_value_problems_note([WIDTH], ET))


class DrawFlowNoticeTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301&field=kavitro_id:integer", "draw", "memory")
        self.assertTrue(self.layer.isValid())
        for target, name in ((controllers_module, "MapHelpers"), (controllers_module, "iface")):
            patcher = patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def draw(self, value, *, sync_result=(True, "")) -> None:
        def handler(layer, feature_id, _item):
            layer.changeAttributeValue(feature_id, 0, value)
            return FeatureLinkResult(True, "", lambda: sync_result, (WIDTH,))

        controller = ModuleFeatureDrawController()
        timers = []
        with patch.object(controllers_module.QTimer, "singleShot", side_effect=lambda _ms, fn: timers.append(fn)):
            self.assertTrue(
                controller.start_draw(
                    item_data={"id": "42"},
                    resolve_layer=lambda: self.layer,
                    on_feature_created=handler,
                    start_failed_message="start failed",
                    layer_save_failed_message="not saved {item_id}: {error}",
                    sync_failed_message="saved, Kavitro not updated {item_id}: {error}",
                    success_message="saved {item_id}",
                    title_error="E",
                    title_success="S",
                    log_module="easement",
                )
            )
            feature = QgsFeature(self.layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
            self.assertTrue(self.layer.addFeature(feature))
        timers[0]()

    def test_saved_feature_with_empty_fields_gives_one_warning_with_the_success_text(self) -> None:
        self.draw(7)

        title, text = self.one_warning()
        self.assertEqual(title, LanguageManager().translate(TranslationKeys.FIELD_VALUE_PROBLEMS_TITLE))
        self.assertEqual(text, notice.with_field_value_problems("saved 42", [WIDTH]))
        self.assertEqual(self.layer.featureCount(), 1)

    def test_failed_commit_saved_nothing_so_no_field_is_named(self) -> None:
        self.draw("not a number")

        title, text = self.one_warning()
        self.assertEqual(title, "E")
        self.assertTrue(text.startswith("not saved 42: "), text)
        self.assertNotIn(WIDTH.field_label, text)
        self.assertEqual(self.layer.featureCount(), 0)

    def test_failed_kavitro_update_still_names_the_empty_fields_of_the_saved_feature(self) -> None:
        self.draw(7, sync_result=(False, "Kavitro refused"))

        title, text = self.one_warning()
        self.assertEqual(title, "E")
        self.assertTrue(text.startswith("saved, Kavitro not updated 42: Kavitro refused\n\n"), text)
        self.assertIn(WIDTH.field_label, text)


class AttachFlowNoticeTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301", "attach", "memory")
        for name in ("MapHelpers", "iface", "DialogHelpers"):
            patcher = patch.object(controllers_module, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def attach(self, link: FeatureLinkResult) -> None:
        feature = Mock()
        feature.id.return_value = 3
        controller = ModuleFeatureAttachController()
        controller._layer = self.layer
        controller._item_id = "42"
        controller._find_feature_at_point = lambda _point, _layer: feature
        controller._attach_handler = lambda _layer, _fid, _item: link
        controller._handle_point_selected(
            object(),
            feature_not_found_message="none",
            save_failed_message="failed {item_id}: {error}",
            success_message="linked {item_id}",
            title_error="E",
            title_warning="W",
            title_success="S",
            log_module="easement",
        )

    def test_linked_feature_with_empty_fields_gives_one_warning(self) -> None:
        self.attach(FeatureLinkResult(True, "", None, (SCALE,)))

        title, text = self.one_warning()
        self.assertEqual(title, LanguageManager().translate(TranslationKeys.FIELD_VALUE_PROBLEMS_TITLE))
        self.assertEqual(text, notice.with_field_value_problems("linked 42", [SCALE]))

    def test_linked_feature_without_problems_keeps_the_success_message(self) -> None:
        self.attach(FeatureLinkResult(True, ""))

        self.show_info.assert_called_once_with("S", "linked 42")
        self.show_warning.assert_not_called()

    def test_failed_link_names_no_field(self) -> None:
        self.attach(FeatureLinkResult(False, "no layer", None, (SCALE,)))

        self.assertEqual(self.one_warning(), ("E", "failed 42: no layer"))

    def test_failed_kavitro_update_after_the_link_names_the_fields(self) -> None:
        self.attach(FeatureLinkResult(True, "", lambda: (False, "Kavitro refused"), (SCALE,)))

        title, text = self.one_warning()
        self.assertEqual(title, "E")
        self.assertEqual(text, notice.with_field_value_problems("failed 42: Kavitro refused", [SCALE]))


class AsBuiltHandlerCollectsProblemsTest(DialogStubCase):
    """The as-built handler hands the service a collector and returns what it found."""

    def test_rejected_form_value_reaches_the_link_result_and_the_save_goes_on(self) -> None:
        layer = QgsVectorLayer("LineString?crs=EPSG:3301&field=Mõõtkava:integer", "asbuilt", "memory")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(10, 0)]))
        layer.dataProvider().addFeatures([feature])
        feature_id = next(layer.getFeatures()).id()

        form = {"Mõõtkava": "1:500"}
        with patch.object(asbuilt_module.AsBuiltGeometryFormDialog, "prompt", return_value=form):
            link = asbuilt_module.AsBuiltFeatureMapController._attach_asbuilt_feature_and_sync_geometry(
                layer, feature_id, {"id": "77", "name": "Teostus"}
            )

        self.assertTrue(link.success, link.message)
        self.assertEqual([(p.field_name, p.raw_value, p.expected) for p in link.value_problems], [("Mõõtkava", "1:500", "integer")])
        self.assertEqual(next(layer.getFeatures())["Mõõtkava"], NULL)
        self.assertEqual(next(layer.getFeatures())["ext_job_id"], "77")


class WorksFlowNoticeTest(DialogStubCase):
    """Works saves go through the controller's own messages, not the shared map workflow."""

    def setUp(self) -> None:
        super().setUp()
        service = works_module.WorksLayerService
        self.insert_result = (True, "")

        def insert(**kwargs):
            kwargs["value_problems"].append(WIDTH)
            return self.insert_result

        self.insert = Mock(side_effect=insert)
        patches = (
            patch.object(works_module.APIModuleActions, "get_task_data", return_value={"id": "9", "name": "Töö"}),
            patch.object(works_module.APIModuleActions, "update_task_geometry", return_value=True),
            patch.object(service, "resolve_main_layer", return_value=object()),
            patch.object(service, "find_feature_by_task_id", return_value=None),
            patch.object(service, "find_property_feature_at_point", return_value=None),
            patch.object(service, "property_cadastral_number", return_value=""),
            patch.object(service, "insert_work_feature", self.insert),
            patch.object(works_module.WorksCreateController, "_clear_capture_tool"),
            patch.object(works_module.WorksCreateController, "_backend_point_geometry_payload", return_value={}),
            patch.object(works_module.WorksCreateController, "_responsible_display_name", return_value="Mari"),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.controller = works_module.WorksCreateController(lang_manager=ET)

    def add_existing(self) -> None:
        self.controller._existing_task_id = "9"
        self.controller._existing_task_payload = {}
        self.controller._handle_existing_task_point_selected(QgsPointXY(1, 1))

    def test_existing_task_added_with_empty_fields_gives_one_warning(self) -> None:
        self.add_existing()

        title, text = self.one_warning()
        self.assertEqual(title, TITLE)
        success = ET.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SUCCESS).format(task_id="9")
        self.assertEqual(text, notice.with_field_value_problems(success, [WIDTH], ET))

    def test_failed_map_save_names_no_field(self) -> None:
        self.insert_result = (False, "provider error")
        self.add_existing()

        _title, text = self.one_warning()
        self.assertNotIn(WIDTH.field_label, text)
        self.assertIn("provider error", text)


def collecting(result):
    """A service stand-in that rejects the width, as a real save into a number field would."""

    def save(**kwargs):
        kwargs["value_problems"].append(WIDTH)
        return result

    return Mock(side_effect=save)


class ProjectPreviewNoticeTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        self.dialog = project_preview_module.ProjectPreviewDialog.__new__(project_preview_module.ProjectPreviewDialog)
        self.dialog._lang = ET
        self.dialog._item_id = "5"
        self.dialog._item = {"id": "5"}
        self.dialog._preview_layer = Mock(return_value=object())
        service = project_preview_module.ProjectsLayerService
        self.start = lambda result: patch.object(service, "upsert_generated_area_feature", collecting(result))
        patcher = patch.object(service, "resolve_main_layer", return_value=Mock())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_saved_area_with_empty_fields_gives_one_warning(self) -> None:
        with self.start((True, "Projektid")):
            self.dialog._save_preview_to_main_layer()

        title, text = self.one_warning()
        self.assertEqual(title, TITLE)
        success = ET.translate(TranslationKeys.PROJECT_PREVIEW_SAVE_SUCCESS).format(item_id="5", layer="Projektid")
        self.assertEqual(text, notice.with_field_value_problems(success, [WIDTH], ET))

    def test_failed_save_names_no_field(self) -> None:
        with self.start((False, "provider error")):
            self.dialog._save_preview_to_main_layer()

        _title, text = self.one_warning()
        self.assertNotIn(WIDTH.field_label, text)


class EasementFinalCutNoticeTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        dialog = easement_preview_module.EasementPreviewDialog.__new__(easement_preview_module.EasementPreviewDialog)
        dialog._lang = ET
        dialog._item_id = "42"
        dialog._item = {"id": "42"}
        dialog._on_status_changed = None
        dialog._ensure_final_cut_layer = Mock(return_value=(object(), ""))
        dialog._easement_form_initial_values = Mock(return_value={})
        dialog._sync_saved_easement_geometry_to_backend = Mock(return_value=True)
        self.dialog = dialog
        module = easement_preview_module
        for target, name, value in (
            (module.EasementLayerService, "resolve_main_layer", Mock()),
            (module.EasementGeometryFormDialog, "prompt", {"Kaitsevööndi laius": "2 meetrit"}),
        ):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def save(self, result) -> list:
        problems: list = []
        with patch.object(easement_preview_module.EasementLayerService, "upsert_final_cut_feature", collecting(result)):
            self.ok, self.message = easement_preview_module.EasementPreviewDialog._save_final_cut_to_main_layer(
                self.dialog, [], problems
            )
        return problems

    def test_saved_area_hands_back_the_empty_fields(self) -> None:
        self.assertEqual(self.save((True, "Servituudid")), [WIDTH])
        self.assertTrue(self.ok)

    def test_failed_save_hands_back_nothing(self) -> None:
        self.assertEqual(self.save((False, "provider error")), [])
        self.assertFalse(self.ok)

    def test_saved_area_whose_kavitro_update_failed_still_hands_back_the_fields(self) -> None:
        self.dialog._sync_saved_easement_geometry_to_backend.return_value = False
        self.assertEqual(self.save((True, "Servituudid")), [WIDTH])
        self.assertFalse(self.ok)


class EasementPropertySaveNoticeTest(DialogStubCase):
    """The property save shows one message, with the final cut's empty fields in it."""

    def setUp(self) -> None:
        super().setUp()
        patcher = patch.object(easement_preview_module, "APIModuleActions")
        api = patcher.start()
        self.addCleanup(patcher.stop)
        api.resolve_property_map_by_cadastral.return_value = ({"1:1:1": "p1"}, [])
        api.get_easement_property_edges.return_value = [{"cadastralUnitNumber": "1:1:1"}]
        dialog = easement_preview_module.EasementPreviewDialog.__new__(easement_preview_module.EasementPreviewDialog)
        dialog._item_id = "42"
        dialog._lang = ET
        dialog._property_edges = [{"cadastralUnitNumber": "1:1:1"}]
        dialog._collect_property_payloads = Mock(return_value=([{"id": "", "cadastralUnitNumber": "1:1:1"}], []))
        dialog._set_property_edges = Mock()
        dialog._rerun_automation = Mock()
        self.dialog = dialog

    def save(self, layer_result, problems) -> None:
        def final_cut(_edges, value_problems):
            value_problems.extend(problems)
            return layer_result

        self.dialog._save_final_cut_to_main_layer = Mock(side_effect=final_cut)
        easement_preview_module.EasementPreviewDialog._save_property_details(self.dialog)

    def test_saved_with_empty_fields_gives_one_warning_naming_them(self) -> None:
        self.save((True, "Lõplik lõige salvestati."), [WIDTH])

        title, text = self.one_warning()
        self.assertEqual(title, TITLE)
        self.assertTrue(text.startswith("Servituudi kinnistuandmed salvestati."), text)
        self.assertTrue(text.endswith(notice.field_value_problems_note([WIDTH], ET)), text)

    def test_saved_without_problems_keeps_the_success_message(self) -> None:
        self.save((True, "Lõplik lõige salvestati."), [])

        self.show_info.assert_called_once()
        self.show_warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
