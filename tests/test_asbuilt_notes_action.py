"""Lisa/uuenda märkmeid merges the notes into the description that is there, never into an empty stand-in."""
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

from PyQt5.QtWidgets import QDialog

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.asbuilt.asbuilt_notes_service import AsBuiltNote
from Kavitro_dev.modules.asbuilt import asbuilt_card_actions
from Kavitro_dev.modules.asbuilt.asbuilt_card_actions import AsBuiltCardActions

ITEM = {"id": "a1", "name": "TJ-12"}
NOTE = AsBuiltNote(date="02.04.2026", note="kaev 47 viga")


class EditNotesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lang = LanguageManager("et")
        self.api = self._patch("APIModuleActions")
        self.dialog_class = self._patch("AsBuiltNotesEditorDialog")
        self.messages = self._patch("ModernMessageDialog")
        # Stands in for the card button.
        self.button = Mock(lang_manager=self.lang)
        dialog = self.dialog_class.return_value
        dialog.exec_.return_value = QDialog.Accepted
        dialog.get_notes.return_value = [NOTE]
        self.api.update_task_description.return_value = True

    def _patch(self, name: str) -> Mock:
        patcher = patch.object(asbuilt_card_actions, name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def edit(self) -> dict:
        self.button.item_data = dict(ITEM)
        AsBuiltCardActions(self.button).edit_notes()
        return self.button.item_data

    def test_failed_load_opens_nothing_and_saves_nothing(self) -> None:
        self.api.get_task_description.return_value = None

        self.edit()

        self.dialog_class.assert_not_called()
        self.api.update_task_description.assert_not_called()
        self.assertEqual(
            self.messages.show_warning.call_args.args,
            (self.lang.translate(TranslationKeys.ERROR),
             self.lang.translate(TranslationKeys.ASBUILT_NOTES_LOAD_FAILED).format(name="TJ-12")),
        )

    def test_notes_go_into_the_description_as_it_is_at_saving(self) -> None:
        self.api.get_task_description.side_effect = ["<p>Avamisel</p>", "<p>Vahepeal muudetud</p>"]

        item = self.edit()

        item_id, saved = self.api.update_task_description.call_args.args
        self.assertEqual(item_id, "a1")
        self.assertTrue(saved.startswith("<p>Vahepeal muudetud</p><p><strong>"))
        self.assertEqual(item["description"], saved)
        self.messages.show_info.assert_called_once()

    def test_failed_reload_before_saving_keeps_the_opened_description(self) -> None:
        self.api.get_task_description.side_effect = ["<p>Avamisel</p>", None]

        self.edit()

        _item_id, saved = self.api.update_task_description.call_args.args
        self.assertTrue(saved.startswith("<p>Avamisel</p><p><strong>"))


if __name__ == "__main__":
    unittest.main()
