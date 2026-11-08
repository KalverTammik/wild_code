from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import re
from typing import Iterable


@dataclass
class AsBuiltNote:
    date: str = ""
    note: str = ""
    resolved: bool = False
    resolved_date: str = ""


class AsBuiltNotesService:
    """Read/write the structured AsBuilt notes section embedded in `description`.

    Kavitro edits descriptions in TipTap, so the section is written in TipTap's own schema: a bold title
    paragraph and a plain table whose resolved column holds a task item. TipTap drops comments, wrappers and
    inline styles on its first save, so none are written. Older sections that still carry them, and sections
    TipTap has already saved (colgroup, colspan, header cells), are read and replaced the same way.
    """

    DATE_FORMAT = "%d.%m.%Y"
    SECTION_TITLE = "🗒️ Märkused ja kommentaarid"
    # Part of the shared description, so in the product language rather than the plugin user's.
    TABLE_HEADERS = ("Kuupäev", "Märkus", "Lahendatud", "Lahendamise kuupäev")

    _SECTION_PATTERN = re.compile(
        r'(?:<!--\s*(?:kavitro:type=asbuilt-notes|mailabl:type=notes)\s*-->\s*)*'
        r'<p(?:\s[^>]*)?>\s*(?:<strong>)?\s*🗒️?\s*Märkused\s+ja\s+kommentaarid\s*(?:</strong>)?\s*</p>'
        r'\s*(?:<div(?:\s[^>]*)?>\s*)?<table(?:\s[^>]*)?>.*?</table>\s*(?:</div>\s*)?(?:<p>\s*</p>\s*)?',
        re.IGNORECASE | re.DOTALL,
    )
    _TABLE_PATTERN = re.compile(r'<table(?:\s[^>]*)?>(.*?)</table>', re.IGNORECASE | re.DOTALL)
    _ROW_PATTERN = re.compile(r'<tr(?:\s[^>]*)?>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
    # TipTap can turn a body cell into a header cell, so both are read.
    _CELL_PATTERN = re.compile(r'<t([dh])(?:\s[^>]*)?>(.*?)</t\1>', re.IGNORECASE | re.DOTALL)
    _BREAK_PATTERN = re.compile(r'<\s*br\s*/?\s*>', re.IGNORECASE)
    _PARAGRAPH_END_PATTERN = re.compile(r'</p\s*>', re.IGNORECASE)
    _TAG_PATTERN = re.compile(r'<[^>]+>')

    @classmethod
    def today_text(cls) -> str:
        return datetime.today().strftime(cls.DATE_FORMAT)

    @classmethod
    def parse_notes(cls, description_html: str | None) -> list[AsBuiltNote]:
        section = cls.extract_notes_section(description_html)
        if not section:
            return []

        table_match = cls._TABLE_PATTERN.search(section)
        if not table_match:
            return []

        rows = cls._ROW_PATTERN.findall(table_match.group(1))
        parsed: list[AsBuiltNote] = []
        # The first row is the header.
        for row_html in rows[1:]:
            cells = [content for _kind, content in cls._CELL_PATTERN.findall(row_html)]
            if len(cells) < 4:
                continue
            parsed.append(
                AsBuiltNote(
                    date=cls._html_to_plain_text(cells[0]),
                    note=cls._html_to_plain_text(cells[1]),
                    resolved=cls._checkbox_checked(cells[2]),
                    resolved_date=cls._html_to_plain_text(cells[3]),
                )
            )
        return parsed

    @classmethod
    def extract_notes_section(cls, description_html: str | None) -> str:
        description = cls._normalize_html(description_html)
        if not description:
            return ""
        match = cls._SECTION_PATTERN.search(description)
        return match.group(0).strip() if match else ""

    @classmethod
    def merge_notes_into_description(
        cls,
        existing_html: str | None,
        notes: Iterable[AsBuiltNote | dict],
    ) -> str:
        description = cls._normalize_html(existing_html)
        notes_section = cls.build_notes_html(notes)

        if cls._SECTION_PATTERN.search(description):
            # A function, not a template: notes hold UNC paths, and re.sub would read their backslashes as escapes.
            return cls._SECTION_PATTERN.sub(lambda _match: notes_section, description, count=1).strip()
        if not notes_section:
            return description
        return description + notes_section

    @classmethod
    def build_notes_html(cls, notes: Iterable[AsBuiltNote | dict]) -> str:
        normalized = [cls._coerce_note(note) for note in notes]
        content_notes = [note for note in normalized if cls._note_has_content(note)]
        if not content_notes:
            return ""

        header = "".join(f"<th>{cls._paragraph(text)}</th>" for text in cls.TABLE_HEADERS)
        rows = "".join(cls._render_table_row(note) for note in content_notes)
        return (
            f"<p><strong>{cls.SECTION_TITLE}</strong></p>"
            f"<table><tbody><tr>{header}</tr>{rows}</tbody></table>"
            "<p></p>"
        )

    @classmethod
    def _coerce_note(cls, note: AsBuiltNote | dict) -> AsBuiltNote:
        if isinstance(note, AsBuiltNote):
            return AsBuiltNote(
                date=cls._normalize_text(note.date),
                note=cls._normalize_text(note.note),
                resolved=bool(note.resolved),
                resolved_date=cls._normalize_text(note.resolved_date),
            )

        data = note if isinstance(note, dict) else {}
        resolved_raw = data.get("resolved")
        if isinstance(resolved_raw, bool):
            resolved = resolved_raw
        else:
            resolved = str(resolved_raw or "").strip().lower() in {"1", "true", "yes", "checked"}

        return AsBuiltNote(
            date=cls._normalize_text(data.get("date")),
            note=cls._normalize_text(data.get("note")),
            resolved=resolved,
            resolved_date=cls._normalize_text(data.get("resolved_date")),
        )

    @staticmethod
    def _normalize_html(value: str | None) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _normalize_text(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _note_has_content(note: AsBuiltNote) -> bool:
        return bool(note.note.strip() or note.resolved or note.resolved_date.strip())

    @classmethod
    def _html_to_plain_text(cls, cell_html: str) -> str:
        if not cell_html:
            return ""
        value = cls._BREAK_PATTERN.sub("\n", cell_html)
        value = cls._PARAGRAPH_END_PATTERN.sub("\n", value)
        value = cls._TAG_PATTERN.sub("", value)
        value = html.unescape(value)
        value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
        return value.strip()

    @staticmethod
    def _checkbox_checked(cell_html: str) -> bool:
        lowered = (cell_html or "").lower()
        return (
            'data-checked="true"' in lowered
            or 'checked="checked"' in lowered
            or re.search(r'<input[^>]*\bchecked\b', lowered) is not None
        )

    @staticmethod
    def _paragraph(value: str) -> str:
        # TipTap escapes only the markup characters in text and writes a line break as <br>.
        return f"<p>{html.escape(value or '', quote=False).replace(chr(10), '<br>')}</p>"

    @classmethod
    def _render_table_row(cls, note: AsBuiltNote) -> str:
        return (
            "<tr>"
            f"<td>{cls._paragraph(note.date)}</td>"
            f"<td>{cls._paragraph(note.note)}</td>"
            f"<td>{cls._render_checkbox_html(note.resolved)}</td>"
            f"<td>{cls._paragraph(note.resolved_date)}</td>"
            "</tr>"
        )

    @staticmethod
    def _render_checkbox_html(is_checked: bool) -> str:
        # TipTap's TaskItem markup, as Kavitro stores it.
        checked = ' checked="checked"' if is_checked else ""
        return (
            '<ul data-type="taskList">'
            f'<li data-checked="{str(bool(is_checked)).lower()}" data-type="taskItem">'
            f'<label><input type="checkbox"{checked}><span></span></label>'
            '<div><p></p></div>'
            '</li>'
            '</ul>'
        )
