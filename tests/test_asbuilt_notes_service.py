"""The as-built notes section of a Kavitro description: written in TipTap's schema, read back in every known form."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.modules.asbuilt.asbuilt_notes_service import AsBuiltNote, AsBuiltNotesService as Service

RESOLVED = AsBuiltNote(date="02.04.2026", note="kaev 47 viga", resolved=True, resolved_date="02.04.2026")
OPEN = AsBuiltNote(date="05.06.2026", note='esimene rida\nteine <rida> & "jutt"', resolved=False, resolved_date="")
TASK_ITEM_CHECKED = (
    '<ul data-type="taskList"><li data-checked="true" data-type="taskItem">'
    '<label><input type="checkbox" checked="checked"><span></span></label><div><p></p></div></li></ul>'
)

# What the plugin wrote before.
LEGACY_SECTION = (
    '<!-- kavitro:type=asbuilt-notes -->\n<!-- mailabl:type=notes -->\n'
    '<p style="font-size: 13px; font-weight: bold; margin: 14px 0 4px 6px;">🗒️ Märkused ja kommentaarid</p>\n'
    '<div style="width: 100%;">\n  <table style="width: 100%; border-collapse: collapse;">\n'
    '    <tr><td style="padding: 4px 6px;">📅</td><td style="padding: 4px 6px;">🗒️ Märkus</td>'
    '<td style="padding: 4px 6px;">✅</td><td style="padding: 4px 6px;">📅 Lahendatud</td></tr>\n'
    '    <tr><td style="padding: 4px 6px;"><p>02.04.2026</p></td><td style="padding: 4px 6px;"><p>kaev 47 viga</p></td>'
    f'<td style="padding: 4px 6px;">{TASK_ITEM_CHECKED}</td><td style="padding: 4px 6px;"><p>02.04.2026</p></td></tr>\n'
    '  </table>\n</div>\n<p></p>'
)

# The same section after a save in Kavitro's TipTap editor.
TIPTAP_SAVED_SECTION = (
    '<p><strong>🗒️ Märkused ja kommentaarid</strong></p>'
    '<table style="min-width: 100px"><colgroup><col style="min-width: 25px"><col style="min-width: 25px">'
    '<col style="min-width: 25px"><col style="min-width: 25px"></colgroup><tbody>'
    '<tr><th colspan="1" rowspan="1"><p>Kuupäev</p></th><th colspan="1" rowspan="1"><p>Märkus</p></th>'
    '<th colspan="1" rowspan="1"><p>Lahendatud</p></th><th colspan="1" rowspan="1"><p>Lahendamise kuupäev</p></th></tr>'
    '<tr><td colspan="1" rowspan="1"><p>02.04.2026</p></td><td colspan="1" rowspan="1"><p>kaev 47 viga</p></td>'
    f'<td colspan="1" rowspan="1">{TASK_ITEM_CHECKED}</td><td colspan="1" rowspan="1"><p>02.04.2026</p></td></tr>'
    '</tbody></table><p></p>'
)


class WrittenSectionTest(unittest.TestCase):
    def test_section_uses_only_markup_from_tiptaps_schema(self) -> None:
        section = Service.build_notes_html([RESOLVED, OPEN])

        self.assertTrue(section.startswith(
            "<p><strong>🗒️ Märkused ja kommentaarid</strong></p>"
            "<table><tbody><tr><th><p>Kuupäev</p></th><th><p>Märkus</p></th>"
            "<th><p>Lahendatud</p></th><th><p>Lahendamise kuupäev</p></th></tr>"
        ))
        self.assertTrue(section.endswith("</tbody></table><p></p>"))
        for foreign in ("<!--", "style=", "<div style", "\n"):
            with self.subTest(markup=foreign):
                self.assertNotIn(foreign, section)

    def test_resolved_column_is_a_tiptap_task_item(self) -> None:
        section = Service.build_notes_html([RESOLVED, OPEN])

        self.assertIn(f"<td>{TASK_ITEM_CHECKED}</td>", section)
        self.assertIn(
            '<li data-checked="false" data-type="taskItem"><label><input type="checkbox"><span></span></label>',
            section,
        )

    def test_text_is_escaped_the_way_tiptap_writes_it(self) -> None:
        section = Service.build_notes_html([OPEN])

        self.assertIn('<p>esimene rida<br>teine &lt;rida&gt; &amp; "jutt"</p>', section)

    def test_written_notes_read_back_unchanged(self) -> None:
        self.assertEqual(Service.parse_notes(Service.build_notes_html([RESOLVED, OPEN])), [RESOLVED, OPEN])

    def test_empty_rows_are_left_out(self) -> None:
        self.assertEqual(Service.build_notes_html([AsBuiltNote(date="01.01.2026")]), "")


class ReadSectionTest(unittest.TestCase):
    def test_section_written_by_earlier_versions(self) -> None:
        self.assertEqual(Service.parse_notes(f"<p>Enne</p>{LEGACY_SECTION}"), [RESOLVED])

    def test_section_saved_by_tiptap(self) -> None:
        self.assertEqual(Service.parse_notes(f"<p>Enne</p>{TIPTAP_SAVED_SECTION}<p>Pärast</p>"), [RESOLVED])

    def test_title_without_the_emoji_variation_selector(self) -> None:
        section = TIPTAP_SAVED_SECTION.replace("🗒️", "🗒")

        self.assertEqual(Service.parse_notes(section), [RESOLVED])

    def test_description_without_a_section(self) -> None:
        self.assertEqual(Service.parse_notes("<p>Ainult vaba tekst</p>"), [])
        self.assertEqual(Service.parse_notes(None), [])


class MergeTest(unittest.TestCase):
    def test_old_section_is_replaced_once_and_the_rest_stays(self) -> None:
        description = f"<p>Enne</p>{LEGACY_SECTION}<p>Pärast</p>"

        merged = Service.merge_notes_into_description(description, [RESOLVED, OPEN])

        self.assertEqual(merged.count("Märkused ja kommentaarid"), 1)
        self.assertTrue(merged.startswith("<p>Enne</p><p><strong>"))
        self.assertTrue(merged.endswith("<p>Pärast</p>"))
        self.assertNotIn("<!--", merged)
        self.assertEqual(Service.parse_notes(merged), [RESOLVED, OPEN])

    def test_section_saved_by_tiptap_is_replaced(self) -> None:
        merged = Service.merge_notes_into_description(TIPTAP_SAVED_SECTION, [OPEN])

        self.assertEqual(merged.count("Märkused ja kommentaarid"), 1)
        self.assertEqual(Service.parse_notes(merged), [OPEN])

    def test_unc_paths_survive_the_replacement(self) -> None:
        unc = AsBuiltNote(date="02.04.2026", note=r"Fail: \\laugas.tvv.sise\GISKAVITRO\2_are\joonis.pdf")

        merged = Service.merge_notes_into_description(LEGACY_SECTION, [unc])

        self.assertEqual(Service.parse_notes(merged), [unc])

    def test_section_is_added_after_the_description(self) -> None:
        merged = Service.merge_notes_into_description("<p>Kirjeldus</p>", [OPEN])

        self.assertTrue(merged.startswith("<p>Kirjeldus</p><p><strong>"))

    def test_without_notes_the_section_is_removed(self) -> None:
        merged = Service.merge_notes_into_description(f"<p>Enne</p>{TIPTAP_SAVED_SECTION}", [])

        self.assertEqual(merged, "<p>Enne</p>")


if __name__ == "__main__":
    unittest.main()
