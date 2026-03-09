from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...constants.button_props import ButtonVariant
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from .asbuilt_notes_service import AsBuiltNote, AsBuiltNotesService


class AsBuiltNotesEditorDialog(QDialog):
    NOTE_MIN_HEIGHT = 64
    RESOLVED_COLUMN_WIDTH = 90
    RESOLVED_DATE_WIDTH = 130
    DELETE_WIDTH = 110

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
        self._group_boxes: dict[str, QGroupBox] = {}

        self.setObjectName("AsBuiltNotesEditorDialog")
        self.setModal(True)
        self.setWindowTitle(self._lang.translate(TranslationKeys.ASBUILT_UPDATE_NOTES_TITLE))
        self.resize(860, 560)

        self._build_ui()
        self._load_notes(notes or [])

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.MODULE_INFO])

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        intro = QLabel(
            self._lang.translate(TranslationKeys.ASBUILT_UPDATE_NOTES_LABEL).format(
                name=self._item_name
            )
        )
        intro.setWordWrap(True)
        intro.setObjectName("AsBuiltNotesIntro")
        layout.addWidget(intro)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        self._groups_container = QWidget(self._scroll_area)
        self._groups_layout = QVBoxLayout(self._groups_container)
        self._groups_layout.setContentsMargins(0, 0, 0, 0)
        self._groups_layout.setSpacing(8)
        self._groups_layout.addStretch(1)

        self._scroll_area.setWidget(self._groups_container)
        layout.addWidget(self._scroll_area, 1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)

        self._add_note_btn = QPushButton(
            self._lang.translate(TranslationKeys.ASBUILT_NOTES_ADD_NOTE)
        )
        self._add_note_btn.setProperty("variant", ButtonVariant.PRIMARY)
        self._add_note_btn.clicked.connect(self._add_note_for_today)
        buttons.addWidget(self._add_note_btn)

        buttons.addStretch(1)

        self._cancel_btn = QPushButton(self._lang.translate(TranslationKeys.CANCEL_BUTTON))
        self._cancel_btn.setProperty("variant", ButtonVariant.GHOST)
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)

        self._save_btn = QPushButton(self._lang.translate(TranslationKeys.SAVE))
        self._save_btn.setProperty("variant", ButtonVariant.SUCCESS)
        self._save_btn.clicked.connect(self.accept)
        buttons.addWidget(self._save_btn)

        for button in (self._add_note_btn, self._cancel_btn, self._save_btn):
            button.setAutoDefault(False)
            button.setDefault(False)

        layout.addLayout(buttons)

    def _load_notes(self, notes: list[AsBuiltNote]) -> None:
        if not notes:
            self._add_note_for_today()
            return

        grouped: dict[str, list[AsBuiltNote]] = {}
        for note in notes:
            grouped.setdefault(note.date, []).append(note)

        for date_key, group_notes in grouped.items():
            group_box = self._ensure_group(date_key)
            group_layout = group_box.layout()
            if group_layout is None:
                continue
            for note in group_notes:
                group_layout.addWidget(self._create_note_row(note))

    def _ensure_group(self, date_key: str) -> QGroupBox:
        key = str(date_key or "").strip()
        existing = self._group_boxes.get(key)
        if existing is not None:
            return existing

        group_box = QGroupBox(self._group_title(key), self._groups_container)
        group_box.setProperty("noteDate", key)

        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(8, 12, 8, 8)
        group_layout.setSpacing(6)
        group_layout.addWidget(self._create_headers(group_box))

        self._group_boxes[key] = group_box
        self._groups_layout.insertWidget(max(0, self._groups_layout.count() - 1), group_box)
        return group_box

    def _create_headers(self, parent: QWidget) -> QWidget:
        frame = QFrame(parent)
        frame.setObjectName("AsBuiltNotesHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        note_label = QLabel(
            f"🗒️ {self._lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_NOTE)}",
            frame,
        )
        layout.addWidget(note_label, 1)

        resolved_label = QLabel(
            f"✅ {self._lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED)}",
            frame,
        )
        resolved_label.setAlignment(Qt.AlignCenter)
        resolved_label.setFixedWidth(self.RESOLVED_COLUMN_WIDTH)
        layout.addWidget(resolved_label)

        resolved_date_label = QLabel(
            f"📅 {self._lang.translate(TranslationKeys.ASBUILT_NOTES_COLUMN_RESOLVED_DATE)}",
            frame,
        )
        resolved_date_label.setAlignment(Qt.AlignCenter)
        resolved_date_label.setFixedWidth(self.RESOLVED_DATE_WIDTH)
        layout.addWidget(resolved_date_label)

        delete_label = QLabel("", frame)
        delete_label.setFixedWidth(self.DELETE_WIDTH)
        layout.addWidget(delete_label)
        return frame

    def _create_note_row(self, note: AsBuiltNote | None = None) -> QFrame:
        row_note = note or AsBuiltNote()

        row = QFrame(self._groups_container)
        row.setProperty("noteRow", True)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        note_edit = QTextEdit(row)
        note_edit.setObjectName("AsBuiltNoteTextEdit")
        note_edit.setMinimumHeight(self.NOTE_MIN_HEIGHT)
        note_edit.setPlaceholderText(
            self._lang.translate(TranslationKeys.ASBUILT_NOTES_PLACEHOLDER)
        )
        note_edit.setPlainText(row_note.note)
        layout.addWidget(note_edit, 1)

        resolved_wrap = QWidget(row)
        resolved_wrap.setFixedWidth(self.RESOLVED_COLUMN_WIDTH)
        resolved_layout = QHBoxLayout(resolved_wrap)
        resolved_layout.setContentsMargins(0, 0, 0, 0)
        resolved_layout.setAlignment(Qt.AlignCenter)

        resolved_checkbox = QCheckBox(resolved_wrap)
        resolved_checkbox.setObjectName("AsBuiltNoteResolvedCheckbox")
        resolved_checkbox.setChecked(bool(row_note.resolved))
        resolved_layout.addWidget(resolved_checkbox)
        layout.addWidget(resolved_wrap)

        resolved_date_edit = QLineEdit(row)
        resolved_date_edit.setObjectName("AsBuiltNoteResolvedDateEdit")
        resolved_date_edit.setFixedWidth(self.RESOLVED_DATE_WIDTH)
        resolved_date_edit.setPlaceholderText(AsBuiltNotesService.today_text())
        resolved_date_edit.setText(row_note.resolved_date)
        layout.addWidget(resolved_date_edit)

        delete_btn = QPushButton(
            self._lang.translate(TranslationKeys.ASBUILT_NOTES_DELETE_ROW),
            row,
        )
        delete_btn.setProperty("variant", ButtonVariant.DANGER)
        delete_btn.setFixedWidth(self.DELETE_WIDTH)
        delete_btn.setAutoDefault(False)
        delete_btn.setDefault(False)
        delete_btn.clicked.connect(lambda _=False, widget=row: self._delete_row(widget))
        layout.addWidget(delete_btn)

        def _on_resolved_changed(state: int) -> None:
            if state == Qt.Checked:
                if not resolved_date_edit.text().strip():
                    resolved_date_edit.setText(AsBuiltNotesService.today_text())
                return
            resolved_date_edit.clear()

        resolved_checkbox.stateChanged.connect(_on_resolved_changed)
        if resolved_checkbox.isChecked() and not resolved_date_edit.text().strip():
            resolved_date_edit.setText(AsBuiltNotesService.today_text())

        return row

    def _add_note_for_today(self) -> None:
        group_box = self._ensure_group(AsBuiltNotesService.today_text())
        group_layout = group_box.layout()
        if group_layout is None:
            return
        group_layout.addWidget(self._create_note_row())
        self._scroll_area.ensureWidgetVisible(group_box)

    def _delete_row(self, row_widget: QWidget) -> None:
        group_box = row_widget.parentWidget()
        if not isinstance(group_box, QGroupBox):
            return

        group_layout = group_box.layout()
        if group_layout is None:
            return

        group_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()

        if self._count_note_rows(group_box) > 0:
            return

        date_key = str(group_box.property("noteDate") or "")
        self._group_boxes.pop(date_key, None)
        self._groups_layout.removeWidget(group_box)
        group_box.setParent(None)
        group_box.deleteLater()

    def _count_note_rows(self, group_box: QGroupBox) -> int:
        layout = group_box.layout()
        if layout is None:
            return 0
        count = 0
        for index in range(layout.count()):
            widget = layout.itemAt(index).widget()
            if isinstance(widget, QFrame) and bool(widget.property("noteRow")):
                count += 1
        return count

    def _group_title(self, date_key: str) -> str:
        stripped = str(date_key or "").strip()
        if stripped:
            return stripped
        return f"📅 {self._lang.translate(TranslationKeys.ASBUILT_NOTES_NO_DATE)}"

    def get_notes(self) -> list[AsBuiltNote]:
        collected: list[AsBuiltNote] = []
        for group_box in self._iter_groups():
            date_key = str(group_box.property("noteDate") or "")
            group_layout = group_box.layout()
            if group_layout is None:
                continue

            for index in range(group_layout.count()):
                row = group_layout.itemAt(index).widget()
                if not isinstance(row, QFrame) or not bool(row.property("noteRow")):
                    continue

                note_edit = row.findChild(QTextEdit, "AsBuiltNoteTextEdit")
                resolved_checkbox = row.findChild(QCheckBox, "AsBuiltNoteResolvedCheckbox")
                resolved_date_edit = row.findChild(QLineEdit, "AsBuiltNoteResolvedDateEdit")
                if note_edit is None or resolved_checkbox is None or resolved_date_edit is None:
                    continue

                collected.append(
                    AsBuiltNote(
                        date=date_key,
                        note=note_edit.toPlainText().strip(),
                        resolved=resolved_checkbox.isChecked(),
                        resolved_date=resolved_date_edit.text().strip(),
                    )
                )
        return collected

    def _iter_groups(self) -> list[QGroupBox]:
        groups: list[QGroupBox] = []
        for index in range(self._groups_layout.count()):
            widget = self._groups_layout.itemAt(index).widget()
            if isinstance(widget, QGroupBox):
                groups.append(widget)
        return groups
