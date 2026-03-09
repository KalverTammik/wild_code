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
    """Read/write the structured AsBuilt notes section embedded in `description`."""

    DATE_FORMAT = "%d.%m.%Y"
    SECTION_TITLE = "🗒️ Märkused ja kommentaarid"
    SECTION_MARKER = "kavitro:type=asbuilt-notes"
    LEGACY_SECTION_MARKER = "mailabl:type=notes"

    _SECTION_PATTERN = re.compile(
        r'(?:<!--\s*(?:kavitro:type=asbuilt-notes|mailabl:type=notes)\s*-->\s*)*'
        r'<p[^>]*?>\s*(?:<strong>)?\s*🗒️\s*Märkused\s+ja\s+kommentaarid\s*(?:</strong>)?\s*</p>'
        r'\s*(?:<div[^>]*?>\s*)?<table[^>]*?>.*?</table>\s*(?:</div>\s*)?(?:<p>\s*</p>\s*)?',
        re.IGNORECASE | re.DOTALL,
    )
    _TABLE_PATTERN = re.compile(r'<table[^>]*?>(.*?)</table>', re.IGNORECASE | re.DOTALL)
    _ROW_PATTERN = re.compile(r'<tr[^>]*?>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
    _CELL_PATTERN = re.compile(r'<td[^>]*?>(.*?)</td>', re.IGNORECASE | re.DOTALL)
    _BREAK_PATTERN = re.compile(r'<\s*br\s*/?\s*>', re.IGNORECASE)
    _PARAGRAPH_END_PATTERN = re.compile(r'</p\s*>', re.IGNORECASE)
    _TAG_PATTERN = re.compile(r'<[^>]+>')

    _TABLE_STYLE = (
        "width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; "
        "font-size: 12px;"
    )
    _HEADER_CELL_STYLE = (
        "padding: 4px 6px; font-weight: bold; background: #e5e7eb; border: 1px solid #cbd5e1; "
        "text-align: center; color: #333333;"
    )
    _BODY_CELL_STYLE = (
        "padding: 4px 6px; border: 1px solid #d1d5db; vertical-align: top;"
    )

    @classmethod
    def today_text(cls) -> str:
        return datetime.today().strftime(cls.DATE_FORMAT)

    @classmethod
    def parse_notes(cls, description_html: str | None) -> list[AsBuiltNote]:
        description = cls._normalize_html(description_html)
        if not description:
            return []

        section = cls.extract_notes_section(description)
        if not section:
            return []

        table_match = cls._TABLE_PATTERN.search(section)
        if not table_match:
            return []

        rows = cls._ROW_PATTERN.findall(table_match.group(1))
        if len(rows) <= 1:
            return []

        parsed: list[AsBuiltNote] = []
        for row_html in rows[1:]:
            cells = cls._CELL_PATTERN.findall(row_html)
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
            replacement = notes_section.strip()
            updated = cls._SECTION_PATTERN.sub(replacement, description, count=1)
            return updated.strip()

        if not notes_section:
            return description.strip()
        if not description:
            return notes_section.strip()
        return f"{description.rstrip()}\n\n{notes_section.strip()}"

    @classmethod
    def build_notes_html(cls, notes: Iterable[AsBuiltNote | dict]) -> str:
        normalized = [cls._coerce_note(note) for note in notes]
        content_notes = [note for note in normalized if cls._note_has_content(note)]
        if not content_notes:
            return ""

        rows_html = "".join(cls._render_table_row(note) for note in content_notes)
        return (
            f"<!-- {cls.SECTION_MARKER} -->\n"
            f"<!-- {cls.LEGACY_SECTION_MARKER} -->\n"
            f"<p style=\"font-size: 13px; font-weight: bold; margin: 14px 0 4px 6px;\">{cls.SECTION_TITLE}</p>\n"
            f"<div style=\"width: 100%;\">\n"
            f"  <table style=\"{cls._TABLE_STYLE}\">\n"
            f"    {cls._render_table_header()}\n"
            f"    {rows_html}\n"
            f"  </table>\n"
            f"</div>\n"
            f"<p></p>"
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
        return 'data-checked="true"' in lowered or 'checked="checked"' in lowered or "checked" in lowered

    @staticmethod
    def _plain_text_to_html(value: str) -> str:
        escaped = html.escape(value or "")
        return escaped.replace("\n", "<br/>")

    @classmethod
    def _render_table_header(cls) -> str:
        return (
            "<tr>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 15%;\">📅</td>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 60%; text-align: left;\">🗒️ Märkus</td>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 10%;\">✅</td>"
            f"<td style=\"{cls._HEADER_CELL_STYLE} width: 15%;\">📅 Lahendatud</td>"
            "</tr>"
        )

    @classmethod
    def _render_table_row(cls, note: AsBuiltNote) -> str:
        return (
            "<tr>"
            f"<td style=\"{cls._BODY_CELL_STYLE} text-align: center;\"><p>{cls._plain_text_to_html(note.date)}</p></td>"
            f"<td style=\"{cls._BODY_CELL_STYLE}\"><p>{cls._plain_text_to_html(note.note)}</p></td>"
            f"<td style=\"{cls._BODY_CELL_STYLE} text-align: center;\">{cls._render_checkbox_html(note.resolved)}</td>"
            f"<td style=\"{cls._BODY_CELL_STYLE} text-align: center;\"><p>{cls._plain_text_to_html(note.resolved_date)}</p></td>"
            "</tr>"
        )

    @staticmethod
    def _render_checkbox_html(is_checked: bool) -> str:
        checked_attr = 'checked="checked"' if is_checked else ""
        data_checked = str(bool(is_checked)).lower()
        return (
            '<ul data-type="taskList">'
            f'<li data-checked="{data_checked}" data-type="taskItem">'
            f'<label><input type="checkbox" {checked_attr}><span></span></label>'
            '<div><p></p></div>'
            '</li>'
            '</ul>'
        )
