from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QFrame, QGridLayout, QLabel, QSizePolicy, QTextEdit, QVBoxLayout, QWidget


def _form_separator() -> QFrame:
    separator = QFrame()
    separator.setObjectName("FormSeparator")
    separator.setFixedHeight(1)
    return separator


class StackedFormGrid(QGridLayout):
    """Layout of the data entry dialogs: labels above the fields, each width given in twelfths of the row.

    Rows share the same twelve columns, so fields of different widths still line up on both edges.
    """

    COLUMNS = 12
    SPACING = 12
    LABEL_GAP = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        # Qt leaves out the spacing between two columns that no row splits, so rows split in different ways
        # gave spans of the same size different widths. A fixed gap column between every two keeps each gap.
        self.setHorizontalSpacing(0)
        self.setVerticalSpacing(10)
        for column in range(self.COLUMNS):
            self.setColumnStretch(2 * column, 1)
        for gap in range(self.COLUMNS - 1):
            self.setColumnMinimumWidth(2 * gap + 1, self.SPACING)
        self._next_row = 0

    def add_fields(self, *fields: tuple[str, QWidget, int]) -> list[QLabel]:
        labels = []
        column = 0
        for text, field, span in fields:
            label = QLabel(text)
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            # The span alone sets the width: a long value must not widen its column and break the line-up.
            policy = field.sizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Ignored)
            field.setSizePolicy(policy)
            cell = QVBoxLayout()
            cell.setSpacing(self.LABEL_GAP)
            cell.addWidget(label)
            cell.addWidget(field)
            self.addLayout(cell, self._next_row, 2 * column, 1, 2 * span - 1)
            labels.append(label)
            column += span
        self._next_row += 1
        return labels

    def add_text_area(self, text: str, field: QWidget) -> QLabel:
        label = self.add_fields((text, field, self.COLUMNS))[0]
        self.setRowStretch(self._next_row - 1, 1)
        return label

    def add_separator(self) -> None:
        self.addWidget(_form_separator(), self._next_row, 0, 1, 2 * self.COLUMNS - 1)
        self._next_row += 1


class CompactTextEdit(QTextEdit):
    """Opens at its minimum height instead of the editor's 192 px and grows with the window."""

    def sizeHint(self):  # noqa: N802 - Qt override
        hint = super().sizeHint()
        hint.setHeight(self.minimumHeight())
        return hint


def fit_dialog_to_content(dialog: QDialog, width: int) -> None:
    # Nested layouts keep the hints they first read, from before the stylesheet fonts, until a layout is activated.
    # Measured without this, the form opens too short or too tall. Inner layouts first: the outer ones read them.
    dialog.ensurePolished()
    for widget in (*reversed(dialog.findChildren(QWidget)), dialog):
        layout = widget.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
    # The layout's minimum height leaves out wrapped labels, which slid the form under the buttons.
    height = dialog.layout().totalHeightForWidth(width)
    dialog.setMinimumSize(width, height)
    dialog.resize(width, height)
