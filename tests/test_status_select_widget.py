"""Characterization tests for StatusSelectWidget and StatusMultiSelectWidget, written against
the code before the shared parts of the two controls and their popups were merged."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, Qt
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QFrame, QLabel, QPushButton, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.ui.theme_manager import Theme, ThemeManager
from Kavitro_dev.widgets.status_select_widget import StatusMultiSelectWidget, StatusSelectWidget

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

OPTIONS = [
    {"id": "1", "name": "Uus", "color": "4fbf6b", "type": "open", "description": "Algne"},
    {"id": "2", "label": "Töös", "color": "#3366FF", "type": "OPEN", "isDefault": True},
    {"id": "3", "name": "Valmis", "color": "zzzzzz", "type": "CLOSED"},
    {"id": "4", "name": "Muu", "color": "", "type": "ARCHIVED"},
    {"id": "", "name": "No id"},
    {"id": "1", "name": "Duplicate"},
]


class _WidgetTest(unittest.TestCase):
    def setUp(self):
        theme = patch.object(ThemeManager, "effective_theme", return_value=Theme.LIGHT)
        theme.start()
        self.addCleanup(theme.stop)
        translate = patch.object(LanguageManager, "translate", lambda self, key: f"T:{key}")
        translate.start()
        self.addCleanup(translate.stop)
        self.host = QWidget()
        self.host.resize(300, 100)
        self.addCleanup(self._dispose)

    def _dispose(self):
        for widget in QCoreApplication.instance().topLevelWidgets():
            if widget.objectName() in ("StatusSelectPopup", "StatusMultiSelectPopup"):
                widget.close()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def rows(self, popup):
        return popup.findChildren(QFrame, "StatusSelectOptionRow")

    def row_labels(self, popup):
        return [row.findChild(QLabel, "StatusSelectOptionLabel").text() for row in self.rows(popup)]

    def sections(self, popup):
        return [label.text() for label in popup.findChildren(QLabel, "StatusSelectSectionLabel")]

    def marked(self, popup):
        return [
            row.findChild(QLabel, "StatusSelectOptionLabel").text()
            for row in self.rows(popup)
            if not row.findChild(QFrame, "StatusSelectSelectedMarker").isHidden()
        ]


class StatusSelectWidgetTest(_WidgetTest):
    def make(self, **kwargs):
        widget = StatusSelectWidget(self.host, **kwargs)
        widget.resize(260, 30)
        return widget

    def test_placeholder_and_disabled_without_options(self):
        widget = self.make()
        self.assertEqual(widget._label.text(), "T:Select")
        self.assertEqual(self.make(placeholder="Pick").currentText(), "")
        self.assertEqual(self.make(placeholder="Pick")._label.text(), "Pick")
        widget.set_options([])
        self.assertFalse(widget.isEnabled())
        self.assertEqual(widget.count(), 0)

    def test_options_are_normalized_deduplicated_and_enabled(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        self.assertTrue(widget.isEnabled())
        self.assertEqual(widget.count(), 4)
        self.assertEqual(
            [(o["id"], o["name"], o["label"], o["color"], o["type"]) for o in widget._options],
            [("1", "Uus", "Uus", "#4FBF6B", "OPEN"), ("2", "Töös", "Töös", "#3366FF", "OPEN"),
             ("3", "Valmis", "Valmis", "#CCCCCC", "CLOSED"), ("4", "Muu", "Muu", "#CCCCCC", "ARCHIVED")],
        )

    def test_initial_selection_prefers_the_asked_then_the_default_then_the_first(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_id=" 3 ")
        self.assertEqual(widget.currentData(), "3")
        widget.set_options(OPTIONS, selected_id="missing")
        self.assertEqual(widget.current_status_id(), "2")
        widget.set_options([{"id": "a", "name": "A"}, {"id": "b", "name": "B"}])
        self.assertEqual(widget.current_status_id(), "a")

    def test_current_values_label_and_tooltip(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_id="1")
        self.assertEqual((widget.currentText(), widget.current_status_label(), widget.current_status_color()),
                         ("Uus", "Uus", "#4FBF6B"))
        self.assertEqual(widget.current_option()["description"], "Algne")
        self.assertEqual((widget._label.text(), widget.toolTip(), widget._control.toolTip()), ("Uus", "Algne", "Algne"))
        widget.set_current_status_id("2")
        self.assertEqual(widget.toolTip(), "Töös")
        self.assertIn("#3366FF", widget._dot.styleSheet())

    def test_set_current_status_id(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_id="1")
        changed = Mock()
        widget.currentChanged.connect(changed)
        self.assertFalse(widget.set_current_status_id("9"))
        self.assertTrue(widget.set_current_status_id("1"))
        changed.assert_not_called()
        self.assertTrue(widget.set_current_status_id("3", emit=False))
        changed.assert_not_called()
        self.assertTrue(widget.set_current_status_id("2"))
        changed.assert_called_once_with("2", "Töös")
        self.assertTrue(widget.set_current_status_id(""))
        self.assertIsNone(widget.current_option())
        self.assertEqual(widget._label.text(), "T:Select")

    def test_popup_groups_marks_and_picks(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_id="2")
        changed = Mock()
        widget.currentChanged.connect(changed)
        widget._toggle_popup()
        popup = widget._popup
        self.assertEqual(popup.objectName(), "StatusSelectPopup")
        self.assertEqual(self.sections(popup), ["T:Status group open", "T:Status group closed", "ARCHIVED"])
        self.assertEqual(self.row_labels(popup), ["Uus", "Töös", "Valmis", "Muu"])
        self.assertEqual(self.marked(popup), ["Töös"])
        self.assertEqual(self.rows(popup)[0].toolTip(), "Algne")
        self.assertGreaterEqual(popup.findChild(QFrame, "StatusSelectPopupFrame").minimumWidth(), 260)
        QTest.mouseClick(self.rows(popup)[2], Qt.MouseButton.LeftButton)
        self.assertIsNone(widget._popup)
        changed.assert_called_once_with("3", "Valmis")

    def test_toggle_closes_an_open_popup_and_disabled_opens_none(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        widget._toggle_popup()
        self.assertTrue(widget._popup.isVisible())
        widget._toggle_popup()
        self.assertIsNone(widget._popup)
        widget.setEnabled(False)
        widget._toggle_popup()
        self.assertIsNone(widget._popup)
        widget.clear()
        self.assertEqual((widget.count(), widget.current_status_id()), (0, ""))

    def test_control_click_and_keyboard_open_the_popup(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        QTest.mouseClick(widget._control, Qt.MouseButton.LeftButton)
        self.assertIsNotNone(widget._popup)
        widget._close_popup()
        QTest.keyClick(widget._control, Qt.Key.Key_Space)
        self.assertIsNotNone(widget._popup)

    def test_control_style(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_id="1")
        widget.set_control_height(30)
        style = widget._control.styleSheet()
        self.assertIn("min-height: 28px;", style)
        self.assertIn("0.12)", style)
        self.assertEqual(widget._control.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        widget.setEnabled(False)
        self.assertIn("background-color: #f2f4f7;", widget._control.styleSheet())
        self.assertEqual(widget._control.cursor().shape(), Qt.CursorShape.ArrowCursor)
        widget.set_current_status_id("")
        widget.setEnabled(True)
        self.assertIn("background-color: #ffffff;", widget._control.styleSheet())
        self.assertRegex(widget._control.styleSheet(), r"border: 1px solid rgba\(\d+,\d+,\d+,0\.48\);")

    def test_dark_theme_colours(self):
        with patch.object(ThemeManager, "effective_theme", return_value=Theme.DARK):
            widget = self.make()
            widget.set_options(OPTIONS)
            widget.set_current_status_id("")
            widget.retheme()
            self.assertIn("#27313a", widget._control.styleSheet())
            self.assertIn("#f1f5f9", widget._label.styleSheet())
            widget._toggle_popup()
            frame = widget._popup.findChild(QFrame, "StatusSelectPopupFrame")
            self.assertIn("#242b33", frame.styleSheet())
            label = self.rows(widget._popup)[0].findChild(QLabel, "StatusSelectOptionLabel")
            self.assertIn("#f5f7fa", label.styleSheet())


class StatusMultiSelectWidgetTest(_WidgetTest):
    def make(self, **kwargs):
        widget = StatusMultiSelectWidget(self.host, **kwargs)
        widget.resize(260, 30)
        return widget

    def test_size_and_placeholder(self):
        widget = self.make()
        self.assertEqual((widget.minimumWidth(), widget.maximumWidth()), (210, 360))
        self.assertEqual(widget._label.text(), "T:Select")
        self.assertTrue(widget._dot.isHidden())

    def test_selection_is_filtered_deduplicated_and_ordered(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_ids=["3", "x", "1", "3", " "])
        self.assertEqual(widget.selected_ids(), ["1", "3"])
        self.assertEqual(widget.selected_texts(), ["Uus", "Valmis"])
        self.assertEqual(widget._label.text(), "Uus, Valmis")
        self.assertEqual(widget.toolTip(), "Uus, Valmis")
        self.assertFalse(widget._dot.isHidden())
        self.assertIn("#4FBF6B", widget._dot.styleSheet())

    def test_without_options_the_asked_ids_are_kept(self):
        widget = self.make()
        widget.set_selected_ids(["5", "5", "6"], emit=False)
        self.assertEqual(widget.selected_ids(), ["5", "6"])
        self.assertEqual(widget.selected_texts(), [])

    def test_set_selected_ids_emits_unless_told_not_to(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        changed = Mock()
        widget.selectionChanged.connect(changed)
        widget.set_selected_ids(["2"], emit=False)
        changed.assert_not_called()
        widget.set_selected_ids(["4", "2"])
        changed.assert_called_once_with(["Töös", "Muu"], ["2", "4"])

    def test_loading_and_error_texts_disable_and_clear(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_ids=["1"])
        widget.set_loading("Loading…")
        self.assertEqual((widget._label.text(), widget.isEnabled(), widget.count(), widget.selected_ids()),
                         ("Loading…", False, 0, []))
        widget.set_error("")
        self.assertEqual(widget._label.text(), "T:Select")
        widget.set_error("Failed")
        self.assertEqual(widget._label.text(), "Failed")
        self.assertIn("background-color: #f2f4f7;", widget._control.styleSheet())
        widget.set_options(OPTIONS)
        self.assertEqual(widget._label.text(), "T:Select")
        self.assertTrue(widget.isEnabled())

    def test_popup_actions_and_rows(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_ids=["2"])
        changed = Mock()
        widget.selectionChanged.connect(changed)
        widget._toggle_popup()
        popup = widget._popup
        self.assertEqual(popup.objectName(), "StatusMultiSelectPopup")
        self.assertEqual(self.sections(popup), ["T:Status group open", "T:Status group closed", "ARCHIVED"])
        self.assertEqual(self.marked(popup), ["Töös"])
        select_all, clear = popup.findChildren(QPushButton, "StatusSelectActionButton")
        self.assertEqual((select_all.text(), clear.text()), ("T:Select All", "T:Clear Selection"))
        self.assertEqual((select_all.isEnabled(), clear.isEnabled()), (True, True))

        QTest.mouseClick(self.rows(popup)[0], Qt.MouseButton.LeftButton)
        self.assertEqual(changed.call_args.args, (["Uus", "Töös"], ["1", "2"]))
        self.assertEqual(self.marked(popup), ["Uus", "Töös"])
        self.assertIs(widget._popup, popup)

        select_all.click()
        self.assertEqual(widget.selected_ids(), ["1", "2", "3", "4"])
        self.assertFalse(select_all.isEnabled())
        clear.click()
        self.assertEqual(changed.call_args.args, ([], []))
        self.assertEqual((select_all.isEnabled(), clear.isEnabled()), (True, False))
        count = changed.call_count
        popup._clear_selection()
        self.assertEqual(changed.call_count, count)
        self.assertEqual(widget._label.text(), "T:Select")

    def test_toggle_a_row_off(self):
        widget = self.make()
        widget.set_options(OPTIONS, selected_ids=["1", "3"])
        widget._toggle_popup()
        QTest.mouseClick(self.rows(widget._popup)[2], Qt.MouseButton.LeftButton)
        self.assertEqual(widget.selected_ids(), ["1"])

    def test_setting_ids_with_an_open_popup_rebuilds_it(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        widget._toggle_popup()
        first = widget._popup
        widget.set_selected_ids(["3"], emit=False)
        self.assertIsNot(widget._popup, first)
        self.assertEqual(self.marked(widget._popup), ["Valmis"])
        widget._toggle_popup()
        self.assertIsNone(widget._popup)

    def test_control_style_follows_the_selection(self):
        widget = self.make()
        widget.set_options(OPTIONS)
        style = widget._control.styleSheet()
        self.assertIn("border: 1px solid rgba(15,23,42,0.18);", style)
        self.assertIn("background-color: #ffffff;", style)
        self.assertIn("min-height: 24px;", style)
        widget.set_selected_ids(["1"], emit=False)
        self.assertNotIn("rgba(15,23,42,0.18)", widget._control.styleSheet())
        self.assertIn("0.12)", widget._control.styleSheet())
        widget.clear()
        self.assertFalse(widget.isEnabled() and widget.count())
        self.assertEqual(widget._label.text(), "T:Select")

    def test_dark_popup_buttons(self):
        with patch.object(ThemeManager, "effective_theme", return_value=Theme.DARK):
            widget = self.make()
            widget.set_options(OPTIONS)
            widget._toggle_popup()
            frame = widget._popup.findChild(QFrame, "StatusSelectPopupFrame")
            self.assertIn("#eef2f7", frame.styleSheet())
            self.assertIn("#242b33", frame.styleSheet())


if __name__ == "__main__":
    unittest.main()
