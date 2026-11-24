"""The settings Confirm reports failed saves, and the Geospatial switch says what it really does (2026-11-24).

- Confirm saves each card on its own and collects the results: a failed card stays pending (its saved
  values are not replaced), the others become clean, and one translated warning names the failed cards.
- The save helpers return their result instead of only logging it, so a failed write reaches Confirm.
- The button that turned Geospatial off was called "Vaata Geospatiali seadistust" and its dialog said all
  Geospatial settings are removed. It is now "Lülita käsitsi seadistusele"; the dialog says only the mode
  changes and layers and mapper data stay.
"""
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

from Kavitro_dev.constants.module_names import ModuleSupports
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.Settings.SettingsUI import SettingsModule
from Kavitro_dev.modules.Settings.cards.SettingsModuleCard import SettingsModuleCard
from Kavitro_dev.modules.Settings.cards.SettingsProjectBaseLayersCard import SettingsProjectBaseLayersCard
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.utils.settings_logic import SettingsLogic
from Kavitro_dev.utils.settings_service import SettingsService

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager("et")


class _LoggedCase(unittest.TestCase):
    def setUp(self) -> None:
        for target in ("log_exception", "log"):
            patcher = patch.object(PythonFailLogger, target)
            patcher.start()
            self.addCleanup(patcher.stop)
        writes = patch("qgis.core.QgsSettings.setValue")
        writes.start()
        self.addCleanup(writes.stop)


class _FakeCard:
    """A card whose save succeeds, fails or raises; a good save makes it clean."""

    def __init__(self, title: str, result=True) -> None:
        self.title = title
        self.result = result
        self.pending = True

    def card_title(self) -> str:
        return self.title

    def has_pending_changes(self) -> bool:
        return self.pending

    def apply(self):
        if isinstance(self.result, Exception):
            raise self.result
        if self.result:
            self.pending = False
        return self.result


class ConfirmCollectsResultsTest(_LoggedCase):
    def setUp(self) -> None:
        super().setUp()
        self.module = SettingsModule()
        self.addCleanup(self.module.deleteLater)
        self.module._project_base_layers_card = _FakeCard("Baaskihid")
        self.module._module_cards = {"Works": _FakeCard("Tööd"), "Project": _FakeCard("Projektid")}
        self.module.logic = Mock()
        self.module.logic.apply_pending_changes.return_value = True
        self.module.logic.has_unsaved_changes.return_value = False
        self.module._sync_map_overlay_from_settings = Mock()
        warning = patch.object(ModernMessageDialog, "show_warning")
        self.warning = warning.start()
        self.addCleanup(warning.stop)

    def test_all_saved_is_clean_and_silent(self) -> None:
        self.assertTrue(self.module.apply_pending_changes())
        self.warning.assert_not_called()
        self.assertFalse(self.module._pending_changes)

    def test_a_failed_card_stays_pending_and_is_named_once(self) -> None:
        self.module._module_cards["Works"].result = False
        self.module._project_base_layers_card.result = RuntimeError("disk full")

        self.assertFalse(self.module.apply_pending_changes())

        self.warning.assert_called_once()
        title, message = self.warning.call_args.args
        self.assertEqual(title, LANG.translate(TranslationKeys.SETTINGS_APPLY_FAILED_TITLE))
        self.assertIn("Tööd", message)
        self.assertIn("Baaskihid", message)
        self.assertNotIn("Projektid", message)
        self.assertTrue(self.module._module_cards["Works"].has_pending_changes())
        self.assertFalse(self.module._module_cards["Project"].has_pending_changes())
        self.assertTrue(self.module._pending_changes)
        self.module._sync_map_overlay_from_settings.assert_called_once_with()

    def test_failed_user_settings_name_the_user_card(self) -> None:
        self.module.logic.apply_pending_changes.return_value = False
        self.assertFalse(self.module.apply_pending_changes())
        self.assertIn(LANG.translate(TranslationKeys.USER), self.warning.call_args.args[1])

    def test_leaving_with_save_stays_when_the_save_failed(self) -> None:
        self.module._module_cards["Works"].result = False
        save = LANG.translate(TranslationKeys.SAVE)
        with patch.object(ModernMessageDialog, "ask_choice_modern", return_value=save):
            self.assertFalse(self.module.confirm_navigation_away())
        self.warning.assert_called_once()


class ModuleCardKeepsFailedValuesPendingTest(_LoggedCase):
    def setUp(self) -> None:
        super().setUp()
        self.logic = Mock()
        self.card = SettingsModuleCard(LANG, "works", "Tööd", supports_tags=True, logic=self.logic)
        self.addCleanup(self.card.deleteLater)
        self.card._pend_element_name = "new-layer"
        self.card._pend_tag_preferences = {"t"}
        self.card._orig_label_values = {"a": "old"}
        self.card._pend_label_values = {"a": "new"}

    def test_failed_layer_write_keeps_every_value_pending(self) -> None:
        self.logic.set_module_layer_id.return_value = False
        self.assertFalse(self.card.apply())
        self.assertEqual(self.card._orig_element_name, "")
        self.assertEqual(self.card._pend_element_name, "new-layer")
        self.assertEqual(self.card._orig_tag_preferences, set())
        self.assertEqual(self.card._orig_label_values, {"a": "old"})
        self.assertTrue(self.card.has_pending_changes())
        # The other values were still written, so the next Confirm only has to retry.
        self.logic.save_module_preference_ids.assert_called_once()
        self.logic.save_module_label_value.assert_called_once_with("works", "a", "new")

    def test_failed_preference_or_label_write_fails_the_card(self) -> None:
        for failing in ("save_module_preference_ids", "save_module_label_value"):
            with self.subTest(failing=failing):
                self.logic.reset_mock()
                for name in ("set_module_layer_id", "save_module_preference_ids", "save_module_label_value"):
                    getattr(self.logic, name).return_value = name != failing
                self.assertFalse(self.card.apply())
                self.assertTrue(self.card.has_pending_changes())

    def test_raising_write_is_caught(self) -> None:
        self.logic.save_module_label_value.side_effect = RuntimeError("boom")
        self.assertFalse(self.card.apply())
        self.assertTrue(self.card.has_pending_changes())

    def test_successful_save_becomes_clean(self) -> None:
        for name in ("set_module_layer_id", "save_module_preference_ids", "save_module_label_value"):
            getattr(self.logic, name).return_value = True
        self.assertTrue(self.card.apply())
        self.assertEqual(self.card._orig_element_name, "new-layer")
        self.assertEqual(self.card._orig_tag_preferences, {"t"})
        self.assertFalse(self.card.has_pending_changes())


class SaveHelpersReturnTheirResultTest(_LoggedCase):
    def test_logic_helpers_report_a_failed_write(self) -> None:
        logic = SettingsLogic()
        logic._service = Mock()
        logic._service.module_main_layer_name.side_effect = RuntimeError("x")
        logic._service.module_label_value.side_effect = RuntimeError("x")
        self.assertFalse(logic.set_module_layer_id("works", kind="element", layer_name="a"))
        self.assertFalse(logic.save_module_label_value("works", "k", "v"))
        self.assertFalse(logic.clear_module_label_value("works", "k"))
        with patch.object(SettingsService, "module_preferred_tags", side_effect=RuntimeError("x")):
            self.assertFalse(logic.save_module_preference_ids("works", support_key=ModuleSupports.TAGS.value, ids={"a"}))

    def test_logic_helpers_report_a_good_write(self) -> None:
        logic = SettingsLogic()
        logic._service = Mock()
        self.assertTrue(logic.set_module_layer_id("works", kind="archive", layer_name=""))
        self.assertTrue(logic.save_module_label_value("works", "k", "v"))
        self.assertTrue(logic.clear_module_label_value("works", "k"))

    def test_failed_user_settings_stay_pending(self) -> None:
        logic = SettingsLogic()
        logic._service = Mock()
        logic._original_preferred = "project"
        logic.set_user_preferred_module("works")
        logic._service.map_canvas_search_bar_enabled.side_effect = RuntimeError("x")
        self.assertFalse(logic.apply_pending_changes())
        self.assertEqual(logic.get_original_preferred(), "project")
        self.assertTrue(logic.has_unsaved_changes())


class BaseLayersCardTest(_LoggedCase):
    def card(self, mode: str) -> SettingsProjectBaseLayersCard:
        card = SettingsProjectBaseLayersCard(LANG)
        self.addCleanup(card.deleteLater)
        card._orig_setup_mode = card._pend_setup_mode = mode
        card._update_geospatial_mode_ui()
        return card

    def test_failed_save_keeps_the_card_pending(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        card._pend_setup_mode = SettingsProjectBaseLayersCard.SETUP_MODE_MANUAL
        with patch.object(card._settings_service, "geospatial_setup_mode"), \
                patch.object(card._service, "save_state", side_effect=RuntimeError("read-only project")):
            self.assertFalse(card.apply())
        self.assertEqual(card._orig_setup_mode, SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        self.assertTrue(card.has_pending_changes())

    def test_good_save_is_clean(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_MANUAL)
        with patch.object(card._settings_service, "geospatial_setup_mode"), patch.object(card._service, "save_state"):
            self.assertTrue(card.apply())
        self.assertFalse(card.has_pending_changes())

    def test_button_is_named_for_what_it_does(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        self.assertEqual(card._geospatial_button.text(), "Lülita käsitsi seadistusele")
        manual = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_MANUAL)
        self.assertEqual(manual._geospatial_button.text(), LANG.translate(TranslationKeys.SETTINGS_GEOSPATIAL_CONNECT_BUTTON))

    def test_switch_dialog_says_what_stays_and_changes_only_the_pending_mode(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        with patch.object(ModernMessageDialog, "ask_yes_no", return_value=True) as ask, \
                patch.object(card._settings_service, "geospatial_setup_mode") as mode_write, \
                patch.object(card._service, "save_state") as save:
            card._geospatial_button.click()
        title, body = ask.call_args.args
        self.assertEqual(title, "Kas lülitada käsitsi seadistusele?")
        self.assertIn("mapperiga kantud andmed jäävad alles", body)
        self.assertIn("Kinnita", body)
        self.assertNotIn("eemaldatakse", body)
        self.assertEqual(ask.call_args.kwargs["yes_label"], "Lülita käsitsi seadistusele")
        self.assertEqual(ask.call_args.kwargs["default"], LANG.translate(TranslationKeys.CANCEL_BUTTON))
        mode_write.assert_not_called()
        save.assert_not_called()
        self.assertEqual(card._pend_setup_mode, SettingsProjectBaseLayersCard.SETUP_MODE_MANUAL)
        self.assertTrue(card.has_pending_changes())

    def test_cancel_keeps_geospatial(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        with patch.object(ModernMessageDialog, "ask_yes_no", return_value=False):
            card._geospatial_button.click()
        self.assertEqual(card._pend_setup_mode, SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        self.assertFalse(card.has_pending_changes())

    def test_a_failing_dialog_does_not_escape_the_click(self) -> None:
        card = self.card(SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)
        with patch.object(ModernMessageDialog, "ask_yes_no", side_effect=RuntimeError("deleted")):
            card._on_geospatial_button_clicked()
        self.assertEqual(card._pend_setup_mode, SettingsProjectBaseLayersCard.SETUP_MODE_GEOSPATIAL)


if __name__ == "__main__":
    unittest.main()
