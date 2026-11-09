"""What the filter widgets share: loading state, the request token lookup, the select-all box, the picker's parts."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QPointF, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from Kavitro_dev.widgets.Filters.BaseSingleFilterWidget import (
    BaseSingleFilterWidget,
    _SimplePickerControl,
    _SimplePickerPopup,
)
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget, _TypePickerControl, _TypePickerPopup

FILTER_WIDGETS = (BaseSingleFilterWidget, StatusFilterWidget, TypeFilterWidget)
SELECT_ALL_WIDGETS = (BaseSingleFilterWidget, TypeFilterWidget)
PICKER_CONTROLS = (_SimplePickerControl, _TypePickerControl)
PICKER_POPUPS = (_SimplePickerPopup, _TypePickerPopup)


def alive(**fields) -> SimpleNamespace:
    return SimpleNamespace(_is_widget_alive=lambda: True, **fields)


def dead(**fields) -> SimpleNamespace:
    return SimpleNamespace(_is_widget_alive=lambda: False, **fields)


def node(parent=None, **fields) -> SimpleNamespace:
    """A stand-in for a Qt parent: only its place in the tree and the given attributes."""
    return SimpleNamespace(parent=lambda: parent, **fields)


def gone():
    raise RuntimeError("wrapped C/C++ object has been deleted")


class SharedPartsStayInOnePlaceTest(unittest.TestCase):
    def test_no_filter_class_carries_its_own_copy(self) -> None:
        loading = ("ensure_loaded", "is_loaded", "is_loading", "_cleanup_worker", "_current_token", "_is_token_active",
                   "_is_widget_alive")
        groups = (
            (FILTER_WIDGETS, loading),
            (SELECT_ALL_WIDGETS, ("_set_all_cb_state",)),
            (PICKER_CONTROLS, ("clicked", "set_summary", "mousePressEvent", "keyPressEvent")),
            (PICKER_POPUPS, ("_clear_layout",)),
        )
        for classes, names in groups:
            for owner in classes:
                for name in names:
                    with self.subTest(owner=owner.__name__, part=name):
                        self.assertNotIn(name, vars(owner))


class FilterLoadStateTest(unittest.TestCase):
    def test_ensure_loaded_reloads_only_when_nothing_is_loaded(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                empty, loaded = SimpleNamespace(_loaded=False, reload=Mock()), SimpleNamespace(_loaded=True, reload=Mock())
                widget.ensure_loaded(empty)
                widget.ensure_loaded(loaded)
                empty.reload.assert_called_once_with()
                loaded.reload.assert_not_called()

    def test_load_state_is_reported(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertTrue(widget.is_loaded(SimpleNamespace(_loaded=True)))
                self.assertFalse(widget.is_loaded(SimpleNamespace(_loaded=False)))
                self.assertTrue(widget.is_loading(SimpleNamespace(_worker_thread=object())))
                self.assertFalse(widget.is_loading(SimpleNamespace(_worker_thread=None)))

    def test_cleanup_forgets_the_finished_worker(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                fake = alive(_worker=object(), _worker_thread=object())
                widget._cleanup_worker(fake)
                self.assertIsNone(fake._worker)
                self.assertIsNone(fake._worker_thread)

    def test_cleanup_leaves_a_deleted_widget_alone(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                worker, thread = object(), object()
                fake = dead(_worker=worker, _worker_thread=thread)
                widget._cleanup_worker(fake)
                self.assertIs(fake._worker, worker)
                self.assertIs(fake._worker_thread, thread)


class FilterTokenLookupTest(unittest.TestCase):
    def test_token_comes_from_the_nearest_owner(self) -> None:
        outer = node(_active_token=1)
        inner = node(outer, _active_token=2)
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertEqual(widget._current_token(alive(parent=lambda: node(inner))), 2)

    def test_without_an_owner_there_is_no_token(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertIsNone(widget._current_token(alive(parent=lambda: node(node()))))
                self.assertIsNone(widget._current_token(alive(parent=lambda: None)))

    def test_deleted_widget_has_no_token(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertIsNone(widget._current_token(dead(parent=lambda: node(_active_token=1))))
                self.assertIsNone(widget._current_token(alive(parent=gone)))

    def test_request_without_a_token_is_always_current(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertTrue(widget._is_token_active(alive(parent=gone), None))

    def test_deleted_widget_or_parent_is_never_current(self) -> None:
        owner = node(is_token_active=lambda token: True)
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertFalse(widget._is_token_active(dead(parent=lambda: owner), 3))
                self.assertFalse(widget._is_token_active(dead(parent=lambda: owner), None))
                self.assertFalse(widget._is_token_active(alive(parent=gone), 3))

    def test_nearest_owner_decides_and_a_failing_one_means_stale(self) -> None:
        def failing(_token):
            raise RuntimeError("owner closing")

        outer = node(is_token_active=lambda token: True)
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                refusing = node(outer, is_token_active=lambda token: False)
                self.assertFalse(widget._is_token_active(alive(parent=lambda: refusing), 3))
                self.assertFalse(widget._is_token_active(alive(parent=lambda: node(is_token_active=failing)), 3))


class FilterWidgetAliveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_live_widget_is_alive_and_deleted_one_is_not(self) -> None:
        for widget in FILTER_WIDGETS:
            with self.subTest(widget=widget.__name__):
                target = QWidget()
                self.assertTrue(widget._is_widget_alive(target))
                sip.delete(target)
                self.assertFalse(widget._is_widget_alive(target))


class SelectAllStateTest(unittest.TestCase):
    @staticmethod
    def fake() -> SimpleNamespace:
        return SimpleNamespace(all_cb=Mock(), _suppress_all_cb=False)

    def test_box_is_set_with_its_signal_handling_suppressed(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                fake, during = self.fake(), []
                fake.all_cb.setCheckState.side_effect = lambda state: during.append(fake._suppress_all_cb)
                widget._set_all_cb_state(fake, Qt.Checked)
                fake.all_cb.setCheckState.assert_called_once_with(Qt.Checked)
                fake.all_cb.setEnabled.assert_not_called()
                self.assertEqual(during, [True])
                self.assertFalse(fake._suppress_all_cb)

    def test_enabled_state_is_applied_when_given(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            for enabled in (True, False):
                with self.subTest(widget=widget.__name__, enabled=enabled):
                    fake = self.fake()
                    widget._set_all_cb_state(fake, Qt.Unchecked, enabled=enabled)
                    fake.all_cb.setEnabled.assert_called_once_with(enabled)

    def test_suppression_ends_even_when_the_box_fails(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                fake = self.fake()
                fake.all_cb.setCheckState.side_effect = RuntimeError("deleted")
                with self.assertRaises(RuntimeError):
                    widget._set_all_cb_state(fake, Qt.Checked)
                self.assertFalse(fake._suppress_all_cb)


class PickerControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def build(self, control_class):
        control = control_class()
        self.addCleanup(control.deleteLater)
        clicked = Mock()
        control.clicked.connect(clicked)
        return control, clicked

    @staticmethod
    def press(button) -> QMouseEvent:
        event = QMouseEvent(QEvent.MouseButtonPress, QPointF(1, 1), button, button, Qt.NoModifier)
        event.ignore()
        return event

    @staticmethod
    def key(code) -> QKeyEvent:
        event = QKeyEvent(QEvent.KeyPress, code, Qt.NoModifier)
        event.ignore()
        return event

    def test_summary_text_is_shown(self) -> None:
        for control_class in PICKER_CONTROLS:
            with self.subTest(control=control_class.__name__):
                control, _clicked = self.build(control_class)
                control.set_summary("Kolm valitud")
                self.assertEqual(control._label.text(), "Kolm valitud")

    def test_left_click_opens_and_is_consumed(self) -> None:
        for control_class in PICKER_CONTROLS:
            with self.subTest(control=control_class.__name__):
                control, clicked = self.build(control_class)
                event = self.press(Qt.LeftButton)
                control.mousePressEvent(event)
                clicked.assert_called_once()
                self.assertTrue(event.isAccepted())

    def test_other_button_or_disabled_control_passes_the_click_on(self) -> None:
        for control_class in PICKER_CONTROLS:
            with self.subTest(control=control_class.__name__):
                control, clicked = self.build(control_class)
                right = self.press(Qt.RightButton)
                control.mousePressEvent(right)
                control.setEnabled(False)
                left = self.press(Qt.LeftButton)
                control.mousePressEvent(left)
                clicked.assert_not_called()
                self.assertFalse(right.isAccepted())
                self.assertFalse(left.isAccepted())

    def test_return_enter_and_space_open(self) -> None:
        for control_class in PICKER_CONTROLS:
            for code in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                with self.subTest(control=control_class.__name__, key=code):
                    control, clicked = self.build(control_class)
                    event = self.key(code)
                    control.keyPressEvent(event)
                    clicked.assert_called_once()
                    self.assertTrue(event.isAccepted())

    def test_other_key_is_passed_on(self) -> None:
        for control_class in PICKER_CONTROLS:
            with self.subTest(control=control_class.__name__):
                control, clicked = self.build(control_class)
                event = self.key(Qt.Key_A)
                control.keyPressEvent(event)
                clicked.assert_not_called()
                self.assertFalse(event.isAccepted())


class PickerPopupClearLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_rows_and_nested_layouts_are_emptied_and_widgets_deleted(self) -> None:
        for popup in PICKER_POPUPS:
            with self.subTest(popup=popup.__name__):
                host = QWidget()
                self.addCleanup(host.deleteLater)
                layout = QVBoxLayout(host)
                nested = QHBoxLayout()
                top, inner = QLabel("üleval", host), QLabel("sees", host)
                layout.addWidget(top)
                nested.addWidget(inner)
                layout.addLayout(nested)

                fake = SimpleNamespace()
                fake._clear_layout = lambda target: popup._clear_layout(fake, target)
                popup._clear_layout(fake, layout)
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

                self.assertEqual(layout.count(), 0)
                self.assertEqual(nested.count(), 0)
                self.assertTrue(sip.isdeleted(top))
                self.assertTrue(sip.isdeleted(inner))


if __name__ == "__main__":
    unittest.main()
