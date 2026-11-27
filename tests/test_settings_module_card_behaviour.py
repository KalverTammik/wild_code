"""Characterization tests for SettingsModuleCard, written against the code before it was split.

They patch dialogs and helpers on their own classes, not on the card module, so they keep
working when the card's methods move to other files.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, QPointF, Qt
from qgis.PyQt.QtGui import QFocusEvent, QMouseEvent
from qgis.PyQt.QtWidgets import QFileDialog, QPushButton, QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.constants.button_props import ButtonVariant
from Kavitro_dev.constants.module_names import ModuleSupports
from Kavitro_dev.constants.setting_placeholders import SettingDialogPlaceholders
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.Settings.cards.SettingsModuleCard import SettingsModuleCard
from Kavitro_dev.modules.projects.projects_entry import ProjectsTempLayerHelper
from Kavitro_dev.modules.works.works_entry import WorksTempLayerHelper
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.project_board_status_rules import ProjectBoardStatusRules

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()


class _Text(str):
    """A translated text that shows which format() arguments it got."""

    def format(self, *args, **kwargs):
        return f"{self}{sorted(kwargs.items())}"


def _translate(key):
    return _Text(f"T:{key}")


def _left_click():
    # A real mouse event: a bare QEvent of this type crashes Qt6.
    return QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(2, 2), QPointF(2, 2), Qt.MouseButton.LeftButton,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)


def _logic():
    logic = Mock()
    logic.get_module_layer_ids.return_value = {}
    logic.load_module_label_values.return_value = {}
    logic.load_module_preference_ids.return_value = []
    return logic


class _CardTest(unittest.TestCase):
    module = "works"
    card_kwargs: dict = {}

    def setUp(self):
        writes = patch("qgis.core.QgsSettings.setValue")
        writes.start()
        self.addCleanup(writes.stop)
        log = patch.object(PythonFailLogger, "log_exception")
        self.log = log.start()
        self.addCleanup(log.stop)
        self.logic = _logic()
        self.card = SettingsModuleCard(
            LanguageManager(language="en"), self.module, self.module.title(), logic=self.logic, **self.card_kwargs
        )
        self.real_translate = self.card.lang_manager.translate
        self.card.lang_manager.translate = _translate
        self.addCleanup(self._dispose)

    def _dispose(self):
        self.card.hide()
        self.card.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def patch(self, target, attribute, **kwargs):
        patcher = patch.object(target, attribute, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock


# --- temp layer flow -----------------------------------------------------------------


class _TempLayerFlow:
    """The same flow runs for works and projects; only the helper, keys and event differ."""

    module: str
    helper: type
    prefix: str
    event: str
    button_name: str
    variant: str

    def setUp(self):
        super().setUp()
        self.reference = Mock(name="reference_layer")
        self.resolve = self.patch(self.helper, "resolve_reference_layer", return_value=self.reference)
        self.gpkg_for = self.patch(self.helper, "gpkg_path_for_layer", return_value="C:/data/main.gpkg")
        self.default_path = self.patch(self.helper, "default_standalone_gpkg_path", return_value="C:/data/new.gpkg")
        self.created = Mock(name="created_layer")
        self.created.isValid.return_value = True
        self.created.name.return_value = "Created"
        self.create = self.patch(self.helper, "create_or_load_layer", return_value=(self.created, ""))
        self.warning = self.patch(ModernMessageDialog, "show_warning")
        self.info = self.patch(ModernMessageDialog, "show_info")
        self.text = self.patch(ModernMessageDialog, "get_text_modern", return_value=("  New layer  ", True))
        self.choice = self.patch(ModernMessageDialog, "ask_choice_modern", return_value=self.key("STORAGE_EXISTING"))
        self.yes_no = self.patch(ModernMessageDialog, "ask_yes_no", return_value=True)
        self.save_as = self.patch(QFileDialog, "getSaveFileName", return_value=("", ""))
        self.sync = self.patch(SettingsModuleCard, "sync_main_layer_selection")

    def key(self, name):
        return f"T:{self.prefix}_temp_layer_{name.lower()}"

    def run_flow(self):
        button = self.card.findChild(QPushButton, self.button_name)
        button.click()

    def warned(self, name):
        self.assertEqual(self.warning.call_args.args[1], self.key(name))

    def test_button_has_its_name_variant_and_text(self):
        button = self.card.findChild(QPushButton, self.button_name)
        self.assertIsNotNone(button)
        self.assertEqual(button.property("variant"), self.variant)
        self.assertEqual(button.text(), self.real_translate(self.key("CREATE_BUTTON")[2:]))

    def test_the_current_main_layer_is_the_preferred_reference(self):
        layer = Mock()
        self.card._layer_selector.currentLayer = Mock(return_value=layer)
        self.run_flow()
        self.resolve.assert_called_once_with(layer)

    def test_no_reference_layer_warns_and_asks_nothing(self):
        self.resolve.return_value = None
        self.run_flow()
        self.warned("REFERENCE_REQUIRED")
        self.text.assert_not_called()

    def test_name_prompt_uses_the_pending_name_then_the_default(self):
        self.text.return_value = ("", False)
        self.run_flow()
        self.assertEqual(self.text.call_args.args, (self.key("PROMPT_TITLE"), self.key("PROMPT_LABEL")))
        self.assertEqual(self.text.call_args.kwargs, {"text": self.helper.DEFAULT_LAYER_NAME})
        self.card._orig_element_name = "orig"
        self.card._pend_element_name = "pend"
        self.run_flow()
        self.assertEqual(self.text.call_args.kwargs, {"text": "pend"})
        self.choice.assert_not_called()

    def test_blank_name_warns(self):
        self.text.return_value = ("   ", True)
        self.run_flow()
        self.warned("NAME_REQUIRED")
        self.choice.assert_not_called()

    def test_storage_question_and_its_cancel(self):
        self.choice.return_value = "T:cancel_button"
        self.run_flow()
        args, kwargs = self.choice.call_args
        self.assertEqual(args, (self.key("STORAGE_TITLE"), self.key("STORAGE_MESSAGE")))
        self.assertEqual(kwargs["buttons"], [self.key("STORAGE_EXISTING"), self.key("STORAGE_STANDALONE"), "T:cancel_button"])
        self.assertEqual(kwargs["default"], self.key("STORAGE_STANDALONE"))
        self.assertEqual(kwargs["cancel"], "T:cancel_button")
        self.assertEqual(kwargs["button_variants"], [ButtonVariant.PRIMARY, ButtonVariant.SUCCESS, ButtonVariant.GHOST])
        self.choice.return_value = None
        self.run_flow()
        self.create.assert_not_called()

    def test_existing_storage_needs_a_geopackage_reference(self):
        self.gpkg_for.return_value = ""
        self.run_flow()
        self.gpkg_for.assert_called_once_with(self.reference)
        self.warned("GPKG_REQUIRED")
        self.create.assert_not_called()

    def test_existing_storage_creates_in_the_reference_package(self):
        self.run_flow()
        self.create.assert_called_once_with(self.reference, "New layer", gpkg_path=None, overwrite_file=False)
        self.save_as.assert_not_called()

    def test_standalone_save_dialog_and_its_cancel(self):
        self.choice.return_value = self.key("STORAGE_STANDALONE")
        self.run_flow()
        self.default_path.assert_called_once_with(self.reference, "New layer")
        self.assertEqual(
            self.save_as.call_args.args,
            (self.card, self.key("SAVE_DIALOG_TITLE"), "C:/data/new.gpkg", "GeoPackage (*.gpkg)"),
        )
        self.create.assert_not_called()

    def test_standalone_path_gets_the_gpkg_suffix_and_a_new_file_is_not_asked(self):
        self.choice.return_value = self.key("STORAGE_STANDALONE")
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "out")
            self.save_as.return_value = (target, "")
            self.run_flow()
        self.yes_no.assert_not_called()
        self.create.assert_called_once_with(self.reference, "New layer", gpkg_path=target + ".gpkg", overwrite_file=False)

    def test_existing_file_asks_before_overwriting(self):
        # Found 2026-11-24: OK deleted the whole file with every layer in it; now the layers are named,
        # Cancel is the default and the old file is kept as a backup.
        overwrite, cancel = "T:temp_layer_overwrite_button", "T:cancel_button"
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "out.GPKG")
            Path(target).write_text("x")
            self.save_as.return_value = (target, "")

            self.choice.side_effect = [self.key("STORAGE_STANDALONE"), cancel]
            self.run_flow()
            self.create.assert_not_called()
            question = self.choice.call_args
            self.assertEqual(question.args[0], self.key("OVERWRITE_TITLE"))
            self.assertIn("out.GPKG", question.args[1])
            self.assertEqual((question.kwargs["buttons"], question.kwargs["default"]), ([overwrite, cancel], cancel))
            self.assertTrue(os.path.exists(target))

            self.choice.side_effect = [self.key("STORAGE_STANDALONE"), overwrite]
            self.run_flow()
            backups = [name for name in os.listdir(folder) if ".backup-" in name]
            self.assertFalse(os.path.exists(target))
            self.assertEqual(len(backups), 1)
            self.assertEqual(Path(folder, backups[0]).read_text(), "x")
            self.assertIn(backups[0], self.info.call_args.args[1])
        self.yes_no.assert_not_called()
        self.create.assert_called_once_with(self.reference, "New layer", gpkg_path=target, overwrite_file=False)

    def test_failed_creation_warns_with_the_name_and_error(self):
        self.create.return_value = (None, "disk full")
        self.run_flow()
        self.assertEqual(
            self.warning.call_args.args,
            ("T:Error", self.key("CREATE_FAILED") + str([("error", "disk full"), ("name", "New layer")])),
        )
        self.created.isValid.return_value = False
        self.create.return_value = (self.created, "")
        self.run_flow()
        self.assertEqual(
            self.warning.call_args.args[1],
            self.key("CREATE_FAILED") + str([("error", "T:Error"), ("name", "New layer")]),
        )
        self.info.assert_not_called()

    def test_created_layer_becomes_the_saved_main_layer(self):
        self.run_flow()
        self.logic.set_module_layer_id.assert_called_once_with(self.module, kind="element", layer_name="Created")
        self.sync.assert_called_once_with("Created", force=True)
        self.assertEqual(self.info.call_args.args, ("T:Success", self.key("READY") + str([("name", "Created")])))
        self.created.name.return_value = ""
        self.run_flow()
        self.sync.assert_called_with("New layer", force=True)

    def test_unexpected_error_is_logged_and_shown(self):
        self.text.side_effect = RuntimeError("dialog gone")
        self.patch(MapHelpers, "layer_name_from_id", return_value="")
        self.run_flow()
        self.assertEqual(self.log.call_args.kwargs["event"], self.event)
        self.assertEqual(
            self.warning.call_args.args[1],
            self.key("CREATE_FAILED") + str([("error", "dialog gone"), ("name", self.helper.DEFAULT_LAYER_NAME)]),
        )
        self.card._pend_element_name = "layer-id"
        self.patch(MapHelpers, "layer_name_from_id", return_value="Layer name")
        self.run_flow()
        self.assertIn(("name", "Layer name"), eval(self.warning.call_args.args[1][len(self.key("CREATE_FAILED")):]))


class WorksTempLayerFlowTest(_TempLayerFlow, _CardTest):
    module = "works"
    helper = WorksTempLayerHelper
    prefix = "works"
    event = "works_temp_layer_button_failed"
    button_name = "WorksTempLayerCreateButton"
    variant = ButtonVariant.WARNING


class ProjectsTempLayerFlowTest(_TempLayerFlow, _CardTest):
    module = "project"
    helper = ProjectsTempLayerHelper
    prefix = "projects"
    event = "projects_temp_layer_button_failed"
    button_name = "ProjectsTempLayerCreateButton"
    variant = ButtonVariant.SUCCESS


# --- card layout ---------------------------------------------------------------------


class CardLayoutTest(unittest.TestCase):
    def build(self, module, **kwargs):
        with patch("qgis.core.QgsSettings.setValue"):
            card = SettingsModuleCard(LanguageManager(language="en"), module, module, logic=_logic(), **kwargs)
        self.addCleanup(card.deleteLater)
        return card

    def names(self, card):
        return {child.objectName() for child in card.findChildren(QWidget) if child.objectName()}

    def test_groups_follow_the_module_and_its_supports(self):
        all_supports = dict(supports_types=True, supports_statuses=True, supports_tags=True)
        cases = {
            ("works", True): {"MainLayerGroup", "GeospatialLayerMapperGroup", "WorksTempLayerHelperGroup",
                              "StatusPreferencesGroup", "TagPreferencesGroup", "TypePreferencesGroup",
                              "ProjectBoardNotStartedStatusesGroup"},
            ("project", False): {"MainLayerGroup", "GeospatialLayerMapperGroup", "ProjectsTempLayerHelperGroup"},
            ("property", False): {"MainLayerGroup", "ArchiveLayerGroup", "GeospatialLayerMapperGroup",
                                  "PropertyManagementContainer"},
        }
        optional = {"ArchiveLayerGroup", "WorksTempLayerHelperGroup", "ProjectsTempLayerHelperGroup",
                    "StatusPreferencesGroup", "TagPreferencesGroup", "TypePreferencesGroup",
                    "ProjectBoardNotStartedStatusesGroup", "PropertyManagementContainer"}
        for (module, supports), expected in cases.items():
            with self.subTest(module=module):
                card = self.build(module, **(all_supports if supports else {}))
                names = self.names(card)
                self.assertTrue(expected <= names, expected - names)
                self.assertFalse((optional - expected) & names, (optional - expected) & names)

    def test_archive_layer_can_be_switched_on_for_any_module(self):
        card = self.build("easement", supports_archive_layer=True)
        layers = card.findChild(QWidget, "LayersContainer").layout()
        self.assertGreaterEqual(layers.indexOf(card.findChild(QWidget, "ArchiveLayerGroup")), 0)
        self.assertGreaterEqual(layers.indexOf(card.findChild(QWidget, "MainLayerGroup")), 0)
        self.assertTrue(card.supports_archive)

    def test_filter_widgets_are_created_only_for_supported_preferences(self):
        card = self.build("works", supports_statuses=True)
        self.assertIsNotNone(card._status_filter_widget)
        self.assertIsNotNone(card._not_started_status_filter_widget)
        self.assertIsNone(card._type_filter_widget)
        self.assertIsNone(card._tags_filter_widget)

    def test_geospatial_mode_swaps_the_mapper_and_the_works_temp_helper(self):
        card = self.build("works")
        mapper = card.findChild(QWidget, "GeospatialLayerMapperGroup")
        temp = card.findChild(QWidget, "WorksTempLayerHelperGroup")
        card.set_geospatial_mode_active(True)
        self.assertFalse(mapper.isHidden())
        self.assertTrue(temp.isHidden())
        card.set_geospatial_mode_active(False)
        self.assertTrue(mapper.isHidden())
        self.assertFalse(temp.isHidden())

    def test_mapper_button_opens_the_mapper_for_the_module(self):
        card = self.build("works")
        with patch("Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog.GeospatialLayerMapperDialog.open_for_module") as open_for:
            card.findChild(QPushButton, "GeospatialLayerMapperButton").click()
        self.assertEqual(open_for.call_args.kwargs["module_name"], "works")
        self.assertIs(open_for.call_args.kwargs["parent"], card)

    def test_label_values_are_loaded_into_the_labels_widget(self):
        logic = _logic()
        logic.load_module_label_values.return_value = {"flag": "true", "text": ""}
        labels = [{"key": "flag", "tool": "checkBox", "title_value": "Flag"},
                  {"key": "text", "tool": "lineEdit", "title_value": "Text"},
                  {"tool": "lineEdit", "title_value": "No key"}]
        with patch("qgis.core.QgsSettings.setValue"):
            card = SettingsModuleCard(LanguageManager(language="en"), "works", "Works", module_labels=labels, logic=logic)
        self.addCleanup(card.deleteLater)
        self.assertEqual(card._orig_label_values, {"flag": True, "text": ""})
        self.assertEqual(card._pend_label_values, {"flag": True, "text": ""})
        self.assertIsNotNone(card._labels_widget)


# --- preferences ---------------------------------------------------------------------


class PreferencesTest(_CardTest):
    module = "works"
    card_kwargs = dict(supports_types=True, supports_statuses=True, supports_tags=True)

    def setUp(self):
        super().setUp()
        stored = {ModuleSupports.STATUSES.value: ["1"], ModuleSupports.TAGS.value: ["t"], ModuleSupports.TYPES.value: [5]}
        self.logic.load_module_preference_ids.side_effect = lambda module, support_key: stored[support_key]
        self.not_started = self.patch(ProjectBoardStatusRules, "load_not_started_status_ids", return_value={"9"})
        for widget in self._widgets():
            widget.ensure_loaded = Mock()
            widget.set_selected_ids = Mock()

    def _widgets(self):
        card = self.card
        return [card._status_filter_widget, card._tags_filter_widget, card._type_filter_widget,
                card._not_started_status_filter_widget]

    def test_activate_loads_every_preference_and_only_loads_widgets_with_saved_ids(self):
        self.card.on_settings_activate()
        self.assertEqual(self.card._orig_status_preferences, {"1"})
        self.assertEqual(self.card._pend_tag_preferences, {"t"})
        self.assertEqual(self.card._orig_type_preferences, {5})
        self.assertEqual(self.card._orig_not_started_status_preferences, {"9"})
        for widget in self._widgets():
            widget.ensure_loaded.assert_called_once_with()
        self.assertFalse(self.card.has_pending_changes())

    def test_filter_loads_its_data_on_first_focus_only(self):
        widget = self.card._type_filter_widget
        self.assertIn(widget, self.card._lazy_filter_widgets)
        QCoreApplication.sendEvent(widget, QFocusEvent(QEvent.Type.FocusIn))
        QCoreApplication.sendEvent(widget, QFocusEvent(QEvent.Type.FocusIn))
        widget.ensure_loaded.assert_called_once_with()
        self.assertNotIn(widget, self.card._lazy_filter_widgets)
        self.assertIn(self.card._status_filter_widget, self.card._lazy_filter_widgets)

    def test_a_failing_lazy_load_is_logged(self):
        widget = self.card._tags_filter_widget
        widget.ensure_loaded.side_effect = RuntimeError("no session")
        QCoreApplication.sendEvent(widget, _left_click())
        self.assertEqual(self.log.call_args.kwargs["event"], "settings_module_filter_lazy_load_failed")
        self.assertNotIn(widget, self.card._lazy_filter_widgets)

    def test_selection_changes_are_pending_and_normalized(self):
        self.card.on_settings_activate()
        self.card._on_preference_selection_changed(support_key=ModuleSupports.STATUSES.value, widget=None, ids=[1, 2])
        self.card._on_preference_selection_changed(support_key=ModuleSupports.TYPES.value, widget=None, ids=[7])
        self.card._on_not_started_status_selection_changed(ids=[" 3 ", "", None])
        self.assertEqual(self.card._pend_status_preferences, {"1", "2"})
        self.assertEqual(self.card._pend_type_preferences, {7})
        self.assertEqual(self.card._pend_not_started_status_preferences, {"3", "None"})
        self.assertTrue(self.card.has_pending_changes())

    def test_widget_signal_feeds_the_pending_set(self):
        self.card.on_settings_activate()
        self.card._tags_filter_widget.selectionChanged.emit(["Tag"], [1, "y"])
        self.assertEqual(self.card._pend_tag_preferences, {"1", "y"})

    def test_selection_failure_is_logged_per_preference(self):
        widget = Mock()
        widget.selected_ids.side_effect = RuntimeError("deleted")
        for key, event in (
            (ModuleSupports.STATUSES.value, "settings_module_status_selection_failed"),
            (ModuleSupports.TAGS.value, "settings_module_tags_selection_failed"),
            (ModuleSupports.TYPES.value, "settings_module_type_selection_failed"),
            ("other", "settings_module_preference_selection_failed"),
        ):
            self.card._on_preference_selection_changed(support_key=key, widget=widget)
            self.assertEqual(self.log.call_args.kwargs["event"], event)
        self.card._on_not_started_status_selection_changed(widget=widget)
        self.assertEqual(self.log.call_args.kwargs["event"], "settings_module_not_started_status_selection_failed")

    def test_apply_saves_only_what_changed(self):
        self.card.on_settings_activate()
        self.card._pend_tag_preferences = {"t", "u"}
        self.card._pend_not_started_status_preferences = {"4"}
        widget = self.card._not_started_status_filter_widget
        widget.selected_ids = Mock(return_value=["4"])
        widget.selected_texts = Mock(return_value=["Four"])
        self.card.apply()
        self.logic.save_module_preference_ids.assert_called_once_with("works", support_key=ModuleSupports.TAGS.value, ids={"t", "u"})
        self.logic.save_module_label_value.assert_called_once_with(
            "works",
            SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES,
            ProjectBoardStatusRules.serialize_not_started_status_rows(["4"], ["Four"]),
        )
        self.assertEqual(self.card._orig_tag_preferences, {"t", "u"})
        self.assertEqual(self.card._orig_not_started_status_preferences, {"4"})
        self.assertFalse(self.card.has_pending_changes())

    def test_emptied_not_started_statuses_clear_the_stored_value(self):
        self.card.on_settings_activate()
        self.card._pend_not_started_status_preferences = set()
        self.card.apply()
        self.logic.clear_module_label_value.assert_called_once_with(
            "works", SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES
        )
        self.logic.save_module_label_value.assert_not_called()

    def test_revert_puts_the_saved_selection_back_without_signals(self):
        self.card.on_settings_activate()
        self.card._pend_status_preferences = {"x"}
        self.card._pend_not_started_status_preferences = {"y"}
        self.card.revert()
        self.assertEqual(self.card._pend_status_preferences, {"1"})
        self.assertEqual(self.card._pend_not_started_status_preferences, {"9"})
        self.card._status_filter_widget.set_selected_ids.assert_called_once_with(["1"], emit=False)
        self.card._not_started_status_filter_widget.set_selected_ids.assert_called_once_with(["9"], emit=False)
        self.assertFalse(self.card.has_pending_changes())

    def reset(self, *, answer=True):
        self.card.on_settings_activate()
        self.card._orig_label_values = {"a": "1"}
        self.card._pend_label_values = {"a": "1"}
        with patch.object(ModernMessageDialog, "ask_yes_no", return_value=answer) as ask:
            self.card._on_reset_settings()
        return ask

    def test_reset_asks_first_and_no_changes_nothing(self):
        ask = self.reset(answer=False)
        ask.assert_called_once()
        self.assertFalse(self.card.has_pending_changes())
        self.assertEqual(self.card._pend_status_preferences, {"1"})

    def test_reset_is_pending_and_writes_nothing_until_confirm(self):
        # Found 2026-11-24: the reset cleared the storage at once, and Discard then showed values that were gone.
        self.logic.get_module_layer_ids.return_value = {"element": "layer-1"}
        self.reset()
        self.logic.clear_module_preference_ids.assert_not_called()
        self.logic.clear_module_label_value.assert_not_called()
        self.logic.set_module_layer_id.assert_not_called()
        for widget in self._widgets():
            widget.set_selected_ids.assert_called_with([], emit=False)
        self.assertTrue(self.card.has_pending_changes())
        self.assertEqual(self.card._orig_status_preferences, {"1"})

        self.card.apply()

        saved = {call.kwargs["support_key"]: set(call.kwargs["ids"])
                 for call in self.logic.save_module_preference_ids.call_args_list}
        self.assertEqual(saved, {ModuleSupports.STATUSES.value: set(), ModuleSupports.TAGS.value: set(),
                                 ModuleSupports.TYPES.value: set()})
        self.logic.clear_module_label_value.assert_any_call("works", SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES)
        self.logic.clear_module_label_value.assert_any_call("works", "a")
        self.logic.set_module_layer_id.assert_called_once_with("works", kind="element", layer_name="")
        self.assertFalse(self.card.has_pending_changes())

    def test_discard_after_a_reset_brings_every_value_back(self):
        self.reset()
        self.card.revert()
        self.assertFalse(self.card.has_pending_changes())
        self.assertEqual(self.card._pend_status_preferences, {"1"})
        self.assertEqual(self.card._pend_not_started_status_preferences, {"9"})
        self.assertEqual(self.card._pend_label_values, {"a": "1"})
        self.logic.set_module_layer_id.assert_not_called()

class UnsupportedPreferencesTest(_CardTest):
    module = "project"

    def test_only_statuses_are_read_and_not_started_needs_status_support(self):
        with patch.object(ProjectBoardStatusRules, "load_not_started_status_ids") as not_started:
            self.card.on_settings_activate()
        not_started.assert_not_called()
        self.assertEqual(
            [call.kwargs["support_key"] for call in self.logic.load_module_preference_ids.call_args_list],
            [ModuleSupports.STATUSES.value],
        )
        self.card._pend_type_preferences = {"x"}
        self.card._pend_tag_preferences = {"y"}
        self.assertFalse(self.card.has_pending_changes())
        self.card._pend_not_started_status_preferences = {"z"}
        self.card.apply()
        self.logic.save_module_label_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()
