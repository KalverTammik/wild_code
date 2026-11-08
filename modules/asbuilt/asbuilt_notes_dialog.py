from __future__ import annotations

import math

from PyQt5.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.form_grid import fit_dialog_to_content
from ...widgets.theme_manager import ThemeManager
from .asbuilt_notes_service import AsBuiltNote, AsBuiltNotesService

# AsBuiltNotesService.DATE_FORMAT in Qt's notation.
QT_DATE_FORMAT = "dd.MM.yyyy"

ROW_SPACING = 8
CHECK_WIDTH = 22
DATE_WIDTH = 116
DELETE_WIDTH = 28


class _GrowingNoteEdit(QTextEdit):
    """One line high for a one-line note; grows with the text up to MAX_LINES and scrolls after that.

    The heights depend on the stylesheet's padding, so fit_height() runs again once the dialog is styled.
    """

    MAX_LINES = 4

    heightChanged = pyqtSignal()

    def __init__(self, parent: QWidget | None = None, *, width_hint: int = 0) -> None:
        super().__init__(parent)
        # Until the editor is laid out its viewport is narrow, which would wrap the text into too many lines.
        self._width_hint = width_hint
        self.setAcceptRichText(False)
        # A note holds no tabs; Tab moves on to the date like in the other fields.
        self.setTabChangesFocus(True)
        # The stylesheet's padding spaces the text, as in the line edits next to it.
        self.document().setDocumentMargin(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.document().contentsChanged.connect(self.fit_height)
        self.fit_height()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self.fit_height()

    def single_line_height(self) -> int:
        _lines, line = self._measure()
        return self._height(line, 1)

    def fit_height(self) -> None:
        lines, line = self._measure()
        height = self._height(line, min(lines, self.MAX_LINES))
        # Compared with the limits, not the current height: a new editor's default height can match one line,
        # and without the limits the layout gives it the editor's 192 px hint.
        if (self.minimumHeight(), self.maximumHeight()) != (height, height):
            self.setFixedHeight(height)
            self.heightChanged.emit()

    def _measure(self) -> tuple[int, float]:
        """The text's lines at the editor's width, and the height of one line, read from a copy of the text.

        The editor's own document is rewrapped to the viewport by the editor whenever its layout finishes, so
        measured at another width it gave the lines of whichever width came last.
        """
        if self.isVisible():
            width = self.viewport().width()
        else:
            margins = self.contentsMargins()
            width = self._width_hint - margins.left() - margins.right()
        document = self.document().clone()
        document.setDefaultFont(self.document().defaultFont())
        document.setDocumentMargin(0)
        if width > 0:
            document.setTextWidth(width)
        document.idealWidth()  # finishes the layout
        lines = 0
        block = document.begin()
        while block.isValid():
            lines += max(block.layout().lineCount(), 1)
            block = block.next()
        lines = max(lines, 1)
        # Read from the laid out text, which includes the leading that the font metrics leave out.
        return lines, document.size().height() / lines

    def _height(self, line: float, lines: int) -> int:
        margins = self.contentsMargins()
        return math.ceil(line * lines) + margins.top() + margins.bottom()


class _NotesScrollArea(QScrollArea):
    """Asks for the height the dialog gives it as its minimum.

    QScrollArea keeps the list's first size as its hint, so after notes were deleted the window stayed tall.
    """

    def sizeHint(self):  # noqa: N802 - Qt override
        hint = super().sizeHint()
        hint.setHeight(self.minimumHeight())
        return hint


class _NoteRow(QFrame):
    """One note: resolved box, text, resolved date and delete, lined up with the first line of the text."""

    deleteRequested = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, note: AsBuiltNote, *, lang: LanguageManager, width_hint: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AsBuiltNoteRow")
        self.date_key = note.date
        self._toggled = False
        # A date on an open note is kept as it was until the box is used, so opening and saving changes nothing.
        self._kept_open_date = "" if note.resolved else note.resolved_date

        self.note_edit = _GrowingNoteEdit(self, width_hint=width_hint)
        self.note_edit.setObjectName("AsBuiltNoteTextEdit")
        self.note_edit.setPlaceholderText(lang.translate(TranslationKeys.ASBUILT_NOTES_PLACEHOLDER))
        self.note_edit.setPlainText(note.note)
        self.note_edit.textChanged.connect(self.stateChanged)

        self._check_cell = QWidget(self)
        self._check_cell.setFixedWidth(CHECK_WIDTH)
        check_layout = QHBoxLayout(self._check_cell)
        check_layout.setContentsMargins(0, 0, 0, 0)
        self.resolved_check = QCheckBox(self._check_cell)
        self.resolved_check.setObjectName("AsBuiltNoteResolvedCheckbox")
        self.resolved_check.setToolTip(lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED))
        self.resolved_check.setChecked(bool(note.resolved))
        check_layout.addWidget(self.resolved_check, 0, Qt.AlignCenter)

        self.date_edit = self._create_date_field(note.resolved_date)
        self.date_edit.setFixedWidth(DATE_WIDTH)
        # An open note shows no date, but its column keeps its place.
        date_policy = self.date_edit.sizePolicy()
        date_policy.setRetainSizeWhenHidden(True)
        self.date_edit.setSizePolicy(date_policy)

        self.delete_button = QToolButton(self)
        self.delete_button.setObjectName("AsBuiltNoteDeleteButton")
        self.delete_button.setIcon(ThemeManager.get_qicon(IconNames.ICON_DELETE))
        self.delete_button.setAutoRaise(True)
        self.delete_button.setFixedWidth(DELETE_WIDTH)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        delete_text = lang.translate(TranslationKeys.ASBUILT_NOTES_DELETE_ROW)
        self.delete_button.setToolTip(delete_text)
        self.delete_button.setAccessibleName(delete_text)
        self.delete_button.clicked.connect(self.deleteRequested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ROW_SPACING)
        layout.addWidget(self._check_cell, 0, Qt.AlignTop)
        layout.addWidget(self.note_edit, 1)
        layout.addWidget(self.date_edit, 0, Qt.AlignTop)
        layout.addWidget(self.delete_button, 0, Qt.AlignTop)

        self.resolved_check.toggled.connect(self._on_resolved_toggled)
        if self.resolved_check.isChecked() and not self._date_text():
            self._set_date_text(AsBuiltNotesService.today_text())
        self._show_resolved_state()

    def fit_to_style(self) -> None:
        """Sizes the row by the stylesheet on it: the fields beside the text are as tall as its first line."""
        self.note_edit.fit_height()
        line_height = self.note_edit.single_line_height()
        for widget in (self._check_cell, self.date_edit, self.delete_button):
            widget.setFixedHeight(line_height)

    def focus_chain(self) -> tuple[QWidget, ...]:
        return self.resolved_check, self.note_edit, self.date_edit, self.delete_button

    def _create_date_field(self, text: str) -> QWidget:
        parsed = QDate.fromString(text, QT_DATE_FORMAT) if text else QDate()
        if text and not parsed.isValid():
            # Typed by hand before the calendar field: kept as text, so nothing is lost.
            field = QLineEdit(text, self)
            field.setObjectName("AsBuiltNoteResolvedDateText")
            return field
        field = QDateEdit(self)
        field.setObjectName("AsBuiltNoteResolvedDateEdit")
        field.setCalendarPopup(True)
        field.setDisplayFormat(QT_DATE_FORMAT)
        # The minimum date stands for "no date" and shows blank.
        field.setSpecialValueText(" ")
        field.setDate(parsed if parsed.isValid() else field.minimumDate())
        return field

    def _date_text(self) -> str:
        if isinstance(self.date_edit, QLineEdit):
            return self.date_edit.text().strip()
        if self.date_edit.date() == self.date_edit.minimumDate():
            return ""
        return self.date_edit.date().toString(QT_DATE_FORMAT)

    def _set_date_text(self, text: str) -> None:
        if isinstance(self.date_edit, QLineEdit):
            self.date_edit.setText(text)
            return
        parsed = QDate.fromString(text, QT_DATE_FORMAT)
        self.date_edit.setDate(parsed if parsed.isValid() else self.date_edit.minimumDate())

    def _on_resolved_toggled(self, checked: bool) -> None:
        self._toggled = True
        if checked:
            if not self._date_text():
                self._set_date_text(AsBuiltNotesService.today_text())
        else:
            self._set_date_text("")
        self._show_resolved_state()
        self.stateChanged.emit()

    def _show_resolved_state(self) -> None:
        resolved = self.resolved_check.isChecked()
        self.date_edit.setVisible(resolved)
        # Resolved notes recede, so the open ones stand out.
        self.note_edit.setProperty("resolved", resolved)
        self.note_edit.style().unpolish(self.note_edit)
        self.note_edit.style().polish(self.note_edit)

    def is_open(self) -> bool:
        return not self.resolved_check.isChecked() and bool(self.note_edit.toPlainText().strip())

    def note(self) -> AsBuiltNote:
        resolved = self.resolved_check.isChecked()
        resolved_date = self._date_text() if resolved else ("" if self._toggled else self._kept_open_date)
        return AsBuiltNote(
            date=self.date_key,
            note=self.note_edit.toPlainText().strip(),
            resolved=resolved,
            resolved_date=resolved_date,
        )


class AsBuiltNotesEditorDialog(QDialog):
    DIALOG_WIDTH = 680
    MIN_LIST_HEIGHT = 120
    MARGIN = 16
    # Room left for the title bar and borders before the window is shown and its frame is known.
    WINDOW_FRAME = 40

    def __init__(
        self,
        *,
        item_name: str,
        notes: list[AsBuiltNote] | None = None,
        lang_manager=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._item_name = str(item_name or "")
        self._group_headers: dict[str, QWidget] = {}
        # The text column's width before the dialog is shown: the dialog minus margins and the fixed columns.
        self._note_width_hint = (
            self.DIALOG_WIDTH - 2 * self.MARGIN - CHECK_WIDTH - DATE_WIDTH - DELETE_WIDTH - 3 * ROW_SPACING
        )
        self._fitting = False
        self._shown = False
        self._row_to_reveal: _NoteRow | None = None
        # The list takes its new height from the window's resize, so a new note is scrolled to a turn later.
        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.setInterval(0)
        self._reveal_timer.timeout.connect(self._reveal_row)

        self.setObjectName("AsBuiltNotesEditorDialog")
        self.setModal(True)
        self.setWindowTitle(self._lang.translate(TranslationKeys.ASBUILT_UPDATE_NOTES_TITLE))

        self._build_ui()
        self._load_notes(notes or [])
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])
        self._fit_to_content(self.DIALOG_WIDTH)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        root.setSpacing(10)

        heading = QHBoxLayout()
        heading.setSpacing(12)
        item_name = QLabel(self._item_name, self)
        item_name.setObjectName("AsBuiltNotesItemName")
        item_name.setWordWrap(True)
        heading.addWidget(item_name, 1)
        self._open_count = QLabel(self)
        self._open_count.setObjectName("AsBuiltNotesOpenCount")
        heading.addWidget(self._open_count, 0, Qt.AlignRight | Qt.AlignVCenter)
        root.addLayout(heading)

        self._list = QWidget(self)
        self._list.setObjectName("AsBuiltNotesList")
        self._list_layout = QVBoxLayout(self._list)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        # In the scrolled list itself, so the columns stay over their fields when a scroll bar appears.
        self._list_layout.addWidget(self._create_column_headers())

        self._add_note_btn = QPushButton(self._lang.translate(TranslationKeys.ASBUILT_NOTES_ADD_NOTE), self._list)
        self._add_note_btn.setObjectName("AsBuiltNotesAddButton")
        self._add_note_btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_ADD))
        self._add_note_btn.setCursor(Qt.PointingHandCursor)
        self._add_note_btn.clicked.connect(self._add_note_for_today)
        self._list_layout.addWidget(self._add_note_btn, 0, Qt.AlignLeft)
        self._list_layout.addStretch(1)

        self._scroll_area = _NotesScrollArea(self)
        self._scroll_area.setObjectName("AsBuiltNotesScroll")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setWidget(self._list)
        root.addWidget(self._scroll_area, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch(1)
        self._cancel_btn = QPushButton(self._lang.translate(TranslationKeys.CANCEL_BUTTON), self)
        self._cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)
        self._save_btn = QPushButton(self._lang.translate(TranslationKeys.SAVE), self)
        self._save_btn.setProperty("variant", ButtonVariant.SUCCESS)
        self._save_btn.clicked.connect(self.accept)
        buttons.addWidget(self._save_btn)
        for button in (self._add_note_btn, self._cancel_btn, self._save_btn):
            button.setAutoDefault(False)
            button.setDefault(False)
        root.addLayout(buttons)

    def _create_column_headers(self) -> QWidget:
        headers = QWidget(self)
        layout = QHBoxLayout(headers)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ROW_SPACING)
        layout.addSpacing(CHECK_WIDTH)
        note_header = QLabel(self._lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_NOTE), headers)
        note_header.setObjectName("AsBuiltNotesColumnHeader")
        layout.addWidget(note_header, 1)
        resolved_header = QLabel(self._lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED), headers)
        resolved_header.setObjectName("AsBuiltNotesColumnHeader")
        resolved_header.setFixedWidth(DATE_WIDTH)
        layout.addWidget(resolved_header)
        layout.addSpacing(DELETE_WIDTH)
        return headers

    def _load_notes(self, notes: list[AsBuiltNote]) -> None:
        for note in notes:
            self._append_row(note)
        if notes:
            self._focus_first_open_note()
        else:
            self._add_note_for_today()
        self._update_open_count()

    def _focus_first_open_note(self) -> None:
        # The cursor starts at the end of the first open note; with none open, on the add button.
        first_open = next((row for row in self._rows() if row.is_open()), None)
        if first_open is None:
            self._add_note_btn.setFocus()
            return
        first_open.note_edit.moveCursor(QTextCursor.End)
        first_open.note_edit.setFocus()

    def _list_widgets(self) -> list[QWidget]:
        return [self._list_layout.itemAt(index).widget() for index in range(self._list_layout.count())]

    def _rows(self) -> list[_NoteRow]:
        return [widget for widget in self._list_widgets() if isinstance(widget, _NoteRow)]

    def _ensure_group(self, date_key: str) -> QWidget:
        existing = self._group_headers.get(date_key)
        if existing is not None:
            return existing

        header = QWidget(self._list)
        header.setObjectName("AsBuiltNotesGroup")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(8)
        title = QLabel(date_key or self._lang.translate(TranslationKeys.ASBUILT_NOTES_NO_DATE), header)
        title.setObjectName("AsBuiltNotesGroupTitle")
        layout.addWidget(title)
        line = QFrame(header)
        line.setObjectName("AsBuiltNotesGroupLine")
        line.setFixedHeight(1)
        layout.addWidget(line, 1, Qt.AlignVCenter)

        self._group_headers[date_key] = header
        self._list_layout.insertWidget(self._list_layout.indexOf(self._add_note_btn), header)
        # In the open dialog the layout would show it only a turn later, and the window would be fitted without it.
        header.show()
        return header

    def _append_row(self, note: AsBuiltNote) -> _NoteRow:
        header = self._ensure_group(note.date)
        widgets = self._list_widgets()
        index = widgets.index(header) + 1
        # After the group's last row.
        while index < len(widgets) and isinstance(widgets[index], _NoteRow):
            index += 1

        row = _NoteRow(note, lang=self._lang, width_hint=self._note_width_hint, parent=self._list)
        row.deleteRequested.connect(lambda row=row: self._delete_row(row))
        row.stateChanged.connect(self._update_open_count)
        self._list_layout.insertWidget(index, row)
        row.show()
        # A row added to the open dialog is measured with its stylesheet at once; the first ones again in
        # _fit_to_content, once the dialog is styled.
        row.ensurePolished()
        row.fit_to_style()
        # A note that grows by a line lengthens the open window like a new note does.
        row.note_edit.heightChanged.connect(self._refit_when_shown)
        self._update_tab_order()
        return row

    def _update_tab_order(self) -> None:
        # Rows are created after the buttons, so without this Tab would reach the notes last.
        chain = [widget for row in self._rows() for widget in row.focus_chain()]
        chain += [self._add_note_btn, self._cancel_btn, self._save_btn]
        for first, second in zip(chain, chain[1:]):
            QWidget.setTabOrder(first, second)

    def _add_note_for_today(self) -> None:
        row = self._append_row(AsBuiltNote(date=AsBuiltNotesService.today_text()))
        self._update_open_count()
        row.note_edit.setFocus()
        if self._shown:
            self._fit_to_content(self.width())
            self._row_to_reveal = row
            self._reveal_timer.start()

    def _reveal_row(self) -> None:
        row, self._row_to_reveal = self._row_to_reveal, None
        if row is None:
            return
        # The add button under the newest note comes into view with it.
        self._scroll_area.ensureWidgetVisible(self._add_note_btn)
        self._scroll_area.ensureWidgetVisible(row)

    def _delete_row(self, row: _NoteRow) -> None:
        self._list_layout.removeWidget(row)
        row.hide()
        row.deleteLater()
        if not any(other.date_key == row.date_key for other in self._rows()):
            header = self._group_headers.pop(row.date_key, None)
            if header is not None:
                self._list_layout.removeWidget(header)
                header.hide()
                header.deleteLater()
        self._update_open_count()
        self._refit_when_shown()

    def _update_open_count(self) -> None:
        rows = self._rows()
        open_notes = sum(1 for row in rows if row.is_open())
        if open_notes:
            text = self._lang.translate(TranslationKeys.ASBUILT_NOTES_OPEN_COUNT).format(count=open_notes)
        elif any(row.resolved_check.isChecked() for row in rows):
            text = self._lang.translate(TranslationKeys.ASBUILT_NOTES_ALL_RESOLVED)
        else:
            # A new, still empty note is neither open nor resolved.
            text = ""
        self._open_count.setText(text)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        # Only now are all rows shown at their real width. Qt shows them one by one, and a refit during that
        # counted the rows not yet shown as empty, so the window opened too short and the list scrolled.
        self._shown = True
        self._fit_to_content(self.width())

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().hideEvent(event)
        self._shown = False

    def _refit_when_shown(self) -> None:
        # Fitted once before opening; afterwards each change in the list's height refits the open window.
        if self._shown and not self._fitting:
            self._fit_to_content(self.width())

    def _fit_to_content(self, width: int) -> None:
        """As tall as the notes need, down to the bottom of the screen; beyond that the list scrolls."""
        self._fitting = True
        try:
            self.ensurePolished()
            for row in self._rows():
                row.fit_to_style()
            self._list_layout.activate()
            needed = self._list.sizeHint().height()
            if self.isVisible():
                # Everything but the list keeps its height, so an open window never grows past the screen first.
                needed = min(needed, self._height_limit() - (self.height() - self._scroll_area.height()))
            self._scroll_area.setMinimumHeight(max(needed, self.MIN_LIST_HEIGHT))
            fit_dialog_to_content(self, width)
            limit = self._height_limit()
            if self.height() > limit:
                # The list takes what the screen leaves and scrolls the rest.
                self._scroll_area.setMinimumHeight(self.MIN_LIST_HEIGHT)
                self.setMinimumSize(width, limit)
                self.resize(width, limit)
            self._keep_on_screen()
        finally:
            self._fitting = False

    def _height_limit(self) -> int:
        # The title bar and borders lie outside height().
        frame = max(self.frameGeometry().height() - self.height(), self.WINDOW_FRAME)
        return self.screen().availableGeometry().height() - frame

    def _keep_on_screen(self) -> None:
        # A taller window keeps its place unless its bottom would leave the screen; then it moves up.
        if not self.isVisible():
            return
        available = self.screen().availableGeometry()
        overflow = self.frameGeometry().bottom() - available.bottom()
        if overflow > 0:
            self.move(self.x(), max(available.top(), self.y() - overflow))

    def get_notes(self) -> list[AsBuiltNote]:
        return [row.note() for row in self._rows()]
