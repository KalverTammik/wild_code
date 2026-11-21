"""Map canvas overlays: a failing on_ready keeps the live overlay, a failing result click is shown to the user."""
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

from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtWidgets import QLineEdit, QListWidgetItem
from qgis.core import QgsApplication

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.utils.map_canvas_glass_overlay import MapCanvasGlassOverlayBase
from Kavitro_dev.utils.map_canvas_search_bar import MapCanvasSearchBar
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.widgets.SearchResultsWidget import SearchResultsWidget


def delete_now(widget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def logged_events(log_mock) -> list[str]:
    return [call.kwargs.get("event") or (call.args[0] if call.args else None) for call in log_mock.call_args_list]


class OverlayCase(unittest.TestCase):
    overlay_cls = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        # A regression must never open a modal window during the suite.
        dialog_patch = patch.object(ModernMessageDialog, "_create_dialog", side_effect=AssertionError("modal opened"))
        dialog_patch.start()
        self.addCleanup(dialog_patch.stop)
        self.extra_widgets = []

    def tearDown(self) -> None:
        instance = self.overlay_cls._active_instance
        self.overlay_cls._active_instance = None
        for widget in [instance, *self.extra_widgets]:
            if widget is not None and not isinstance(widget, Mock):
                delete_now(widget)


class Overlay(MapCanvasGlassOverlayBase):
    SIZE = (10, 10)

    def __init__(self) -> None:
        super().__init__(object_name="TestOverlay")
        self._finish_init()

    def _build_ui(self) -> None:
        pass

    def _target_pos(self) -> QPoint:
        return QPoint(0, 0)


class OverlayOnReadyTest(OverlayCase):
    overlay_cls = Overlay

    def test_a_failing_on_ready_keeps_the_reused_overlay(self) -> None:
        Overlay.show_for_session()
        first = Overlay._active_instance

        with patch.object(PythonFailLogger, "log") as log:
            Overlay.show_for_session(on_ready=Mock(side_effect=TypeError("callback bug")))

        self.assertIs(Overlay._active_instance, first)
        self.assertTrue(first.isVisible())
        self.assertEqual(logged_events(log), ["map_overlay_on_ready_failed"])
        self.assertEqual(log.call_args.kwargs["module"], "map")

    def test_a_failing_on_ready_still_shows_a_new_overlay(self) -> None:
        with patch.object(PythonFailLogger, "log") as log:
            Overlay.show_for_session(on_ready=Mock(side_effect=TypeError("callback bug")))

        bar = Overlay._active_instance
        self.assertIsNotNone(bar)
        self.assertTrue(bar.isVisible())
        self.assertEqual(logged_events(log), ["map_overlay_on_ready_failed"])

        # The next call reuses it instead of building a second overlay.
        on_ready = Mock()
        Overlay.show_for_session(on_ready=on_ready)
        self.assertIs(Overlay._active_instance, bar)
        on_ready.assert_called_once_with(bar)

    def test_a_deleted_overlay_is_replaced_and_on_ready_gets_the_new_one(self) -> None:
        Overlay._active_instance = Mock(raise_=Mock(side_effect=RuntimeError("wrapped C/C++ object has been deleted")))
        on_ready = Mock()

        with patch.object(PythonFailLogger, "log") as log:
            Overlay.show_for_session(on_ready=on_ready)

        fresh = Overlay._active_instance
        self.assertIsInstance(fresh, Overlay)
        on_ready.assert_called_once_with(fresh)
        self.assertEqual(logged_events(log), ["map_overlay_reuse_failed"])


class SearchBarFailureTest(OverlayCase):
    overlay_cls = MapCanvasSearchBar

    def test_a_failing_wire_keeps_the_search_bar(self) -> None:
        MapCanvasSearchBar.show_for_session()
        first = MapCanvasSearchBar._active_instance

        broken_signal = Mock(connect=Mock(side_effect=TypeError("connect bug")))
        with patch.object(MapCanvasSearchBar, "resultClicked", broken_signal), \
                patch.object(PythonFailLogger, "log") as log:
            MapCanvasSearchBar.show_for_session(result_handler=lambda *_: None)

        self.assertIs(MapCanvasSearchBar._active_instance, first)
        self.assertEqual(logged_events(log), ["map_overlay_on_ready_failed"])

    def test_a_failing_result_click_is_logged_and_shown_in_the_results_popup(self) -> None:
        MapCanvasSearchBar.show_for_session()
        bar = MapCanvasSearchBar._active_instance
        results = bar.search_results_widget
        item = QListWidgetItem("Title")
        item.setData(Qt.UserRole, {"type": "result", "module": "PROPERTIES", "id": "1", "title": "Title"})

        with patch("Kavitro_dev.dialog.PluginDialog.get_instance", return_value=object()), \
                patch(
                    "Kavitro_dev.utils.search.searchHelpers.SearchUIController.handle_search_result",
                    side_effect=RuntimeError("handler bug"),
                ), \
                patch.object(PythonFailLogger, "log") as log:
            results._on_item_clicked(item)  # real click path: emits, then hides the popup
            QCoreApplication.processEvents()

        self.assertEqual(logged_events(log), ["map_search_result_open_failed"])
        self.assertTrue(results.isVisible())
        self.assertEqual(results.resultsList.count(), 1)
        self.assertEqual(
            results.resultsList.item(0).text(),
            LanguageManager().translate(TranslationKeys.SEARCH_RESULT_OPEN_FAILED),
        )

    def test_the_deferred_message_is_skipped_once_the_bar_is_gone(self) -> None:
        class DeletedBar:
            _lang = LanguageManager()
            search_edit = None

            @property
            def search_results_widget(self):
                raise RuntimeError("wrapped C/C++ object has been deleted")

        MapCanvasSearchBar._show_result_open_failed(DeletedBar())

    def test_refocus_after_the_search_field_is_gone_does_not_raise(self) -> None:
        # Before the guard this aborted the whole test process (exception inside a Qt timer callback).
        field = QLineEdit()
        SearchResultsWidget._refocus_search_field(SearchResultsWidget, field)
        delete_now(field)
        QCoreApplication.processEvents()

        with patch.object(QLineEdit, "setFocus", side_effect=RuntimeError("wrapped C/C++ object has been deleted")):
            SearchResultsWidget._set_focus_if_alive(QLineEdit())


if __name__ == "__main__":
    unittest.main()
