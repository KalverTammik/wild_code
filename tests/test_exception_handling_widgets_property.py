"""Exception handling in widgets/ and modules/Property: narrowed guards keep their fallback, broad guards leave a log line."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

import requests
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QObject, QUrl, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget
from qgis.core import Qgis

from property_fixtures import LocationFilterTestCase, close_dialog, open_dialog

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager, set_current_language
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.FlowControllers.attention_display_rules import AttentionDisplayRules
from Kavitro_dev.modules.Property.FlowControllers.main_layer_check_controller import MainLayerCheckController
from Kavitro_dev.modules.Property.widgets.property_ui_tools import PropertyUITools
from Kavitro_dev.modules.Property.widgets.property_tree_widget import PropertyTreeWidget
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.modules.Property.dialogs.AddUpdatePropertyDialog import AddPropertyDialog
from Kavitro_dev.modules.Property.FlowControllers.property_archive_scope_reader import layer_identity
from Kavitro_dev.widgets.DataDisplayWidgets.status_change_controller import StatusChangeController
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilesDialog import TaskFilesDialog
from Kavitro_dev.widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget
from Kavitro_dev.widgets.Filters.BaseSingleFilterWidget import BaseSingleFilterWidget
from Kavitro_dev.widgets.Filters.NotStartedStatusFilterWidget import NotStartedStatusFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import _TypePickerPopup
from Kavitro_dev.widgets.ModuleKpiCard import ModuleKpiCard
from Kavitro_dev.widgets.ProgressDialogModern import ProgressDialogModern
from Kavitro_dev.widgets.PropertySummaryCard import PropertySummaryCard
from Kavitro_dev.widgets.layer_tree_picker import LayerTreePicker
from Kavitro_dev.ui.theme_manager import ThemeManager

# The package re-exports some of these names as classes, so the modules are loaded by path.
check_module = importlib.import_module("Kavitro_dev.modules.Property.FlowControllers.main_layer_check_controller")
dialog_module = importlib.import_module("Kavitro_dev.modules.Property.dialogs.AddUpdatePropertyDialog")
html_module = importlib.import_module("Kavitro_dev.widgets.DataDisplayWidgets.HtmlDescriptionWidget")
preview_module = importlib.import_module("Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog")
from Kavitro_dev.widgets.DataDisplayWidgets import task_file_external_open as external_open
from Kavitro_dev.widgets.DataDisplayWidgets import task_file_identity

# Anything that could open a modal window if a regression reached it.
MESSAGE_DIALOG_METHODS = ("Info_messages_modern", "Warning_messages_modern", "Error_messages_modern",
                          "show_info", "show_warning", "show_error", "ask_choice_modern", "get_text_modern")


def logged(log_mock) -> list[str]:
    """Event names of a patched PythonFailLogger.log (log_exception forwards to it)."""
    return [call.args[0] for call in log_mock.call_args_list if call.args]


def call_for(log_mock, event: str):
    return next(call for call in log_mock.call_args_list if call.args and call.args[0] == event)


class WidgetCase(unittest.TestCase):
    """A fixture window that owns every widget a test builds, a patched logger and stubbed dialogs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = QWidget()
        patcher = patch.object(PythonFailLogger, "log")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)
        for name in MESSAGE_DIALOG_METHODS:
            stub = patch.object(ModernMessageDialog, name)
            stub.start()
            self.addCleanup(stub.stop)

    def tearDown(self) -> None:
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class AttentionRulesTest(unittest.TestCase):
    def test_failing_translate_keeps_the_raw_cause_and_leaves_a_log_line(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            text = AttentionDisplayRules._translate_cause_text(
                "missing in main layer", translate=Mock(side_effect=KeyError("Missing translation")))
        self.assertEqual(text, "missing in main layer")
        call = call_for(log, "attention_cause_translate_failed")
        self.assertEqual(call.kwargs["module"], "property")

    def test_working_translate_is_not_logged(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            text = AttentionDisplayRules._translate_cause_text("missing in main layer", translate=lambda key: "puudub")
        self.assertEqual(text, "puudub")
        log.assert_not_called()


class MainLayerCheckLookupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def controller(self, *, lookup=None) -> MainLayerCheckController:
        controller = MainLayerCheckController()
        self.addCleanup(controller.deleteLater)
        controller.configure(
            rows_for_verify_by_row={0: ("1234", "")},
            main_layer=Mock(),
            main_layer_lookup=lookup or {},
            lookup_is_complete=False,
        )
        return controller

    def test_failed_layer_read_is_logged_and_reported_as_a_lookup_failure(self) -> None:
        controller = self.controller()
        with patch.object(check_module.MapHelpers, "find_features_by_fields_and_values",
                          side_effect=RuntimeError("layer deleted")), \
                patch.object(PythonFailLogger, "log") as log:
            causes = controller._compute_causes_for_row(0)
        self.assertEqual(causes, [TranslationKeys.ATTENTION_CAUSE_MAIN_LAYER_LOOKUP_FAILED])
        call = call_for(log, "main_layer_lookup_failed")
        self.assertEqual(call.kwargs["module"], "property")
        self.assertEqual(call.kwargs["extra"], {"tunnus": "1234"})

    def test_plain_miss_is_missing_without_a_log_line(self) -> None:
        controller = self.controller()
        with patch.object(check_module.MapHelpers, "find_features_by_fields_and_values", return_value=[]), \
                patch.object(PythonFailLogger, "log") as log:
            self.assertEqual(controller._compute_causes_for_row(0), ["missing in main layer"])
        log.assert_not_called()

    def test_feature_without_the_date_field_is_not_older(self) -> None:
        feature = Mock()
        feature.attribute.side_effect = KeyError("muudet")
        controller = self.controller(lookup={"1234": feature})
        self.assertEqual(controller._compute_causes_for_row(0), [])

    def test_unexpected_attribute_error_is_not_swallowed(self) -> None:
        feature = Mock()
        feature.attribute.side_effect = RuntimeError("not a field problem")
        controller = self.controller(lookup={"1234": feature})
        with self.assertRaises(RuntimeError):
            controller._compute_causes_for_row(0)


class SipGuardsTest(WidgetCase):
    def test_objects_that_are_not_sip_wrappers_count_as_alive_and_none_as_deleted(self) -> None:
        for owner in (PropertyTreeWidget, StatusChangeController):
            with self.subTest(owner=owner.__name__):
                self.assertTrue(owner._is_deleted(None))
                self.assertFalse(owner._is_deleted(object()))
                live = QWidget(self.window)
                self.assertFalse(owner._is_deleted(live))
                sip.delete(live)
                self.assertTrue(owner._is_deleted(live))

    def tools(self, ui) -> PropertyUITools:
        tools = PropertyUITools.__new__(PropertyUITools)
        tools.property_ui = ui
        return tools

    def test_property_tools_treat_a_plain_object_as_not_an_active_ui(self) -> None:
        self.assertIsNone(self.tools(Mock())._get_active_ui())
        live = QWidget(self.window)
        self.assertIs(self.tools(live)._get_active_ui(), live)
        sip.delete(live)
        self.assertIsNone(self.tools(live)._get_active_ui())

    def test_property_tools_widget_validity(self) -> None:
        tools = self.tools(None)
        self.assertFalse(tools._is_widget_valid(None))
        self.assertFalse(tools._is_widget_valid(Mock()))
        live = QWidget(self.window)
        self.assertTrue(tools._is_widget_valid(live))
        sip.delete(live)
        self.assertFalse(tools._is_widget_valid(live))

    def test_token_of_a_closing_owner_is_stale_but_a_broken_owner_is_not_hidden(self) -> None:
        ui = QWidget(self.window)
        ui.is_token_active = Mock(side_effect=RuntimeError("owner closing"))
        self.assertFalse(self.tools(ui)._is_token_active(3))
        bare = QWidget(self.window)
        with self.assertRaises(AttributeError):
            self.tools(bare)._is_token_active(3)


class TaskFilePreviewHandlersTest(WidgetCase):
    def dialog(self) -> TaskFilePreviewDialog:
        with patch.object(TaskFilePreviewDialog, "_load_preview"), \
                patch.object(preview_module.ThemeManager, "apply_module_style"):
            return TaskFilePreviewDialog(
                file_info={"uuid": "u-1", "fileName": "a.pdf", "ext": "pdf"},
                parent=self.window,
            )

    FILE_INFO = {"uuid": "u-1", "fileName": "a.pdf", "ext": "pdf"}

    def test_download_failure_is_logged_without_the_link_and_leaves_no_temp_file(self) -> None:
        link = "https://files.example/a.pdf?sig=SECRET"
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(tempfile, "tempdir", folder), \
                patch.object(preview_module.APIModuleActions, "create_file_download_link", return_value=link), \
                patch.object(external_open.requests, "get",
                             side_effect=requests.ConnectionError(f"failed for {link}")):
            result = external_open.materialize_remote_file_to_temp(self.FILE_INFO, allowed_extension="pdf")
            self.assertEqual(os.listdir(os.path.join(folder, external_open.EXTERNAL_TEMP_FOLDER_NAME)), [])
        self.assertEqual(result, "")
        call = call_for(self.log, "task_file_preview_download_failed")
        self.assertEqual(call.kwargs["extra"], {"error_type": "ConnectionError", "uuid": "u-1"})
        self.assertNotIn("SECRET", repr(call))

    def test_temp_file_that_cannot_be_created_ends_the_download_quietly(self) -> None:
        with patch.object(preview_module.APIModuleActions, "create_file_download_link",
                          return_value="https://files.example/a.pdf"), \
                patch.object(tempfile, "mkstemp", side_effect=OSError("disk full")):
            result = external_open.materialize_remote_file_to_temp(self.FILE_INFO, allowed_extension="pdf")
        self.assertEqual(result, "")
        self.assertIn("task_file_preview_download_failed", logged(self.log))

    def test_pdf_temp_write_failure_is_logged_and_forgets_the_path(self) -> None:
        dialog = self.dialog()
        with patch.object(tempfile, "mkstemp", side_effect=OSError("disk full")):
            self.assertEqual(dialog._write_pdf_temp_file(b"%PDF"), "")
        self.assertEqual(dialog._pdf_temp_path, "")
        self.assertIn("task_file_preview_pdf_temp_write_failed", logged(self.log))

    def test_missing_file_association_falls_back_to_the_desktop_services(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            path = handle.name
        self.addCleanup(os.remove, path)
        with patch.object(os, "startfile", side_effect=OSError("no association"), create=True), \
                patch.object(external_open.QDesktopServices, "openUrl", return_value=True) as open_url:
            self.assertTrue(external_open.open_local_path(path))
        open_url.assert_called_once()

    def test_web_view_that_cannot_be_created_is_logged(self) -> None:
        dialog = self.dialog()

        class Broken:
            def __init__(self, _parent):
                raise RuntimeError("no web engine")

        self.assertFalse(dialog._load_pdf_webengine_preview(
            "a.pdf", webengine_settings_cls=object, webengine_view_cls=Broken))
        self.assertIn("task_file_preview_webview_create_failed", logged(self.log))

    def test_web_view_that_refuses_the_pdf_is_logged_and_released(self) -> None:
        dialog = self.dialog()

        class RefusingView(QWidget):
            loadFinished = SimpleNamespace(connect=Mock(side_effect=TypeError("no such signal")))

            def settings(self):
                return SimpleNamespace(setAttribute=Mock(side_effect=TypeError("wrong enum")))

            def stop(self):
                pass

            def setUrl(self, _url):
                raise RuntimeError("view deleted")

            def load(self, _url):
                raise RuntimeError("view deleted")

        settings_cls = SimpleNamespace(PdfViewerEnabled=1, PluginsEnabled=2)
        self.assertFalse(dialog._load_pdf_webengine_preview(
            "a.pdf", webengine_settings_cls=settings_cls, webengine_view_cls=RefusingView))
        events = logged(self.log)
        self.assertIn("task_file_preview_loadfinished_connect_failed", events)
        self.assertIn("task_file_preview_pdf_load_failed", events)
        self.assertIsNone(dialog._web_view)

    def test_release_of_an_already_deleted_web_view_is_quiet(self) -> None:
        dialog = self.dialog()
        view = Mock()
        view.stop.side_effect = RuntimeError("deleted")
        view.setUrl.side_effect = RuntimeError("deleted")
        view.deleteLater.side_effect = RuntimeError("deleted")
        dialog._web_view = view
        dialog._release_web_view()
        self.assertIsNone(dialog._web_view)

    def test_undecodable_text_and_odd_sizes_keep_their_fallbacks(self) -> None:
        self.assertEqual(task_file_identity.decode_text(b"\x81"), "\x81")
        self.assertEqual(task_file_identity.human_readable_size("many"), "–")


class HtmlDescriptionFallbackTest(WidgetCase):
    def test_link_without_the_decoded_form_is_still_classified(self) -> None:
        class UrlWithoutDecodedForm(QUrl):
            def toString(self, *args):
                if args:
                    raise TypeError("no formatting argument in this binding")
                return super().toString()

        widget = html_module.HtmlDescriptionWidget("<p>x</p>", self.window)
        with patch.object(html_module, "classify_description_link",
                          wraps=html_module.classify_description_link) as classify, \
                patch.object(ModernMessageDialog, "ask_choice_modern", return_value="No"):
            widget._handle_anchor_clicked(UrlWithoutDecodedForm("https://example.com"))
        self.assertEqual(classify.call_args_list[0].args[0], "https://example.com")


class SmallWidgetHandlersTest(WidgetCase):
    def test_area_widget_float_coercion(self) -> None:
        coerce = EasementPropertyAreaCalculationWidget._coerce_float
        self.assertEqual(coerce("2.5"), 2.5)
        for value in (None, "", "abc", [1]):
            with self.subTest(value=value):
                self.assertIsNone(coerce(value))

    def test_created_at_falls_back_when_the_locale_cannot_format_it(self) -> None:
        locale = Mock(toString=Mock(side_effect=TypeError("unsupported")))
        self.assertEqual(TaskFilesDialog._format_created_at("2026-01-02T03:04:05", locale), "2026-01-02 03:04")
        self.assertEqual(TaskFilesDialog._format_created_at("not a date", locale), "–")

    def test_layer_picker_guards_keep_their_fallbacks(self) -> None:
        picker = LayerTreePicker(self.window)
        picker.setFilters(Qgis.LayerFilter.HasGeometry)
        self.assertTrue(picker._layer_allowed(None))
        picker.setShowCrs(True)
        layer = SimpleNamespace(name=lambda: "Roads", crs=Mock(side_effect=RuntimeError("deleted")))
        self.assertEqual(picker._layer_label(layer), "Roads")

    def test_kpi_card_cancels_a_worker_whose_signals_are_not_connected_or_gone(self) -> None:
        class Worker(QObject):
            finished = pyqtSignal(object)
            error = pyqtSignal(str)

        for gone in (False, True):
            with self.subTest(deleted=gone):
                worker = Worker()
                card = SimpleNamespace(_worker=worker, _worker_thread=None,
                                       _handle_success=lambda _payload: None, _handle_error=lambda _message: None)
                if gone:
                    sip.delete(worker)
                ModuleKpiCard._cancel_worker(card)
                self.assertIsNone(card._worker)

    def test_type_picker_height_falls_back_when_the_owner_is_gone(self) -> None:
        for control in (None, Mock(mapToGlobal=Mock(side_effect=RuntimeError("deleted")))):
            with self.subTest(control=control):
                popup = SimpleNamespace(_owner=SimpleNamespace(_control=control), _max_body_height=0)
                _TypePickerPopup._update_available_height(popup)
                self.assertEqual(popup._max_body_height, 520)

    def test_progress_dialog_theme_failure_is_logged_and_the_dialog_still_builds(self) -> None:
        with patch.object(ThemeManager, "apply_module_style", side_effect=OSError("qss missing")):
            dialog = ProgressDialogModern("Title", 10, self.window)
        self.assertIsNotNone(dialog)
        self.assertIn("progress_dialog_theme_failed", logged(self.log))

    def test_summary_card_clears_and_logs_when_a_field_read_fails(self) -> None:
        card = PropertySummaryCard(self.window)
        feature = Mock()
        feature.attribute.side_effect = ValueError("odd value")
        card.set_feature(feature)
        self.assertEqual(card.lbl_katastritunnus_value.text(), "—")
        call = call_for(self.log, "property_summary_card_set_feature_failed")
        self.assertEqual(call.kwargs["module"], "property")


class FilterSavedIdsTest(WidgetCase):
    def test_failing_saved_ids_loader_is_logged_and_the_load_still_finishes(self) -> None:
        settings = Mock()
        settings.load_module_preference_ids.return_value = []
        widget = BaseSingleFilterWidget(
            "contract", "Label", "FilterObject", "support", self.window, auto_load=False,
            settings_logic=settings,
            selected_ids_loader=Mock(side_effect=ValueError("bad saved ids")),
        )
        finished = Mock()
        widget.loadFinished.connect(finished)
        widget._load_request_id = 4
        widget._handle_load_success([("A", "a")], None, 4)
        finished.assert_called_once_with(True)
        call = call_for(self.log, "filter_saved_ids_load_failed")
        self.assertEqual(call.kwargs["module"], "contract")


class NotStartedFilterLanguageTest(WidgetCase):
    """Like the other filter widgets, the not-started status filter follows the plugin-wide language."""

    def test_title_follows_the_current_language(self) -> None:
        set_current_language("en")
        self.addCleanup(set_current_language, "et")
        widget = NotStartedStatusFilterWidget("project", self.window, auto_load=False, settings_logic=Mock())
        self.assertEqual(widget.selector.toolTip(),
                         LanguageManager().translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_TITLE))


class AddDialogHandlersTest(LocationFilterTestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = patch.object(PythonFailLogger, "log")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)
        for name in MESSAGE_DIALOG_METHODS:
            stub = patch.object(ModernMessageDialog, name)
            stub.start()
            self.addCleanup(stub.stop)

    def test_failed_map_selection_start_is_logged_and_the_dialog_still_opens(self) -> None:
        self.add_import_fields()
        with patch.object(dialog_module.DialogHelpers, "enter_map_selection_mode",
                          side_effect=RuntimeError("no coordinator")):
            dialog = open_dialog(AddPropertyDialog, self.window)
        try:
            self.assertIn("add_property_map_selection_start_failed", logged(self.log))
            self.assertIsNone(dialog._parent_window)
            self.assertFalse(dialog._restore_parent_on_close)
        finally:
            close_dialog(self, dialog)

    def test_malformed_backend_row_result_is_logged(self) -> None:
        class Unprintable:
            def __str__(self):
                raise ValueError("no text form")

        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog, self.window)
        try:
            dialog._on_backend_verify_row_result(0, "1", {"causes": [Unprintable()]})
            self.assertIn("add_property_backend_verify_causes_failed", logged(self.log))
        finally:
            close_dialog(self, dialog)

    def test_layer_identity_of_a_deleted_layer_is_empty(self) -> None:
        layer = SimpleNamespace(id=Mock(side_effect=RuntimeError("deleted")), source=lambda: "memory://x")
        self.assertEqual(layer_identity(layer), ("", "memory://x"))
        self.assertEqual(layer_identity(None), ("", ""))
        self.assertEqual(layer_identity(object()), ("", ""))


if __name__ == "__main__":
    unittest.main()
