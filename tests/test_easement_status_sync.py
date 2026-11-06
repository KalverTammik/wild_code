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

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout

from Kavitro_dev.modules.easements import easement_attach_existing_controller as controller_module
from Kavitro_dev.modules.easements import easement_preview_dialog as preview_module
from Kavitro_dev.python import api_actions as api_module
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.utils.status_color_helper import StatusColorHelper
from Kavitro_dev.widgets.DataDisplayWidgets.MainStatusWidget import MainStatusWidget
from Kavitro_dev.widgets.DataDisplayWidgets.ModuleConnectionActions import ModuleConnectionActions
from Kavitro_dev.widgets.DataDisplayWidgets.module_action_buttons import MoreActionsButton

PREPARING = {"id": "1", "name": "Ettevalmistamisel", "color": "4FBF6B", "type": "OPEN"}
SIGNED = {"id": "2", "name": "Allkirjastatud", "color": "2188FF", "type": "OPEN"}


class StubLanguageManager:
    @staticmethod
    def translate(key) -> str:
        return str(getattr(key, "value", key) or "")


class EasementStatusApiTest(unittest.TestCase):
    def _client(self, response=None, *, error=None) -> Mock:
        client = Mock()
        if error is not None:
            client.send_query.side_effect = error
        else:
            client.send_query.return_value = response
        for target, name, kwargs in (
            (api_module, "APIClient", {"return_value": client}),
            (api_module.PythonFailLogger, "log_exception", {}),
        ):
            patcher = patch.object(target, name, **kwargs)
            started = patcher.start()
            self.addCleanup(patcher.stop)
            if name == "log_exception":
                self.log = started
        return client

    def test_change_sends_the_status_id_in_the_easement_input(self) -> None:
        client = self._client({"updateEasement": {"id": "7", "status": SIGNED}})

        self.assertEqual(APIModuleActions.update_easement_status("7", "2"), SIGNED)

        (query,), kwargs = client.send_query.call_args
        self.assertIn("updateEasement(input: $input)", query)
        self.assertEqual(kwargs["variables"], {"input": {"id": "7", "status": "2"}})

    def test_answer_with_another_status_counts_as_refused(self) -> None:
        self._client({"updateEasement": {"id": "7", "status": PREPARING}})

        self.assertIsNone(APIModuleActions.update_easement_status("7", "2"))
        self.assertEqual(self.log.call_args.kwargs["event"], "easement_update_status_not_applied")

    def test_failed_request_counts_as_refused(self) -> None:
        self._client(error=RuntimeError("offline"))

        self.assertIsNone(APIModuleActions.update_easement_status("7", "2"))
        self.assertEqual(self.log.call_args.kwargs["event"], "easement_update_status_failed")

    def test_nothing_is_sent_without_an_easement_or_a_status(self) -> None:
        client = self._client({})

        self.assertIsNone(APIModuleActions.update_easement_status("", "2"))
        self.assertIsNone(APIModuleActions.update_easement_status("7", " "))
        self.assertIsNone(APIModuleActions.get_easement_status(""))
        client.send_query.assert_not_called()

    def test_read_returns_the_status_kavitro_has_now(self) -> None:
        client = self._client({"easement": {"id": "7", "status": SIGNED}})

        self.assertEqual(APIModuleActions.get_easement_status("7"), SIGNED)

        (query,), kwargs = client.send_query.call_args
        self.assertIn("easement(id: $id)", query)
        self.assertEqual(kwargs["variables"], {"id": "7"})

    def test_unreadable_status_returns_nothing(self) -> None:
        for response in ({"easement": None}, {"easement": {"id": "7", "status": None}}):
            with self.subTest(response=response):
                self._client(response)
                self.assertIsNone(APIModuleActions.get_easement_status("7"))

        self._client(error=RuntimeError("offline"))
        self.assertIsNone(APIModuleActions.get_easement_status("7"))
        self.assertEqual(self.log.call_args.kwargs["event"], "easement_status_fetch_failed")


class EasementCardStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def _card(self, item: dict):
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        layout = QHBoxLayout(card)
        status = MainStatusWidget(item, module_name="easement", parent=card)
        actions = ModuleConnectionActions("easement", item["id"], item, StubLanguageManager())
        layout.addWidget(status)
        layout.addWidget(actions)

        def delete() -> None:
            card.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(delete)
        more = next(button for button in actions.buttons if isinstance(button, MoreActionsButton))
        return status, more

    def test_status_from_the_form_reaches_only_its_own_card(self) -> None:
        status, more = self._card({"id": "1", "status": PREPARING})
        other_status, _other_more = self._card({"id": "2", "status": PREPARING})

        more._handle_easement_status_changed(SIGNED)

        bg, _fg, _border = StatusColorHelper.upgrade_status_color(SIGNED["color"])
        self.assertEqual(status._status_name, SIGNED["name"])
        self.assertIn(f"rgba({bg[0]},{bg[1]},{bg[2]}", status.core_fill.styleSheet())
        self.assertEqual(more._item_data["status"], SIGNED)
        self.assertEqual(other_status._status_name, PREPARING["name"])

    def test_both_form_flows_pass_the_card_update_on(self) -> None:
        _status, more = self._card({"id": "1", "status": PREPARING})
        prompt = patch.object(controller_module.EasementGeometryFormDialog, "prompt", return_value=None)

        with prompt as attach_prompt:
            controller = controller_module.EasementAttachExistingController.__new__(controller_module.EasementAttachExistingController)
            controller._on_status_changed = more._handle_easement_status_changed
            controller._attach_easement_feature_with_form(None, 1, {"id": "1"})

        self.assertEqual(attach_prompt.call_args.kwargs["on_status_changed"], more._handle_easement_status_changed)

        dialog = preview_module.EasementPreviewDialog.__new__(preview_module.EasementPreviewDialog)
        dialog._item, dialog._property_edges, dialog._final_area_sqm = {"id": "1"}, [], 0.0
        dialog._lang = StubLanguageManager()
        dialog._on_status_changed = more._handle_easement_status_changed
        with (
            patch.object(preview_module.EasementPreviewDialog, "_ensure_final_cut_layer", return_value=(object(), "")),
            patch.object(preview_module.EasementLayerService, "resolve_main_layer", return_value=object()),
            patch.object(preview_module.EasementGeometryFormDialog, "prompt", return_value=None) as preview_prompt,
        ):
            preview_module.EasementPreviewDialog._save_final_cut_to_main_layer(dialog)

        self.assertEqual(preview_prompt.call_args.kwargs["on_status_changed"], more._handle_easement_status_changed)

    def test_card_buttons_hand_their_update_to_the_form_flows(self) -> None:
        _status, more = self._card({"id": "1", "status": PREPARING})

        with patch.object(controller_module.EasementAttachExistingController, "start_attach") as start:
            more._attach_existing_easement_on_map({"id": "1"}, StubLanguageManager())

        self.assertTrue(start.called)
        self.assertEqual(more._easement_feature_map_controller._on_status_changed, more._handle_easement_status_changed)


if __name__ == "__main__":
    unittest.main()
