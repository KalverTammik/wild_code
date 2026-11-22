"""Marks the text inputs of a data entry form whose value the map layer field would not store.

The check runs while the form is filled, with the same rules as the layer save (`coerce_field_value`),
so a value the save would leave empty never leaves the form.
"""
from __future__ import annotations

from functools import partial
from typing import Callable, Optional

from PyQt5.QtWidgets import QLineEdit, QStackedWidget, QTabWidget, QWidget

from ..languages.translation_keys import TranslationKeys
from ..utils.layers.field_value_problems import expected_text, problem_line
from ..utils.layers.module_layer_service_base import FieldValueProblem
from ..ui.messages_helper import ModernMessageDialog

# Form values by form key -> the problem per key the save would hit; keys without a problem are left out.
FormValueValidator = Callable[[dict[str, object]], dict[str, FieldValueProblem]]


def _reveal(widget: QWidget) -> None:
    # Focus alone does not switch tabs, so a wrong value on the other tab would stay out of sight.
    child = widget
    parent = child.parentWidget()
    while parent is not None:
        tabs = parent.parentWidget()
        if isinstance(parent, QStackedWidget) and isinstance(tabs, QTabWidget):
            tabs.setCurrentIndex(tabs.indexOf(child))
        child, parent = parent, parent.parentWidget()


class FormValueCheck:
    """Red frame and a tooltip on each input whose value does not fit; one warning on save.

    A field is checked when the user leaves it, not on every key press, so a half-typed value is not
    marked. A marked field is checked on every change, so the mark goes as soon as the value fits.
    """

    STATE_PROPERTY = "validationState"
    STATE_ERROR = "error"

    def __init__(self, validator: FormValueValidator, inputs: dict[str, tuple[QLineEdit, str]], lang) -> None:
        """`inputs`: form key -> (line edit, label the form shows for it), in the form's order."""
        self._validator = validator
        self._inputs = dict(inputs)
        self._lang = lang
        self._own_tooltips = {key: widget.toolTip() for key, (widget, _label) in self._inputs.items()}
        self._marked: dict[str, FieldValueProblem] = {}
        for key, (widget, _label) in self._inputs.items():
            widget.editingFinished.connect(partial(self._check, key))
            widget.textChanged.connect(partial(self._recheck_marked, key))

    def check_all(self) -> list[str]:
        """Marks every input; the keys that do not fit, in the form's order."""
        problems = self._validator({key: widget.text().strip() for key, (widget, _label) in self._inputs.items()})
        for key in self._inputs:
            self._mark(key, problems.get(key))
        return [key for key in self._inputs if key in problems]

    def confirm(self, parent: Optional[QWidget] = None) -> bool:
        """True when every value fits; otherwise one warning names them and the first one gets the focus."""
        invalid = self.check_all()
        if not invalid:
            return True
        lines = "\n".join(problem_line(self._marked[key], self._lang, field=self._inputs[key][1]) for key in invalid)
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.FORM_VALUE_INVALID_TITLE),
            self._lang.translate(TranslationKeys.FORM_VALUE_INVALID_MESSAGE).format(fields=lines),
            parent=parent,
        )
        first = self._inputs[invalid[0]][0]
        _reveal(first)
        first.setFocus()
        first.selectAll()
        return False

    def _check(self, key: str) -> None:
        widget = self._inputs[key][0]
        self._mark(key, self._validator({key: widget.text().strip()}).get(key))

    def _recheck_marked(self, key: str, _text: str) -> None:
        if key in self._marked:
            self._check(key)

    def _mark(self, key: str, problem: Optional[FieldValueProblem]) -> None:
        widget = self._inputs[key][0]
        if problem is None:
            self._marked.pop(key, None)
            tooltip, state = self._own_tooltips[key], ""
        else:
            self._marked[key] = problem
            tooltip = self._lang.translate(TranslationKeys.FORM_VALUE_INVALID_TOOLTIP).format(
                expected=expected_text(problem, self._lang)
            )
            state = self.STATE_ERROR
        widget.setToolTip(tooltip)
        if widget.property(self.STATE_PROPERTY) == state:
            return
        widget.setProperty(self.STATE_PROPERTY, state)
        # A dynamic property changes the stylesheet match only after a repolish.
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
