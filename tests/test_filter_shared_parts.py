"""What the filter widgets share: loading state, the request token lookup, the select-all box, the picker's parts."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QPointF, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.utils.FilterHelpers.FilterHelper import FilterHelper
from Kavitro_dev.utils.url_manager import ModuleSupports
from Kavitro_dev.widgets.Filters.BaseSingleFilterWidget import (
    BaseSingleFilterWidget,
    _SimplePickerControl,
    _SimplePickerPopup,
)
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget, _TypePickerControl, _TypePickerPopup
from Kavitro_dev.widgets.theme_manager import ThemeManager

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
                   "_is_widget_alive", "_start_async_load")
        groups = (
            (FILTER_WIDGETS, loading),
            (SELECT_ALL_WIDGETS, ("_set_all_cb_state", "_refresh_popup", "_sync_all_checkbox_state", "_apply_select_all")),
            (PICKER_CONTROLS, ("clicked", "set_summary", "mousePressEvent", "keyPressEvent", "__init__", "apply_style")),
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


class FakeCombo:
    """Rows of (value, check state); a row without a value is a placeholder."""

    def __init__(self, rows) -> None:
        self.rows = list(rows)

    def count(self) -> int:
        return len(self.rows)

    def itemData(self, index: int):  # noqa: N802
        return self.rows[index][0]

    def itemCheckState(self, index: int):  # noqa: N802
        return self.rows[index][1]

    def setItemCheckState(self, index: int, state) -> None:  # noqa: N802
        self.rows[index] = (self.rows[index][0], state)


class FakeComboWithActions(FakeCombo):
    def __init__(self, rows) -> None:
        super().__init__(rows)
        self.selectAllOptions = Mock()
        self.deselectAllOptions = Mock()


def combo_owner(combo) -> SimpleNamespace:
    """A stand-in that answers to the combo under the name each widget uses for it."""
    return SimpleNamespace(combo=combo, type_combo=combo, _options_combo=combo, _set_all_cb_state=Mock())


class SelectAllFromComboTest(unittest.TestCase):
    def state_for(self, widget, rows):
        owner = combo_owner(FakeCombo(rows))
        widget._sync_all_checkbox_state(owner)
        owner._set_all_cb_state.assert_called_once()
        return owner._set_all_cb_state.call_args.args[0]

    def test_box_shows_how_much_is_checked(self) -> None:
        checked, unchecked = ("a", Qt.Checked), ("b", Qt.Unchecked)
        for widget in SELECT_ALL_WIDGETS:
            for rows, expected in (([], Qt.Unchecked), ([unchecked], Qt.Unchecked), ([checked, checked], Qt.Checked),
                                   ([checked, unchecked], Qt.PartiallyChecked)):
                with self.subTest(widget=widget.__name__, rows=rows):
                    self.assertEqual(self.state_for(widget, rows), expected)

    def test_placeholder_rows_are_not_counted(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                self.assertEqual(self.state_for(widget, [(None, Qt.Unchecked), ("a", Qt.Checked)]), Qt.Checked)

    def test_combo_actions_are_used_when_it_has_them(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                combo = FakeComboWithActions([("a", Qt.Unchecked)])
                owner = combo_owner(combo)
                widget._apply_select_all(owner, True)
                combo.selectAllOptions.assert_called_once_with()
                widget._apply_select_all(owner, False)
                combo.deselectAllOptions.assert_called_once_with()
                self.assertEqual(combo.rows, [("a", Qt.Unchecked)])

    def test_without_combo_actions_each_real_row_is_set(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            for checked, state in ((True, Qt.Checked), (False, Qt.Unchecked)):
                with self.subTest(widget=widget.__name__, checked=checked):
                    other = Qt.Unchecked if checked else Qt.Checked
                    combo = FakeCombo([(None, other), ("a", other), ("b", other)])
                    widget._apply_select_all(combo_owner(combo), checked)
                    self.assertEqual(combo.rows, [(None, other), ("a", state), ("b", state)])


class PopupRefreshTest(unittest.TestCase):
    def test_open_popup_is_refreshed(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                popup = Mock()
                owner = SimpleNamespace(_popup=popup)
                widget._refresh_popup(owner)
                popup.refresh.assert_called_once_with()
                self.assertIs(owner._popup, popup)

    def test_closed_popup_needs_nothing(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                owner = SimpleNamespace(_popup=None)
                widget._refresh_popup(owner)
                self.assertIsNone(owner._popup)

    def test_deleted_popup_is_forgotten(self) -> None:
        for widget in SELECT_ALL_WIDGETS:
            with self.subTest(widget=widget.__name__):
                popup = Mock()
                popup.refresh.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
                owner = SimpleNamespace(_popup=popup)
                widget._refresh_popup(owner)
                self.assertIsNone(owner._popup)


class RealFilterCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.host = QWidget()
        self.addCleanup(self.delete_host)
        lang = LanguageManager("et")
        settings = Mock()
        settings.load_module_preference_ids.return_value = []
        self.status = StatusFilterWidget("contract", self.host, auto_load=False, lang_manager=lang, settings_logic=settings)
        self.types = TypeFilterWidget("contract", self.host, auto_load=False, settings_logic=settings)
        self.tags = TagsFilterWidget("contract", lang, self.host, auto_load=False, settings_logic=settings)
        self.widgets = (self.status, self.types, self.tags)

    def delete_host(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class FilterLoadResponseTest(RealFilterCase):
    def test_select_all_works_on_the_combo_holding_the_options(self) -> None:
        self.assertIs(self.tags._options_combo, self.tags.combo)
        self.assertIs(self.types._options_combo, self.types.type_combo)

    def finished_signal(self, widget) -> Mock:
        finished = Mock()
        widget.loadFinished.connect(finished)
        return finished

    def test_current_response_finishes_the_load(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                finished = self.finished_signal(widget)
                widget._load_request_id = 4
                widget._handle_load_success([], None, 4)
                finished.assert_called_once_with(True)
                self.assertTrue(widget.is_loaded())
                finished.reset_mock()
                widget._handle_load_error("katki", None, 4)
                finished.assert_called_once_with(False)
                self.assertFalse(widget.is_loaded())

    def test_answer_to_an_older_request_is_ignored(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                finished = self.finished_signal(widget)
                widget._load_request_id = 4
                widget._handle_load_success([], None, 3)
                widget._handle_load_error("katki", None, 3)
                finished.assert_not_called()
                self.assertFalse(widget.is_loaded())

    def test_answer_for_a_stale_token_is_ignored(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                finished = self.finished_signal(widget)
                widget._load_request_id = 4
                widget._is_token_active = lambda _token: False
                widget._handle_load_success([], 9, 4)
                widget._handle_load_error("katki", 9, 4)
                finished.assert_not_called()

    def test_answer_after_the_widget_is_gone_is_ignored(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                finished = self.finished_signal(widget)
                widget._load_request_id = 4
                widget._is_widget_alive = lambda: False
                widget._handle_load_success([], None, 4)
                widget._handle_load_error("katki", None, 4)
                finished.assert_not_called()


class FilterAsyncLoadTest(RealFilterCase):
    def start(self, widget):
        widget._load_request_id = 9
        widget._current_token = lambda: 4
        widget._handle_load_success = Mock()
        widget._handle_load_error = Mock()
        home = sys.modules[type(widget)._start_async_load.__module__]
        with patch.object(home, "FunctionWorker") as worker_class, patch.object(
            home, "start_worker", return_value="thread"
        ) as start_worker, patch.object(FilterHelper, "cancel_pending_load") as cancel:
            widget._start_async_load()
        return worker_class, start_worker, cancel

    def test_earlier_load_is_cancelled_without_a_new_request_number(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                _worker_class, _start, cancel = self.start(widget)
                cancel.assert_called_once_with(widget, invalidate_request=False)
                self.assertEqual(widget._load_request_id, 9)

    def test_worker_is_started_and_kept(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                worker_class, start, _cancel = self.start(widget)
                start.assert_called_once_with(worker_class.return_value, on_thread_finished=widget._cleanup_worker)
                self.assertIs(widget._worker, worker_class.return_value)
                self.assertEqual(widget._worker_thread, "thread")

    def test_answers_carry_the_token_and_request_of_their_start(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                worker_class, _start, _cancel = self.start(widget)
                worker = worker_class.return_value
                widget._load_request_id = 10
                worker.finished.connect.call_args.args[0]("vastus")
                worker.error.connect.call_args.args[0]("viga")
                widget._handle_load_success.assert_called_once_with("vastus", 4, 9)
                widget._handle_load_error.assert_called_once_with("viga", 4, 9)

    def test_each_filter_asks_for_its_own_options(self) -> None:
        with patch.object(FilterHelper, "get_filter_edges_by_key_and_module", return_value="servast") as edges, patch.object(
            APIModuleActions, "get_module_status_options", return_value="olekud"
        ) as statuses:
            for widget, expected, key in ((self.tags, "servast", ModuleSupports.TAGS.value),
                                          (self.types, "servast", ModuleSupports.TYPES.value),
                                          (self.status, "olekud", None)):
                with self.subTest(widget=type(widget).__name__):
                    edges.reset_mock()
                    statuses.reset_mock()
                    worker_class, _start, _cancel = self.start(widget)
                    self.assertEqual(worker_class.call_args.args[0](), expected)
                    if key is None:
                        statuses.assert_called_once_with("contract")
                        edges.assert_not_called()
                    else:
                        edges.assert_called_once_with(key, "contract")
                        statuses.assert_not_called()


class PickerControlTest(unittest.TestCase):
    NAMES = {_SimplePickerControl: ("SimplePickerControl", "SimplePickerSummary"),
             _TypePickerControl: ("TypePickerControl", "TypePickerSummary")}

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def build(self, control_class):
        control = control_class()
        self.addCleanup(control.deleteLater)
        clicked = Mock()
        control.clicked.connect(clicked)
        return control, clicked

    def test_control_is_built_under_its_own_names(self) -> None:
        for control_class, (control_name, summary_name) in self.NAMES.items():
            with self.subTest(control=control_class.__name__):
                control, _clicked = self.build(control_class)
                self.assertEqual(control.objectName(), control_name)
                self.assertEqual(control._label.objectName(), summary_name)
                self.assertEqual(control.cursor().shape(), Qt.PointingHandCursor)
                self.assertEqual(control.focusPolicy(), Qt.StrongFocus)
                self.assertTrue(control._label.testAttribute(Qt.WA_TransparentForMouseEvents))
                self.assertEqual(control.layout().count(), 2)

    def test_style_targets_its_own_names_in_the_current_theme(self) -> None:
        for control_class, (control_name, summary_name) in self.NAMES.items():
            for theme, background, accent, text in (("dark", "#303a42", "#1f5d5c", "#c5c5d2"),
                                                    ("light", "#ffffff", "#2188ff", "#24292e")):
                with self.subTest(control=control_class.__name__, theme=theme), patch.object(
                    ThemeManager, "effective_theme", return_value=theme
                ):
                    control, _clicked = self.build(control_class)
                    style = control.styleSheet()
                    self.assertIn(f"QFrame#{control_name} {{background: {background};", style)
                    self.assertIn(f"QFrame#{control_name}:hover, QFrame#{control_name}:focus {{", style)
                    self.assertIn(f"border-color: {accent};", style)
                    self.assertIn(f"QLabel#{summary_name} {{color: {text};", style)

    def test_applying_the_style_again_follows_a_theme_change(self) -> None:
        for control_class in self.NAMES:
            with self.subTest(control=control_class.__name__):
                with patch.object(ThemeManager, "effective_theme", return_value="dark"):
                    control, _clicked = self.build(control_class)
                with patch.object(ThemeManager, "effective_theme", return_value="light"):
                    control.apply_style()
                self.assertIn("background: #ffffff;", control.styleSheet())
                self.assertNotIn("#303a42", control.styleSheet())

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
