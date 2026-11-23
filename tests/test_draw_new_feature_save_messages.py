"""Drawing a new map feature for a Kavitro item tells apart "nothing was saved" from "saved, but Kavitro was not updated".

The old flow sent the geometry to Kavitro before the layer commit and then showed "the feature was created, but
linking failed" for every failure, also when the commit failed and the drawn feature was thrown away.
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

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt import asbuilt_feature_map_controller as asbuilt_module
from Kavitro_dev.modules.easements import easement_attach_existing_controller as easement_module
from Kavitro_dev.modules.projects import projects_feature_map_controller as projects_module
from Kavitro_dev.ui.map_tools import module_feature_controllers as controllers_module
from Kavitro_dev.ui.map_tools.module_feature_controllers import (
    FeatureLinkResult,
    ModuleFeatureAttachController,
    ModuleFeatureDrawController,
)
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

LAYER_SAVE_FAILED = "not saved {item_id}: {error}"
SYNC_FAILED = "saved, Kavitro not updated {item_id}: {error}"  # the old texts still carry {error}
SUCCESS = "saved {item_id}"


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
        log = patch.object(PythonFailLogger, "log_exception")
        self.log = log.start()
        self.addCleanup(log.stop)


class DrawFlowTest(DialogStubCase):
    def setUp(self) -> None:
        super().setUp()
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301&field=kavitro_id:integer", "draw", "memory")
        self.assertTrue(self.layer.isValid())
        self.sync = Mock(side_effect=self._record_sync)
        self.sync_saw = None
        self.sync_result = (True, "")
        for target, name in ((controllers_module, "MapHelpers"), (controllers_module, "iface")):
            patcher = patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _record_sync(self):
        self.sync_saw = (self.layer.isEditable(), self.layer.featureCount())
        return self.sync_result

    def handler(self, value, *, link_ok=True):
        def link(layer, feature_id, _item):
            layer.changeAttributeValue(feature_id, 0, value)
            return FeatureLinkResult(link_ok, "" if link_ok else "form cancelled", self.sync)

        return link

    def draw(self, handler) -> None:
        controller = ModuleFeatureDrawController()
        timers = []
        with patch.object(controllers_module.QTimer, "singleShot", side_effect=lambda _ms, fn: timers.append(fn)):
            started = controller.start_draw(
                item_data={"id": "42"},
                resolve_layer=lambda: self.layer,
                on_feature_created=handler,
                start_failed_message="start failed",
                layer_save_failed_message=LAYER_SAVE_FAILED,
                sync_failed_message=SYNC_FAILED,
                success_message=SUCCESS,
                title_error="E",
                title_success="S",
                log_module="easement",
            )
            self.assertTrue(started)
            feature = QgsFeature(self.layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
            self.assertTrue(self.layer.addFeature(feature))
        self.assertEqual(len(timers), 1)
        timers[0]()

    def warned(self) -> str:
        self.show_warning.assert_called_once()
        self.show_info.assert_not_called()
        title, text = self.show_warning.call_args.args
        self.assertEqual(title, "E")
        return text

    def retry_offered(self) -> str:
        """The text of the one "try again" question; no warning or success follows when it is declined."""
        self.show_warning.assert_not_called()
        self.show_info.assert_not_called()
        self.ask_choice_modern.assert_called_once()
        title, text = self.ask_choice_modern.call_args.args[:2]
        self.assertEqual(title, "E")
        return text

    def test_the_commit_does_not_open_the_form_a_second_time(self) -> None:
        # QGIS emits featureAdded again on commit (temporary id -> permanent id); the user got the form twice
        # and the second run failed with "could not be verified".
        calls = []
        timers = []

        def sync_with_wait_window():
            # The Kavitro request opens a wait window whose event loop runs queued timers.
            while timers:
                timers.pop(0)()
            return True, ""

        self.sync = Mock(side_effect=sync_with_wait_window)
        link = self.handler(7)

        def counting_handler(layer, feature_id, item):
            calls.append(feature_id)
            return link(layer, feature_id, item)

        controller = ModuleFeatureDrawController()
        with patch.object(controllers_module.QTimer, "singleShot", side_effect=lambda _ms, fn: timers.append(fn)):
            controller.start_draw(
                item_data={"id": "42"},
                resolve_layer=lambda: self.layer,
                on_feature_created=counting_handler,
                start_failed_message="start failed",
                layer_save_failed_message=LAYER_SAVE_FAILED,
                sync_failed_message=SYNC_FAILED,
                success_message=SUCCESS,
                title_error="E",
                title_success="S",
                log_module="easement",
            )
            feature = QgsFeature(self.layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
            self.assertTrue(self.layer.addFeature(feature))
            while timers:
                timers.pop(0)()

        self.assertEqual(len(calls), 1)
        self.assertEqual(self.layer.featureCount(), 1)
        self.show_info.assert_called_once()
        self.show_warning.assert_not_called()

    def test_failed_commit_says_nothing_was_saved_and_leaves_no_feature(self) -> None:
        # The provider refuses the value, as in the user's "1 feature(s) not added. Provider errors: ..." case.
        self.draw(self.handler("not a number"))

        text = self.warned()
        self.assertTrue(text.startswith("not saved 42: "), text)
        self.assertIn("not added", text)
        self.assertEqual(self.layer.featureCount(), 0)
        self.assertFalse(self.layer.isEditable())
        self.sync.assert_not_called()

    def test_failed_link_says_nothing_was_saved_and_leaves_no_feature(self) -> None:
        self.draw(self.handler(7, link_ok=False))

        self.assertEqual(self.warned(), "not saved 42: form cancelled")
        self.assertEqual(self.layer.featureCount(), 0)
        self.assertFalse(self.layer.isEditable())
        self.sync.assert_not_called()

    def test_failed_kavitro_update_says_the_feature_is_saved(self) -> None:
        self.sync_result = (False, "Kavitro refused")
        self.draw(self.handler(7))

        self.assertTrue(self.retry_offered().startswith("saved, Kavitro not updated 42: Kavitro refused\n\n"))
        self.assertEqual(self.layer.featureCount(), 1)
        self.assertFalse(self.layer.isEditable())
        self.assertEqual(next(self.layer.getFeatures())["kavitro_id"], 7)

    def test_kavitro_update_that_raises_is_logged_and_reported_as_not_updated(self) -> None:
        self.sync.side_effect = RuntimeError("network gone")
        self.draw(self.handler(7))

        self.assertTrue(self.retry_offered().startswith("saved, Kavitro not updated 42: network gone\n\n"))
        self.assertEqual(self.layer.featureCount(), 1)
        self.assertEqual([c.kwargs["event"] for c in self.log.call_args_list], ["module_feature_draw_kavitro_sync_failed"])

    def test_a_failed_kavitro_update_can_be_sent_again(self) -> None:
        # Found 2026-11-23: the layer is saved first, and a failed Kavitro update only warned. Now it can be retried.
        results = [(False, "Kavitro refused"), (True, "")]
        self.sync.side_effect = lambda: results.pop(0)
        self.ask_choice_modern.side_effect = lambda *_args, **kwargs: kwargs["buttons"][0]  # "Try again"

        self.draw(self.handler(7))

        self.assertEqual(self.sync.call_count, 2)
        self.ask_choice_modern.assert_called_once()
        self.show_info.assert_called_once_with("S", "saved 42")
        self.show_warning.assert_not_called()

    def test_kavitro_is_updated_only_after_the_layer_commit(self) -> None:
        self.draw(self.handler(7))

        self.show_info.assert_called_once_with("S", "saved 42")
        self.show_warning.assert_not_called()
        self.assertEqual(self.sync_saw, (False, 1))
        self.log.assert_not_called()

    def start_only(self, handler):
        controller = ModuleFeatureDrawController()
        started = controller.start_draw(
            item_data={"id": "42"}, resolve_layer=lambda: self.layer, on_feature_created=handler,
            start_failed_message="start failed", layer_save_failed_message=LAYER_SAVE_FAILED,
            sync_failed_message=SYNC_FAILED, success_message=SUCCESS, title_error="E", title_success="S",
            log_module="project",
        )
        self.assertTrue(started)
        self.assertTrue(self.layer.isEditable())
        canvas = controllers_module.iface.mapCanvas.return_value
        tool_changed = canvas.mapToolSet.connect.call_args.args[0]
        return controller, canvas, tool_changed

    def add_point(self):
        feature = QgsFeature(self.layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(3, 4)))
        self.assertTrue(self.layer.addFeature(feature))

    def test_another_map_tool_ends_the_draw_and_a_later_feature_is_not_linked(self) -> None:
        handler = Mock()
        controller, canvas, tool_changed = self.start_only(handler)

        tool_changed(object(), canvas.mapTool.return_value)

        self.assertFalse(self.layer.isEditable())  # the empty session this draw opened is closed
        canvas.mapToolSet.disconnect.assert_called_once_with(tool_changed)
        self.assertTrue(self.layer.startEditing())
        with patch.object(controllers_module.QTimer, "singleShot") as later:
            self.add_point()
        later.assert_not_called()
        handler.assert_not_called()
        self.layer.rollBack()

    def test_the_draw_tool_itself_keeps_the_draw_going(self) -> None:
        controller, canvas, tool_changed = self.start_only(Mock())

        tool_changed(canvas.mapTool.return_value, None)

        self.assertTrue(self.layer.isEditable())
        with patch.object(controllers_module.QTimer, "singleShot") as later:
            self.add_point()
        later.assert_called_once()
        controller.cancel()
        self.layer.rollBack()

    def test_stopping_the_edit_session_ends_the_draw(self) -> None:
        handler = Mock()
        self.start_only(handler)

        self.layer.rollBack()  # the user leaves edit mode before drawing

        self.assertTrue(self.layer.startEditing())
        with patch.object(controllers_module.QTimer, "singleShot") as later:
            self.add_point()
        later.assert_not_called()
        self.layer.rollBack()

    def test_saving_the_drawn_feature_is_not_taken_for_an_abandoned_draw(self) -> None:
        # The commit stops the edit session; the draw must still finish and report success.
        with patch.object(PythonFailLogger, "log") as log:
            self.draw(self.handler(7))

        self.show_info.assert_called_once_with("S", "saved 42")
        self.assertEqual(self.layer.featureCount(), 1)
        self.assertNotIn("module_feature_draw_abandoned", [c.args[0] for c in log.call_args_list])

    def test_a_layer_the_user_is_editing_is_refused_and_left_untouched(self) -> None:
        # Saving the drawing would commit the whole session; keeping it pending would
        # report a save that did not happen. Neither: the draw does not start.
        self.assertTrue(self.layer.startEditing())
        earlier = QgsFeature(self.layer.fields())
        earlier.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(5, 5)))
        self.assertTrue(self.layer.addFeature(earlier))
        controller = ModuleFeatureDrawController()

        started = controller.start_draw(
            item_data={"id": "42"}, resolve_layer=lambda: self.layer, on_feature_created=self.handler(7),
            start_failed_message="start failed", layer_save_failed_message=LAYER_SAVE_FAILED,
            sync_failed_message=SYNC_FAILED, success_message=SUCCESS, title_error="E", title_success="S",
            log_module="easement",
        )

        self.assertFalse(started)
        self.assertIn("draw", self.warned())
        self.assertTrue(self.layer.isEditable())  # the user's session and its earlier edit stay
        self.assertEqual(self.layer.featureCount(), 1)
        controllers_module.iface.actionAddFeature.assert_not_called()
        self.layer.rollBack()


class AttachFlowTest(DialogStubCase):
    def test_attach_runs_the_kavitro_update_and_reports_its_failure(self) -> None:
        controller = ModuleFeatureAttachController()
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "attach", "memory")
        feature = Mock()
        feature.id.return_value = 3
        sync = Mock(return_value=(False, "geometry not sent"))
        controller._layer = layer
        controller._item_id = "9"
        controller._find_feature_at_point = lambda _point, _layer: feature
        controller._attach_handler = Mock(return_value=FeatureLinkResult(True, "", sync))

        with patch.object(controllers_module, "MapHelpers"), patch.object(controller, "_clear_capture_tool"):
            controller._handle_point_selected(
                QgsPointXY(0, 0),
                feature_not_found_message="missing",
                save_failed_message="{item_id}: {error}",
                success_message="ok {item_id}",
                title_error="E",
                title_warning="W",
                title_success="S",
                log_module="easement",
            )

        sync.assert_called_once_with()
        self.show_warning.assert_not_called()
        self.show_info.assert_not_called()
        title, text = self.ask_choice_modern.call_args.args[:2]
        self.assertEqual(title, "E")
        self.assertTrue(text.startswith("9: geometry not sent\n\n"), text)


class AttachRetryTest(DialogStubCase):
    def test_attach_can_send_a_failed_kavitro_update_again(self) -> None:
        controller = ModuleFeatureAttachController()
        feature = Mock()
        feature.id.return_value = 3
        sync = Mock(side_effect=[(False, "geometry not sent"), RuntimeError("network gone"), (True, "ok")])
        controller._layer = QgsVectorLayer("Point?crs=EPSG:3301", "attach", "memory")
        controller._item_id = "9"
        controller._find_feature_at_point = lambda _point, _layer: feature
        controller._attach_handler = Mock(return_value=FeatureLinkResult(True, "", sync))
        self.ask_choice_modern.side_effect = lambda *_args, **kwargs: kwargs["buttons"][0]

        with patch.object(controllers_module, "MapHelpers"), patch.object(controller, "_clear_capture_tool"):
            controller._handle_point_selected(
                QgsPointXY(0, 0), feature_not_found_message="missing", save_failed_message="{item_id}: {error}",
                success_message="ok {item_id}", title_error="E", title_warning="W", title_success="S",
                log_module="easement",
            )

        self.assertEqual(sync.call_count, 3)
        self.assertEqual(self.ask_choice_modern.call_count, 2)
        self.assertTrue(self.ask_choice_modern.call_args_list[1].args[1].startswith("9: network gone"))
        self.show_info.assert_called_once_with("S", "ok 9")
        self.show_warning.assert_not_called()


class ModuleHandlersTest(DialogStubCase):
    """Each module returns its Kavitro update instead of sending it while linking."""

    PAYLOAD = {"type": "Point", "coordinates": [1, 2]}

    def start(self, target, name, **kwargs) -> Mock:
        patcher = patch.object(target, name, **kwargs)
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started

    def check(self, link: FeatureLinkResult, api_call: Mock) -> None:
        self.assertTrue(link.success)
        api_call.assert_not_called()
        api_call.return_value = False
        synced, _detail = link.sync_to_kavitro()
        self.assertFalse(synced)
        api_call.assert_called_once_with("42", self.PAYLOAD)

    def test_easement(self) -> None:
        api = self.start(easement_module, "APIModuleActions")
        self.start(easement_module.EasementGeometryFormDialog, "prompt", return_value={})
        self.start(easement_module.EasementLayerService, "attach_backend_item_to_feature", return_value=(True, ""))
        self.start(easement_module.EasementAttachExistingController, "_geometry_payload_for_item", return_value=self.PAYLOAD)
        controller = easement_module.EasementAttachExistingController(lang_manager=LanguageManager())
        self.check(controller._attach_easement_feature_with_form(None, 1, {"id": "42"}), api.update_easement_geometry)

    def test_asbuilt(self) -> None:
        api = self.start(asbuilt_module, "APIModuleActions")
        self.start(asbuilt_module.AsBuiltGeometryFormDialog, "prompt", return_value={})
        self.start(asbuilt_module.AsBuiltLayerService, "attach_backend_item_to_feature", return_value=(True, ""))
        self.start(asbuilt_module.AsBuiltFeatureMapController, "_geometry_payload_for_item", return_value=self.PAYLOAD)
        link = asbuilt_module.AsBuiltFeatureMapController._attach_asbuilt_feature_and_sync_geometry(None, 1, {"id": "42"})
        self.check(link, api.update_task_geometry)

    def test_project_failure_is_no_longer_reported_as_success(self) -> None:
        api = self.start(projects_module, "APIModuleActions")
        self.start(projects_module.ProjectsLayerService, "attach_backend_item_to_feature", return_value=(True, ""))
        self.start(projects_module.ProjectsFeatureMapController, "_geometry_payload_for_item", return_value=self.PAYLOAD)
        link = projects_module.ProjectsFeatureMapController._attach_project_area_and_sync_geometry(None, 1, {"id": "42"})
        self.check(link, api.update_project_geometry)

    def test_each_module_shows_the_not_saved_text_for_a_layer_failure(self) -> None:
        lang = LanguageManager()
        for controller, key in (
            (easement_module.EasementAttachExistingController(lang_manager=lang), TranslationKeys.EASEMENT_DRAW_NEW_LAYER_SAVE_FAILED),
            (asbuilt_module.AsBuiltFeatureMapController(lang_manager=lang), TranslationKeys.ASBUILT_DRAW_NEW_LAYER_SAVE_FAILED),
            (projects_module.ProjectsFeatureMapController(lang_manager=lang), TranslationKeys.PROJECT_DRAW_NEW_LAYER_SAVE_FAILED),
        ):
            with self.subTest(key=key):
                messages = controller._workflow._config.draw_messages
                self.assertEqual(messages.layer_save_failed_template, lang.translate(key))
                self.assertNotEqual(messages.layer_save_failed_template, messages.sync_failed_template)
                self.assertIn("{error}", messages.layer_save_failed_template)


if __name__ == "__main__":
    unittest.main()
