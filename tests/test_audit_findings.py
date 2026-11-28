"""The button audit's last open findings: easement property data, a failed work move, search
"show more" and a filter selection made while the options are still loading."""
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
from qgis.PyQt.QtCore import QCoreApplication, QEvent, Qt

from Kavitro_dev.constants.module_names import Module
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.easements import easement_preview_dialog as preview_module
from Kavitro_dev.modules.easements.preview_dialog import preview_layers_mixin as layers_module
from Kavitro_dev.modules.easements.preview_dialog import property_editor_mixin as editor_module
from Kavitro_dev.modules.works import works_reposition_controller as reposition_module
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.modules.works.works_sync_service import WorksSyncService
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.utils.api_error_handling import ApiError, ApiErrorKind
from Kavitro_dev.utils.search.UnifiedSearchController import UnifiedSearchController
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget
from Kavitro_dev.widgets.SearchResultsWidget import SearchResultsWidget

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager()
OFFLINE = ApiError(ApiErrorKind.NETWORK, "Network is down")
DIALOG = preview_module.EasementPreviewDialog


def delete_later(test: unittest.TestCase, widget) -> None:
    def delete() -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    test.addCleanup(delete)


class _Patches(unittest.TestCase):
    def start(self, target, name: str, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started


class EasementPropertySaveTest(_Patches):
    def setUp(self) -> None:
        self.messages = self.start(editor_module, "ModernMessageDialog")
        self.start(editor_module.PythonFailLogger, "log_exception")
        self.api = self.start(editor_module, "APIModuleActions")
        self.api.resolve_property_map_by_cadastral.return_value = ({}, [])
        dialog = DIALOG.__new__(DIALOG)
        dialog._item_id = "42"
        dialog._lang = LANG
        dialog._property_edges = []
        dialog._set_property_edges = Mock()
        dialog._rerun_automation = Mock()
        dialog._save_final_cut_to_main_layer = Mock(return_value=(True, ""))
        self.areas: dict[str, float] = {}
        self.cut = object()
        dialog._ensure_final_cut_layer = Mock(return_value=(self.cut, ""))
        dialog._apply_final_cut_area_calculations = Mock(side_effect=lambda _layer: self.areas.update(row=125.0))
        dialog._collect_property_payloads = Mock(side_effect=lambda: (
            [{"id": "p1", "area": {"size": self.areas.get("row", 0.0), "unit": "M2"}}], []))
        self.dialog = dialog

    def test_the_cut_areas_are_calculated_before_the_data_is_collected(self) -> None:
        DIALOG._save_property_details(self.dialog)

        self.dialog._apply_final_cut_area_calculations.assert_called_once_with(self.cut)
        _item, sent = self.api.associate_easement_properties.call_args.args
        self.assertEqual(sent[0]["area"]["size"], 125.0)

    def test_a_failed_read_after_saving_keeps_the_rows_and_leaves_the_layer_alone(self) -> None:
        self.api.get_easement_property_edges.side_effect = OFFLINE

        DIALOG._save_property_details(self.dialog)

        self.dialog._set_property_edges.assert_not_called()
        self.dialog._save_final_cut_to_main_layer.assert_not_called()
        self.messages.show_info.assert_not_called()
        self.messages.show_warning.assert_called_once_with(
            LANG.translate(TranslationKeys.ERROR),
            LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_REFRESH_FAILED).format(
                pid="42", err="Network is down"),
        )


class EasementPropertyLoadTest(_Patches):
    def test_a_failed_read_is_shown_and_nothing_is_replaced(self) -> None:
        messages = self.start(preview_module, "ModernMessageDialog")
        self.start(preview_module.PythonFailLogger, "log_exception")
        self.start(preview_module.APIModuleActions, "get_easement_property_edges", side_effect=OFFLINE)
        dialog = DIALOG.__new__(DIALOG)
        dialog._item_id, dialog._lang = "42", LANG
        dialog._status_label = Mock()
        dialog._set_property_edges = Mock()
        dialog._run_connected_property_preview_flow = Mock()

        DIALOG._initialize_connected_property_flow(dialog)

        text = LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTIES_LOAD_FAILED).format(err="Network is down")
        messages.show_warning.assert_called_once_with(LANG.translate(TranslationKeys.ERROR), text)
        dialog._status_label.setText.assert_called_once_with(text)
        dialog._set_property_edges.assert_not_called()
        dialog._run_connected_property_preview_flow.assert_not_called()

    def test_a_new_preview_round_drops_the_earlier_final_cut(self) -> None:
        memory = self.start(layers_module, "MemoryLayerResultService")
        dialog = DIALOG.__new__(DIALOG)
        dialog._lang = LANG
        dialog._final_preview_name = "vana lõige"
        dialog._connected_property_numbers = []
        dialog._property_summary_card = Mock()
        dialog._set_row_status = Mock()
        dialog._status_label = Mock()

        DIALOG._run_connected_property_preview_flow(dialog)

        memory.remove_existing.assert_called_once_with("vana lõige", only_memory=True)
        self.assertEqual(dialog._final_preview_name, "")


class WorkMoveMessageTest(_Patches):
    def setUp(self) -> None:
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:string", "Tööd", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(["7"])
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
        self.layer.dataProvider().addFeatures([feature])
        self.start(WorksLayerService, "resolve_main_layer", return_value=self.layer)
        self.send = self.start(APIModuleActions, "update_task_geometry", return_value=True)
        self.messages = self.start(reposition_module, "ModernMessageDialog")
        self.start(reposition_module.PythonFailLogger, "log_exception")
        sync = WorksSyncService()
        sync.attach()
        self.addCleanup(sync.detach)
        self.addCleanup(WorksSyncService._failed_geometry_tasks.clear)
        self.controller = reposition_module.WorksRepositionController()
        self.controller._layer, self.controller._task_id = self.layer, "7"
        self.controller._feature_id = next(self.layer.getFeatures()).id()
        self.controller._status_color = "00ff00"

    def test_a_move_kavitro_did_not_get_shows_no_success(self) -> None:
        self.send.return_value = False
        with patch("Kavitro_dev.modules.works.works_sync_service.PythonFailLogger"):
            self.controller._handle_point_selected(QgsPointXY(50, 60))

        self.messages.show_info.assert_not_called()

    def test_a_saved_move_shows_success_also_after_an_earlier_failure(self) -> None:
        WorksSyncService._failed_geometry_tasks.add("7")

        self.controller._handle_point_selected(QgsPointXY(50, 60))

        self.messages.show_info.assert_called_once()


class SearchShowMoreTest(unittest.TestCase):
    def _rows(self, widget) -> list[str]:
        return [widget.resultsList.item(row).data(Qt.ItemDataRole.UserRole)["type"]
                for row in range(widget.resultsList.count())]

    def test_show_more_opens_the_rest_without_a_new_search(self) -> None:
        widget = SearchResultsWidget()
        delete_later(self, widget)
        hits = [{"id": str(i), "title": f"Vaste {i}"} for i in range(8)]
        widget.show_results([{"type": "PROJECTS", "total": 8, "hits": hits}], None)
        self.assertEqual(self._rows(widget), ["header"] + ["result"] * 5 + ["show_more"])

        widget._on_item_clicked(widget.resultsList.item(6))

        self.assertEqual(self._rows(widget), ["header"] + ["result"] * 8)

    def test_the_search_asks_for_more_than_is_first_shown(self) -> None:
        with patch("Kavitro_dev.utils.search.UnifiedSearchController.APIClient") as client, \
                patch("Kavitro_dev.utils.search.UnifiedSearchController.GraphQLQueryLoader"):
            UnifiedSearchController._run_search(Mock(), "term")
        limit = client.return_value.send_query.call_args.kwargs["variables"]["input"]["limit"]
        self.assertTrue(5 < limit <= 10, limit)


class FilterChoiceWhileLoadingTest(_Patches):
    def setUp(self) -> None:
        self.settings = Mock()
        self.settings.load_module_preference_ids.return_value = ["1"]

    def _loaded(self, widget, payload) -> None:
        widget._handle_load_success(payload, widget._current_token(), widget._load_request_id)

    def test_clearing_while_the_types_load_stays_cleared(self) -> None:
        for choice, expected in (([], []), (None, ["1"])):
            with self.subTest(choice=choice):
                widget = TypeFilterWidget(Module.PROJECT.value, auto_load=False, settings_logic=self.settings)
                delete_later(self, widget)
                if choice is not None:
                    widget.set_selected_ids(choice, emit=False)

                self._loaded(widget, [{"id": "1", "label": "Üks", "group": ""}, {"id": "2", "label": "Kaks", "group": ""}])

                self.assertEqual(widget.selected_ids(), expected)


if __name__ == "__main__":
    unittest.main()
