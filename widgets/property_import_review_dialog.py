"""Collect explicit choices after the automatic property import has finished."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView,
                             QLabel, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout)

from ..constants.file_paths import QssPaths
from ..languages.translation_keys import TranslationKeys as K
from .theme_manager import ThemeManager
from .DateHelpers import DateHelpers


class PropertyImportReviewDialog(QDialog):
    def __init__(self, decisions, *, lang_manager, parent=None):
        super().__init__(parent)
        self.decisions = decisions
        self.lang = lang_manager
        tr = self.lang.translate
        self.setWindowTitle(tr(K.PROPERTY_IMPORT_REVIEW_TITLE))
        self.resize(850, 680)
        layout = QVBoxLayout(self)
        intro = QLabel(tr(K.PROPERTY_IMPORT_REVIEW_INTRO))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.table = QTableWidget(len(decisions), 3)
        self.table.setHorizontalHeaderLabels([tr(K.PROPERTY_ARCHIVE_PLAN_COLUMN_TUNNUS),
                                              tr(K.PROPERTY_IMPORT_REASON), tr(K.PROPERTY_IMPORT_ACTION)])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().hide()
        self.choices = []
        for row, item in enumerate(decisions):
            self.table.setItem(row, 0, QTableWidgetItem(item['tunnus']))
            reason = tr(item['reason'])
            if item.get('changed'):
                reason = tr(K.PROPERTY_IMPORT_CHANGED) + '\n' + reason
            self.table.setItem(row, 1, QTableWidgetItem(reason))
            choice = QComboBox()
            choice.addItem(tr(K.PROPERTY_IMPORT_LATER), 'later')
            choice.addItem(tr(K.PROPERTY_IMPORT_KEEP), 'keep')
            if item['reason'] == K.PROPERTY_ADD_BACKEND_DIFFERS:
                choice.addItem(tr(K.PROPERTY_IMPORT_APPLY), 'apply')
            choice.currentIndexChanged.connect(self._update_confirm)
            self.choices.append(choice)
            self.table.setCellWidget(row, 2, choice)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.resizeRowsToContents()
        layout.addWidget(self.table, 1)

        # One decision for the whole list; a row that cannot take it keeps its own.
        bulk_row = QHBoxLayout()
        bulk_row.addWidget(QLabel(tr(K.PROPERTY_IMPORT_BULK_LABEL)))
        self.bulk_choice = QComboBox()
        self.bulk_choice.addItem(tr(K.PROPERTY_IMPORT_LATER), 'later')
        self.bulk_choice.addItem(tr(K.PROPERTY_IMPORT_KEEP), 'keep')
        if any(item['reason'] == K.PROPERTY_ADD_BACKEND_DIFFERS for item in decisions):
            self.bulk_choice.addItem(tr(K.PROPERTY_IMPORT_APPLY), 'apply')
        bulk_row.addWidget(self.bulk_choice)
        bulk_button = QPushButton(tr(K.PROPERTY_IMPORT_BULK_SET))
        bulk_button.setAutoDefault(False)
        bulk_button.clicked.connect(self._set_all)
        bulk_row.addWidget(bulk_button)
        self.bulk_note = QLabel('')
        self.bulk_note.setWordWrap(True)
        bulk_row.addWidget(self.bulk_note, 1)
        layout.addLayout(bulk_row)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details, 1)
        scope = QLabel(tr(K.PROPERTY_IMPORT_WRITE_SCOPE))
        scope.setTextFormat(Qt.PlainText)
        scope.setWordWrap(True)
        layout.addWidget(scope)
        buttons = QHBoxLayout()
        buttons.addStretch()
        later = QPushButton(tr(K.PROPERTY_IMPORT_LATER))
        later.clicked.connect(self.reject)
        buttons.addWidget(later)
        self.confirm = QPushButton(tr(K.PROPERTY_IMPORT_CONFIRM))
        self.confirm.setEnabled(False)
        self.confirm.setAutoDefault(False)
        self.confirm.clicked.connect(self.accept)
        buttons.addWidget(self.confirm)
        layout.addLayout(buttons)
        self.table.currentCellChanged.connect(self._show_details)
        if decisions:
            self.table.selectRow(0)
        ThemeManager.apply_app_style(self, [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.COMBOBOX])

    def _set_all(self):
        action = self.bulk_choice.currentData()
        applied = 0
        for choice in self.choices:
            index = choice.findData(action)
            if index < 0:
                continue
            choice.setCurrentIndex(index)
            applied += 1
        skipped = len(self.choices) - applied
        self.bulk_note.setText(self.lang.translate(
            K.PROPERTY_IMPORT_BULK_SKIPPED).format(count=skipped) if skipped else '')
        self._update_confirm()

    def _update_confirm(self):
        self.confirm.setEnabled(any(choice.currentData() != 'later' for choice in self.choices))

    def _show_details(self, row, *_args):
        if row < 0:
            return
        item = self.decisions[row]
        unknown = self.lang.translate(K.PROPERTY_IMPORT_UNKNOWN)
        values = {key: str(item.get(key) or unknown) for key in (
            'tunnus', 'import_address', 'import_date', 'backend_address', 'backend_date',
            'main_address', 'main_date')}
        for key in ('import_date', 'backend_date', 'main_date'):
            values[key] = DateHelpers().date_to_iso_string(item.get(key)) or unknown
        text = self.lang.translate(K.PROPERTY_IMPORT_DETAILS).format(**values)
        info = item['backend_info']
        matches = (info.get('active_properties') or []) + (info.get('archived_properties') or [])
        if len(matches) > 1:
            text += '\n\n' + self.lang.translate(K.PROPERTY_IMPORT_MATCHES).format(matches='; '.join(
                str(match.get('id') or '') + ' — ' + str(match.get('displayAddress') or '') for match in matches))
        self.details.setPlainText(text)

    def selected_decisions(self):
        return {item['tunnus']: choice.currentData() for item, choice in zip(self.decisions, self.choices)
                if choice.currentData() != 'later'}
