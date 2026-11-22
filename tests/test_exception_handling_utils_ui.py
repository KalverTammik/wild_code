"""Exception handling in utils/ and ui/: narrowed guards keep their fallback, broad guards leave a log line."""
from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, QPoint
from PyQt5.QtWidgets import QApplication, QTableView, QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.contract.ContractUi import ContractsModule
from Kavitro_dev.python.api_client import APIClient
from Kavitro_dev.ui.session_ui_controller import SessionUIController
from Kavitro_dev.ui.window_state.DialogCoordinator import DialogCoordinator
from Kavitro_dev.ui.window_state.popup_helpers import PopupHelpers
from Kavitro_dev.utils import security_boundaries
from Kavitro_dev.utils.SessionManager import SessionManager
from Kavitro_dev.utils.layers import layer_processing_service as lps_module
from Kavitro_dev.utils.layers.layer_processing_service import LayerProcessingService
from Kavitro_dev.ui.map_canvas_glass_overlay import MapCanvasGlassOverlayBase
from Kavitro_dev.ui.map_canvas_search_bar import MapCanvasSearchBar
from Kavitro_dev.utils.property import ArchiveLayerHandler as archive_module
from Kavitro_dev.widgets.property_table.PropertyTableManager import PropertyTableManager
from Kavitro_dev.widgets.property_table.property_table_model import PropertyTableModel
from Kavitro_dev.utils.secure_session_store import SecureSessionStore


def delete_now(widget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class QtCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])


def logged_events(log_mock) -> list[str]:
    """Event names of a patched PythonFailLogger.log / log_exception, whichever way they were passed."""
    events = []
    for call in log_mock.call_args_list:
        events.append(call.kwargs.get("event") or (call.args[0] if call.args else None))
    return events


class SecureSessionStoreLoggingTest(unittest.TestCase):
    SECRET = "super-secret-token-value"

    class Settings:
        def __init__(self, fail_remove: bool = False) -> None:
            self.values = {}
            self.fail_remove = fail_remove

        def value(self, key, default=None, **_kwargs):
            return self.values.get(key, default)

        def setValue(self, key, value):
            self.values[key] = value

        def remove(self, key):
            if self.fail_remove:
                raise ValueError(SecureSessionStoreLoggingTest.SECRET)
            self.values.pop(key, None)

        def sync(self):
            pass

    class AuthManager:
        def __init__(self) -> None:
            self.error = ValueError(SecureSessionStoreLoggingTest.SECRET)

        def loadAuthenticationConfig(self, *_args):
            raise self.error

        def updateAuthenticationConfig(self, *_args):
            raise self.error

        def storeAuthenticationConfig(self, *_args):
            raise self.error

        def removeAuthenticationConfig(self, *_args):
            raise self.error

        def availableAuthMethodConfigs(self):
            raise self.error

    def store(self, *, fail_remove: bool = False) -> SecureSessionStore:
        return SecureSessionStore(self.AuthManager(), self.Settings(fail_remove), lambda *_a: SimpleNamespace())

    def assert_type_only(self, log, event: str) -> None:
        events = logged_events(log)
        self.assertIn(event, events)
        call = log.call_args_list[events.index(event)]
        self.assertEqual(call.kwargs["module"], "auth")
        self.assertEqual(call.kwargs["extra"], {"error_type": "ValueError"})
        self.assertNotIn("message", call.kwargs)
        self.assertNotIn(self.SECRET, repr(call))

    def test_load_failure_is_logged_with_the_type_only_and_still_reports_unavailable(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            success, _config = self.store()._load_config("id", full=True)
        self.assertFalse(success)
        self.assert_type_only(log, "session_store_load_failed")

    def test_remove_failure_is_logged_with_the_type_only(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            self.assertFalse(self.store()._remove_auth_config("id"))
        self.assert_type_only(log, "session_store_remove_failed")

    def test_legacy_purge_failure_is_logged_with_the_type_only(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            self.assertFalse(self.store(fail_remove=True).purge_legacy_token())
        self.assert_type_only(log, "session_store_purge_legacy_failed")

    def test_discovery_failure_is_logged_and_still_reports_cleanup_pending(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            self.assertTrue(self.store().cleanup_stale_configs())
        self.assert_type_only(log, "session_store_cleanup_discovery_failed")


class SecurityBoundariesDriveProbeTest(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "the probe only runs on Windows")
    def test_a_failing_drive_probe_is_logged_and_reports_a_remote_drive(self) -> None:
        def broken(*_args):
            raise OSError("probe failed")

        fake_windll = SimpleNamespace(
            kernel32=SimpleNamespace(GetDriveTypeW=broken),
            mpr=SimpleNamespace(WNetGetConnectionW=broken),
        )
        with patch.object(ctypes, "windll", fake_windll, create=True), \
                patch.object(PythonFailLogger, "log") as log:
            # Fails closed: an unknown drive gets the network confirmation, never the silent local path.
            self.assertEqual(security_boundaries.windows_drive_type("Z:\\file.pdf"), security_boundaries._WINDOWS_DRIVE_REMOTE)
            self.assertEqual(security_boundaries.windows_mapped_drive_remote_name("Z:\\file.pdf"), "")
        self.assertEqual(logged_events(log), ["security_drive_probe_failed"] * 2)
        self.assertEqual(log.call_args.kwargs["module"], "general")


class OverlayLoggingTest(QtCase):
    class Overlay(MapCanvasGlassOverlayBase):
        SIZE = (10, 10)

        def __init__(self) -> None:
            super().__init__(object_name="TestOverlay")
            self._finish_init()

        def _build_ui(self) -> None:
            pass

        def _target_pos(self) -> QPoint:
            return QPoint(0, 0)

    def tearDown(self) -> None:
        instance = self.Overlay._active_instance
        self.Overlay._active_instance = None
        if instance is not None:
            delete_now(instance)

    def test_closing_forgets_a_deleted_overlay_but_not_a_programming_error(self) -> None:
        self.Overlay._active_instance = Mock(close=Mock(side_effect=RuntimeError("deleted")))
        self.Overlay.close_active()
        self.assertIsNone(self.Overlay._active_instance)

        self.Overlay._active_instance = Mock(close=Mock(side_effect=ZeroDivisionError("bug")))
        with self.assertRaises(ZeroDivisionError):
            self.Overlay.close_active()


class SearchBarLoggingTest(unittest.TestCase):
    def test_a_failing_result_click_is_logged(self) -> None:
        with patch("Kavitro_dev.dialog.PluginDialog.get_instance", return_value=object()), \
                patch(
                    "Kavitro_dev.utils.search.searchHelpers.SearchUIController.handle_search_result",
                    side_effect=RuntimeError("handler bug"),
                ), \
                patch.object(PythonFailLogger, "log") as log:
            MapCanvasSearchBar._open_result_in_plugin(Mock(), "property", "1", "Title")
        self.assertEqual(logged_events(log), ["map_search_result_open_failed"])
        self.assertEqual(log.call_args.kwargs["module"], "map")


class LayerProcessingLoggingTest(unittest.TestCase):
    def test_failing_visibility_step_is_logged_and_the_selection_count_still_returned(self) -> None:
        source = Mock(selectedFeatureCount=Mock(return_value=3))
        overlay = Mock()
        with patch.object(lps_module.processing, "run"), \
                patch.object(lps_module.MapHelpers, "ensure_layer_visible", side_effect=RuntimeError("no canvas")), \
                patch.object(PythonFailLogger, "log") as log:
            count = LayerProcessingService.select_features_intersecting_layer(source, overlay)
        self.assertEqual(count, 3)
        self.assertEqual(logged_events(log), ["layer_ensure_visible_failed"])
        self.assertEqual(log.call_args.kwargs["module"], "layers")

    def test_a_deleted_layer_counts_as_no_selection(self) -> None:
        layer = Mock()
        layer.isValid.return_value = True
        layer.selectedFeatureCount.side_effect = RuntimeError("deleted")
        self.assertIsNone(LayerProcessingService.buffer_selected_features(layer, distance=1.0, result_layer_name="x"))


class GpkgLayerExistsLoggingTest(unittest.TestCase):
    def test_an_unreadable_file_is_logged_and_reported_as_missing_layer(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "archive.gpkg")
            Path(path).write_bytes(b"not a geopackage")
            with patch.object(archive_module.ogr, "Open", side_effect=RuntimeError("locked")), \
                    patch.object(PythonFailLogger, "log") as log:
                self.assertFalse(archive_module.GPKGHelpers.gpkg_layer_exists(path, "layer"))
        self.assertEqual(logged_events(log), ["gpkg_layer_exists_check_failed"])
        self.assertEqual(log.call_args.kwargs["module"], "layers")

    def test_a_missing_layer_object_is_logged(self) -> None:
        datasource = Mock()
        datasource.GetLayerCount.return_value = 1
        datasource.GetLayerByIndex.return_value = None
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "archive.gpkg")
            Path(path).write_bytes(b"x")
            with patch.object(archive_module.ogr, "Open", return_value=datasource), \
                    patch.object(PythonFailLogger, "log") as log:
                self.assertFalse(archive_module.GPKGHelpers.gpkg_layer_exists(path, "layer"))
        self.assertEqual(logged_events(log), ["gpkg_layer_exists_check_failed"])


class PropertyTableManagerTest(QtCase):
    def build_table(self, feature) -> QTableView:
        table = QTableView()
        model = PropertyTableModel(["id", "address"], parent=table)
        model.set_rows([{"cadastral_id": "1", "feature": feature}])
        table.setModel(model)
        self.addCleanup(delete_now, table)
        return table

    def test_a_failing_normalizer_is_logged_and_the_raw_value_is_used(self) -> None:
        table = self.build_table({"muudet": "2024-01-02"})

        def broken_normalizer(_value):
            raise OverflowError("date out of range")

        with patch.object(PythonFailLogger, "log") as log:
            text = PropertyTableManager.get_payload_field_text(table, 0, 0, "muudet", normalizer=broken_normalizer)
        self.assertEqual(text, "2024-01-02")
        self.assertEqual(logged_events(log), ["property_payload_normalizer_failed"])
        self.assertEqual(log.call_args.kwargs["module"], "property")

    def test_a_missing_payload_field_reads_as_none(self) -> None:
        table = self.build_table({"muudet": "x"})
        self.assertIsNone(PropertyTableManager.get_payload_field_value(table, 0, 0, "absent"))

    def test_a_deleted_table_reads_as_empty_but_a_programming_error_is_not_hidden(self) -> None:
        deleted = Mock()
        deleted.model.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.assertEqual(PropertyTableManager.get_cell_text(deleted, 0, 0), "")
        self.assertIsNone(PropertyTableManager.get_cell_data(deleted, 0, 0))
        self.assertEqual(PropertyTableManager.row_count(deleted), 0)

        broken = Mock()
        broken.model.side_effect = ZeroDivisionError("bug")
        with self.assertRaises(ZeroDivisionError):
            PropertyTableManager.get_cell_text(broken, 0, 0)

    def test_a_non_numeric_row_reads_as_empty(self) -> None:
        table = self.build_table({"muudet": "x"})
        self.assertEqual(PropertyTableManager.get_cell_text(table, "abc", 0), "")


class WindowStateTest(QtCase):
    def test_a_deleted_window_is_not_minimized_and_not_alive(self) -> None:
        widget = QWidget()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertFalse(DialogCoordinator(None).is_minimized(widget))
        self.assertFalse(PopupHelpers.is_popup_alive(widget))

    def test_only_the_deleted_object_error_is_swallowed(self) -> None:
        coordinator = DialogCoordinator(None)
        gone = Mock(isWindow=Mock(return_value=True), isMinimized=Mock(side_effect=RuntimeError("deleted")))
        self.assertFalse(coordinator.is_minimized(gone))
        broken = Mock(isWindow=Mock(return_value=True), isMinimized=Mock(side_effect=ZeroDivisionError("bug")))
        with self.assertRaises(ZeroDivisionError):
            coordinator.is_minimized(broken)
        with self.assertRaises(ZeroDivisionError):
            PopupHelpers.is_popup_alive(Mock(isVisible=Mock(side_effect=ZeroDivisionError("bug"))))


class SessionUiControllerTest(unittest.TestCase):
    def test_a_failing_destroyed_hook_is_logged(self) -> None:
        dialog = Mock()
        dialog._session_listener = None
        dialog._has_shown = True
        dialog.destroyed.connect.side_effect = TypeError("bad slot")
        dialog.moduleManager.getActiveModuleName.return_value = "x"
        dialog.moduleManager.getActiveModuleInstance.return_value = None
        with patch.object(SessionManager, "register_listener"), \
                patch.object(SessionUIController, "refresh_login_ui"), \
                patch.object(PythonFailLogger, "log_exception") as log_exception:
            SessionUIController.after_show(dialog)
        self.assertEqual(logged_events(log_exception), ["session_listener_unregister_hook_failed"])
        self.assertEqual(log_exception.call_args.kwargs["module"], "auth")

    def test_login_parent_prefers_the_given_parent_then_the_main_window(self) -> None:
        parent = object()
        self.assertIs(SessionUIController._login_parent(parent), parent)
        main_window = object()
        with patch("qgis.utils.iface", SimpleNamespace(mainWindow=lambda: main_window)):
            self.assertIs(SessionUIController._login_parent(None), main_window)

    def test_login_parent_survives_a_deleted_main_window(self) -> None:
        def deleted():
            raise RuntimeError("wrapped C/C++ object has been deleted")

        with patch("qgis.utils.iface", SimpleNamespace(mainWindow=deleted)):
            self.assertIsNone(SessionUIController._login_parent(None))


class FilteredFeedLanguageTest(QtCase):
    def test_status_and_type_filters_share_the_module_language_manager(self) -> None:
        lang = LanguageManager("et")
        for patcher in (
            patch.object(APIClient, "send_query", side_effect=AssertionError("Unexpected API call")),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        with patch.object(ModuleManager, "getModuleSupports", return_value=(True, True, True, False)):
            module = ContractsModule(lang_manager=lang)
        self.addCleanup(delete_now, module)
        self.assertIs(module.status_filter._lang, lang)
        self.assertIs(module.type_filter._lang, lang)


if __name__ == "__main__":
    unittest.main()
