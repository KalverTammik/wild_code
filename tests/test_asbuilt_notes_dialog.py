"""The as-built notes dialog: one row per note under its date, the resolved date only on resolved notes."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt5.QtCore import QCoreApplication, QEvent, QPoint
from PyQt5.QtWidgets import QWIDGETSIZE_MAX, QApplication, QLabel, QLineEdit, QPushButton, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.asbuilt.asbuilt_notes_dialog import AsBuiltNotesEditorDialog
from Kavitro_dev.modules.asbuilt.asbuilt_notes_service import AsBuiltNote, AsBuiltNotesService

TODAY = "08.11.2026"
NOTES = [
    AsBuiltNote(date="02.04.2026", note="kaev 47 viga", resolved=True, resolved_date="03.04.2026"),
    AsBuiltNote(date="02.04.2026", note="toru sügavus", resolved=False, resolved_date=""),
    # Typed by hand before the calendar field.
    AsBuiltNote(date="05.06.2026", note="vana kuupäev", resolved=True, resolved_date="eelmisel nädalal"),
    AsBuiltNote(date="05.06.2026", note="lahtine kuupäevaga", resolved=False, resolved_date="01.06.2026"),
]


class NotesDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.lang = LanguageManager("et")
        today = patch.object(AsBuiltNotesService, "today_text", return_value=TODAY)
        today.start()
        self.addCleanup(today.stop)

    def open_dialog(self, notes: list[AsBuiltNote]) -> AsBuiltNotesEditorDialog:
        dialog = AsBuiltNotesEditorDialog(item_name="TJ-12 Kase tn", notes=notes, lang_manager=self.lang)
        self.addCleanup(self._delete, dialog)
        return dialog

    @staticmethod
    def _delete(dialog: AsBuiltNotesEditorDialog) -> None:
        dialog.hide()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    @staticmethod
    def texts(dialog: AsBuiltNotesEditorDialog, object_name: str) -> list[str]:
        return [label.text() for label in dialog.findChildren(QLabel, object_name)]

    def test_notes_are_grouped_by_date_under_one_row_of_column_headers(self) -> None:
        dialog = self.open_dialog(NOTES)

        self.assertEqual(self.texts(dialog, "AsBuiltNotesGroupTitle"), ["02.04.2026", "05.06.2026"])
        self.assertEqual(
            self.texts(dialog, "AsBuiltNotesColumnHeader"),
            [self.lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_NOTE),
             self.lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED)],
        )
        self.assertEqual(self.texts(dialog, "AsBuiltNotesItemName"), ["TJ-12 Kase tn"])

    def test_opening_and_saving_changes_nothing(self) -> None:
        dialog = self.open_dialog(NOTES)

        self.assertEqual(dialog.get_notes(), NOTES)
        self.assertEqual([field.text() for field in dialog.findChildren(QLineEdit, "AsBuiltNoteResolvedDateText")],
                         ["eelmisel nädalal"])

    def test_resolved_date_shows_only_on_resolved_notes(self) -> None:
        dialog = self.open_dialog(NOTES)

        self.assertEqual([row.date_edit.isHidden() for row in dialog._rows()], [False, True, False, True])

    def test_resolving_fills_in_today_and_reopening_clears_the_date(self) -> None:
        dialog = self.open_dialog([AsBuiltNote(date="02.04.2026", note="toru sügavus")])
        row = dialog._rows()[0]

        row.resolved_check.setChecked(True)
        self.assertEqual(dialog.get_notes()[0].resolved_date, TODAY)
        self.assertFalse(row.date_edit.isHidden())

        row.resolved_check.setChecked(False)
        self.assertEqual(dialog.get_notes()[0].resolved_date, "")
        self.assertTrue(row.date_edit.isHidden())

    def test_resolving_keeps_a_date_the_note_already_had(self) -> None:
        dialog = self.open_dialog([NOTES[3]])

        dialog._rows()[0].resolved_check.setChecked(True)

        self.assertEqual(dialog.get_notes()[0].resolved_date, "01.06.2026")

    def test_resolved_notes_are_marked_for_the_stylesheet(self) -> None:
        dialog = self.open_dialog(NOTES[:2])
        rows = dialog._rows()

        self.assertEqual([row.note_edit.property("resolved") for row in rows], [True, False])
        rows[1].resolved_check.setChecked(True)
        self.assertTrue(rows[1].note_edit.property("resolved"))

    def test_added_note_goes_to_todays_group_and_takes_the_cursor(self) -> None:
        dialog = self.open_dialog(NOTES[:1])
        self.show(dialog)

        dialog.findChild(QPushButton, "AsBuiltNotesAddButton").click()
        QApplication.processEvents()

        self.assertEqual(self.texts(dialog, "AsBuiltNotesGroupTitle"), ["02.04.2026", TODAY])
        new_row = dialog._rows()[-1]
        self.assertEqual(new_row.date_key, TODAY)
        self.assertIs(QApplication.focusWidget(), new_row.note_edit)

    def test_deleting_the_last_note_of_a_date_removes_its_heading(self) -> None:
        dialog = self.open_dialog(NOTES)

        dialog._rows()[3].delete_button.click()
        dialog._rows()[2].delete_button.click()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.assertEqual(self.texts(dialog, "AsBuiltNotesGroupTitle"), ["02.04.2026"])
        self.assertEqual(dialog.get_notes(), NOTES[:2])

    def test_heading_counts_the_open_notes(self) -> None:
        dialog = self.open_dialog(NOTES)
        count = dialog.findChild(QLabel, "AsBuiltNotesOpenCount")

        self.assertEqual(count.text(), self.lang.translate(TranslationKeys.ASBUILT_NOTES_OPEN_COUNT).format(count=2))
        for row in dialog._rows():
            row.resolved_check.setChecked(True)
        self.assertEqual(count.text(), self.lang.translate(TranslationKeys.ASBUILT_NOTES_ALL_RESOLVED))

    def test_without_notes_one_empty_note_is_ready_for_today(self) -> None:
        dialog = self.open_dialog([])

        self.assertEqual(self.texts(dialog, "AsBuiltNotesGroupTitle"), [TODAY])
        self.assertEqual(dialog.findChild(QLabel, "AsBuiltNotesOpenCount").text(), "")
        self.assertEqual(AsBuiltNotesService.build_notes_html(dialog.get_notes()), "")

    def show(self, dialog: AsBuiltNotesEditorDialog) -> None:
        dialog.show()
        dialog.activateWindow()
        QApplication.processEvents()

    def test_rows_hold_their_fields_and_line_up_with_the_first_line(self) -> None:
        dialog = self.open_dialog(NOTES + [AsBuiltNote(date="02.04.2026", note="üks\nkaks\nkolm", resolved=True)])
        self.show(dialog)

        for row in dialog._rows():
            with self.subTest(note=row.note().note):
                # Taller than its row, the note was cut off at the bottom.
                self.assertEqual(row.height(), row.note_edit.height())
                self.assertEqual(row.date_edit.height(), row.note_edit.single_line_height())
                self.assertEqual(row.delete_button.height(), row.note_edit.single_line_height())
        one_line = dialog._rows()[0]
        self.assertEqual(one_line.note_edit.height(), one_line.date_edit.height())

    def test_cursor_starts_in_the_first_open_note(self) -> None:
        dialog = self.open_dialog(NOTES)
        self.show(dialog)

        self.assertIs(QApplication.focusWidget(), dialog._rows()[1].note_edit)

    def test_with_every_note_resolved_the_cursor_starts_on_adding_one(self) -> None:
        dialog = self.open_dialog([NOTES[0], NOTES[2]])
        self.show(dialog)

        self.assertIs(QApplication.focusWidget(), dialog.findChild(QPushButton, "AsBuiltNotesAddButton"))

    def test_tab_goes_through_the_notes_before_the_buttons(self) -> None:
        dialog = self.open_dialog(NOTES)
        self.show(dialog)
        rows = dialog._rows()

        rows[0].note_edit.setFocus()
        dialog.focusNextChild()
        self.assertIn(QApplication.focusWidget(), (rows[0].date_edit, *rows[0].date_edit.findChildren(QLineEdit)))

        rows[-1].delete_button.setFocus()
        dialog.focusNextChild()
        self.assertIs(QApplication.focusWidget(), dialog.findChild(QPushButton, "AsBuiltNotesAddButton"))

    def test_note_field_is_held_at_its_height_even_when_it_has_it_already(self) -> None:
        # A new editor's default height once matched one line; not held there, it took the editor's 192 px hint.
        dialog = self.open_dialog([NOTES[1]])
        edit = dialog._rows()[0].note_edit
        edit.setMinimumHeight(0)
        edit.setMaximumHeight(QWIDGETSIZE_MAX)
        edit.resize(edit.width(), edit.single_line_height())

        edit.fit_height()

        self.assertEqual(edit.maximumHeight(), edit.single_line_height())

    def test_note_field_grows_with_the_text_up_to_four_lines(self) -> None:
        lines = (1, 3, 4, 10)
        dialog = self.open_dialog([AsBuiltNote(date="02.04.2026", note="\n".join(["rida"] * n)) for n in lines])

        one, three, four, ten = (row.note_edit.height() for row in dialog._rows())

        self.assertLess(one, three)
        self.assertLess(three, four)
        self.assertEqual(four, ten)

    def test_dialog_opens_as_tall_as_its_notes_and_scrolls_a_long_list(self) -> None:
        short = self.open_dialog(NOTES[:1])
        longer = self.open_dialog(NOTES)
        many = self.open_dialog([AsBuiltNote(date="02.04.2026", note=f"märkus {n}") for n in range(40)])

        self.assertLess(short.height(), longer.height())
        self.assertEqual(short.width(), AsBuiltNotesEditorDialog.DIALOG_WIDTH)
        self.assertEqual(many.height(), many._height_limit())
        self.show(longer)
        self.assertEqual(longer._scroll_area.verticalScrollBar().maximum(), 0, "a short list must open without scrolling")
        self.show(many)
        self.assertGreater(many._scroll_area.verticalScrollBar().maximum(), 0)

    @staticmethod
    def settle() -> None:
        for _ in range(5):
            QApplication.processEvents()

    @staticmethod
    def fully_visible(dialog: AsBuiltNotesEditorDialog, widget: QWidget) -> bool:
        viewport = dialog._scroll_area.viewport()
        top = widget.mapTo(viewport, QPoint(0, 0)).y()
        return top >= 0 and top + widget.height() <= viewport.height()

    def test_new_notes_lengthen_the_window_until_the_screen_is_full_then_the_newest_stays_in_view(self) -> None:
        dialog = self.open_dialog(NOTES[:1])
        self.show(dialog)
        start = dialog.height()
        add = dialog.findChild(QPushButton, "AsBuiltNotesAddButton")

        with patch.object(dialog, "_height_limit", return_value=start + 80):
            add.click()
            self.settle()
            self.assertGreater(dialog.height(), start, "the first new note fits on the screen")
            self.assertEqual(dialog._scroll_area.verticalScrollBar().maximum(), 0)

            for _ in range(6):
                add.click()
                self.settle()

            self.assertEqual(dialog.height(), start + 80, "the window stops at the bottom of the screen")
            self.assertGreater(dialog._scroll_area.verticalScrollBar().maximum(), 0)
            self.assertTrue(self.fully_visible(dialog, dialog._rows()[-1]), "the newest note is scrolled into view")
            self.assertTrue(self.fully_visible(dialog, add))

    def test_a_note_growing_by_a_line_lengthens_the_window(self) -> None:
        dialog = self.open_dialog(NOTES[:2])
        self.show(dialog)
        start = dialog.height()

        dialog._rows()[1].note_edit.setPlainText("toru sügavus\nkontrollida K12\nja K14")
        self.settle()

        self.assertGreater(dialog.height(), start)
        self.assertEqual(dialog._scroll_area.verticalScrollBar().maximum(), 0)

    def test_deleting_notes_shortens_the_window(self) -> None:
        dialog = self.open_dialog(NOTES)
        self.show(dialog)
        start = dialog.height()

        dialog._rows()[3].delete_button.click()
        dialog._rows()[2].delete_button.click()
        self.settle()

        self.assertLess(dialog.height(), start)


if __name__ == "__main__":
    unittest.main()
