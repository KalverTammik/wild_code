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

from qgis.core import QgsApplication, QgsPointXY
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.works import works_create_controller as controller_module
from Kavitro_dev.utils.FilterHelpers.FilterHelper import FilterHelper
from Kavitro_dev.modules.works import works_create_dialog as dialog_module
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

Dialog = dialog_module.WorksCreateDialog
ALL_FAILURES = sorted(
    [Dialog.LOAD_FAILED_TYPES, Dialog.LOAD_FAILED_RESPONSIBLES, Dialog.LOAD_FAILED_STATUSES, Dialog.LOAD_FAILED_PRIORITIES]
)
TYPES = [{"id": "t", "label": "Avarii"}]
USERS = [{"id": "1", "displayName": "Kasutaja"}]
STATUSES = [{"id": "s", "name": "Planeeritud", "color": "4FBF6B", "isDefault": True}]
PRIORITIES = [{"value": "", "label": "Puudub"}, {"value": "HIGH", "label": "Kõrge"}]


class _Patched(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.events: list[str] = []
        for active in (
            patch.object(ModernMessageDialog, "show_warning"),
            patch.object(ModernMessageDialog, "show_info"),
            patch.object(controller_module.PythonFailLogger, "log_exception", side_effect=self._log),
            patch.object(dialog_module.WorksLayerService, "property_display_text", return_value=""),
        ):
            active.start()
            self.addCleanup(active.stop)

    def _log(self, _exc, **kwargs) -> None:
        self.events.append(kwargs.get("event", ""))


class WorksCreateDialogLoadFailureTest(_Patched):
    def setUp(self) -> None:
        super().setUp()
        self.lang = LanguageManager(language="et")
        self.window = QWidget()

    def tearDown(self) -> None:
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def _dialog(self, **kwargs) -> Dialog:
        options = {
            "type_options": TYPES,
            "assignable_users": USERS,
            "status_options": STATUSES,
            "priority_options": PRIORITIES,
        }
        options.update(kwargs)
        return Dialog(point=QgsPointXY(1, 1), property_feature=None, parent=self.window, **options)

    def test_failed_type_load_says_so_and_blocks_creating(self) -> None:
        with patch.object(dialog_module.FilterHelper, "get_filter_edges_by_key_and_module") as lookup:
            dialog = self._dialog(type_options=[], load_failures=[Dialog.LOAD_FAILED_TYPES])

        lookup.assert_not_called()
        self.assertFalse(dialog._types_hint.isHidden())
        self.assertEqual(dialog._types_hint.text(), self.lang.translate(TranslationKeys.WORKS_CREATE_TYPES_LOAD_FAILED))
        self.assertFalse(dialog._create_btn.isEnabled())

    def test_failed_type_lookup_of_the_dialog_itself_says_so(self) -> None:
        with patch.object(dialog_module.FilterHelper, "get_filter_edges_by_key_and_module", side_effect=RuntimeError("x")):
            dialog = self._dialog(type_options=[])

        self.assertEqual(dialog._types_hint.text(), self.lang.translate(TranslationKeys.WORKS_CREATE_TYPES_LOAD_FAILED))
        self.assertFalse(dialog._create_btn.isEnabled())

    def test_types_that_loaded_empty_still_show_the_no_types_hint(self) -> None:
        with patch.object(dialog_module.FilterHelper, "get_filter_edges_by_key_and_module", return_value=[]):
            dialog = self._dialog(type_options=[])

        self.assertEqual(dialog._types_hint.text(), self.lang.translate(TranslationKeys.WORKS_CREATE_NO_TYPES))
        self.assertTrue(dialog._options_hint.isHidden())

    def test_failed_choice_lists_are_named_next_to_the_form(self) -> None:
        dialog = self._dialog(
            assignable_users=[],
            status_options=[],
            priority_options=[],
            load_failures=[Dialog.LOAD_FAILED_RESPONSIBLES, Dialog.LOAD_FAILED_STATUSES, Dialog.LOAD_FAILED_PRIORITIES],
        )

        translate = self.lang.translate
        fields = ", ".join(
            translate(key)
            for key in (
                TranslationKeys.WORKS_CREATE_RESPONSIBLE_LABEL,
                TranslationKeys.WORKS_CREATE_STATUS_LABEL,
                TranslationKeys.WORKS_CREATE_PRIORITY_LABEL,
            )
        )
        self.assertFalse(dialog._options_hint.isHidden())
        self.assertEqual(
            dialog._options_hint.text(),
            translate(TranslationKeys.WORKS_CREATE_OPTIONS_LOAD_FAILED).format(fields=fields),
        )
        self.assertFalse(dialog._priority_combo.isEnabled())
        self.assertFalse(dialog._responsible_combo.isEnabled())
        self.assertTrue(dialog._create_btn.isEnabled(), "the types loaded, so the work can still be created")

    def test_loaded_dialog_shows_no_failure_hint(self) -> None:
        dialog = self._dialog()

        self.assertTrue(dialog._options_hint.isHidden())
        self.assertTrue(dialog._types_hint.isHidden())
        self.assertTrue(dialog._priority_combo.isEnabled())
        self.assertTrue(dialog._create_btn.isEnabled())


class WorksCreateControllerLoadFailureTest(_Patched):
    def setUp(self) -> None:
        super().setUp()
        self.controller = controller_module.WorksCreateController()

    def _lookups(self, *, fail: bool, **overrides):
        error = RuntimeError("offline")

        def kwargs(name, value):
            if name in overrides:
                return {"return_value": overrides[name]}
            return {"side_effect": error} if fail else {"return_value": value}

        return (
            patch.object(FilterHelper, "get_filter_edges_by_key_and_module", **kwargs("types", TYPES)),
            patch.object(APIModuleActions, "get_assignable_users", **kwargs("users", USERS)),
            patch.object(APIModuleActions, "get_current_user_id", **kwargs("user_id", "1")),
            patch.object(APIModuleActions, "get_module_status_options", **kwargs("statuses", STATUSES)),
            patch.object(APIModuleActions, "get_task_priority_options", **kwargs("priorities", PRIORITIES)),
        )

    def _run(self, patches, call):
        for active in patches:
            active.start()
        try:
            return call()
        finally:
            for active in patches:
                active.stop()

    def _preload(self, *, fail: bool) -> None:
        self.controller._preload_request_id = 3
        payload = self._run(self._lookups(fail=fail), self.controller._fetch_preload_payload)
        self.controller._handle_preload_success(payload, 3)

    def test_failed_preload_and_failed_retry_reach_the_dialog_as_failures(self) -> None:
        self._preload(fail=True)

        options = self._run(self._lookups(fail=True), self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], ALL_FAILURES)
        self.assertEqual(options["type_options"], [])

    def test_failed_preload_with_a_working_retry_has_no_failures(self) -> None:
        self._preload(fail=True)

        options = self._run(self._lookups(fail=False), self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], [])
        self.assertEqual(options["type_options"], TYPES)
        self.assertEqual(options["default_responsible_id"], "1")

    def test_preload_worker_error_is_retried_and_reported(self) -> None:
        self.controller._preload_request_id = 4
        self.controller._handle_preload_error("worker crashed", 4)

        options = self._run(self._lookups(fail=True), self.controller._resolve_dialog_options)

        self.assertIn("works_create_dialog_preload_failed", self.events)
        self.assertEqual(options["load_failures"], ALL_FAILURES)

    def test_successful_preload_has_no_failures_and_sends_nothing_more(self) -> None:
        self._preload(fail=False)
        patches = self._lookups(fail=True)

        options = self._run(patches, self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], [])
        self.assertEqual(options["status_options"][0]["id"], "s")

    def test_statuses_that_loaded_empty_are_not_a_failure(self) -> None:
        options = self._run(self._lookups(fail=False, statuses=[]), self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], [])
        self.assertEqual(options["status_options"], [])

    def test_status_lookups_ask_for_the_error_instead_of_an_empty_list(self) -> None:
        # Without raise_on_error a failed read comes back as [] and looks like a module without statuses.
        patches = self._lookups(fail=False)
        with patch.object(APIModuleActions, "get_module_status_options", return_value=STATUSES) as lookup:
            self._run(patches[:3] + patches[4:], self.controller._fetch_preload_payload)
            self._run(patches[:3] + patches[4:], self.controller._resolve_status_options)

        self.assertEqual(lookup.call_count, 2)
        for call in lookup.call_args_list:
            self.assertTrue(call.kwargs.get("raise_on_error"))

    def test_an_empty_user_list_counts_as_a_failed_load(self) -> None:
        # get_assignable_users swallows a failed request; a successful one always holds the logged-in user.
        options = self._run(self._lookups(fail=False, users=[]), self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], [Dialog.LOAD_FAILED_RESPONSIBLES])

    def test_failures_are_counted_again_for_each_dialog(self) -> None:
        self._run(self._lookups(fail=True), self.controller._resolve_dialog_options)

        options = self._run(self._lookups(fail=False), self.controller._resolve_dialog_options)

        self.assertEqual(options["load_failures"], [])

    def test_clicked_point_opens_the_dialog_with_the_failures(self) -> None:
        received: dict = {}

        class _RejectingDialog:
            Accepted = 1

            def __init__(self, **kwargs) -> None:
                received.update(kwargs)

            def exec(self) -> int:
                return 0

        patches = self._lookups(fail=True) + (
            patch.object(controller_module, "WorksCreateDialog", _RejectingDialog),
            patch.object(controller_module.WorksLayerService, "find_property_feature_at_point", return_value=None),
            patch.object(controller_module.WorksCreateController, "_clear_capture_tool"),
        )
        self._run(patches, lambda: self.controller._handle_point_selected(QgsPointXY(1, 1)))

        self.assertEqual(received["load_failures"], ALL_FAILURES)
        self.assertEqual(received["default_responsible_id"], "")


if __name__ == "__main__":
    unittest.main()
