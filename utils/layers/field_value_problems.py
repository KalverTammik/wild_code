"""The user's note about values a layer save left empty (see `FieldValueProblem`).

Text only, plus one show call through the dialogs the UI caller hands in: services return the problems,
the flow that saved tells the user once, together with its own success text.
"""
from __future__ import annotations

from typing import Iterable, Optional

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..user_dialogs import UserDialogs
from .module_layer_service_base import FieldValueProblem

# More lines would push the dialog's button off a laptop screen.
MAX_LISTED = 10

_EXPECTED_KEYS = {
    FieldValueProblem.NUMBER: TranslationKeys.FIELD_VALUE_EXPECTED_NUMBER,
    FieldValueProblem.INTEGER: TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER,
    FieldValueProblem.YES_NO: TranslationKeys.FIELD_VALUE_EXPECTED_YES_NO,
    FieldValueProblem.DATE: TranslationKeys.FIELD_VALUE_EXPECTED_DATE,
    FieldValueProblem.DATE_TIME: TranslationKeys.FIELD_VALUE_EXPECTED_DATE_TIME,
}


def _unique(problems: Iterable[FieldValueProblem]) -> list[FieldValueProblem]:
    # A save may write the same field twice (a default, then the form value); the user needs it once.
    seen: set[tuple[str, str]] = set()
    unique: list[FieldValueProblem] = []
    for problem in problems or ():
        key = (problem.field_name, problem.raw_value)
        if key not in seen:
            seen.add(key)
            unique.append(problem)
    return unique


def expected_text(problem: FieldValueProblem, lang) -> str:
    """What the field takes, as the user reads it ("a whole number")."""
    return lang.translate(_EXPECTED_KEYS[problem.expected])


def problem_line(problem: FieldValueProblem, lang, *, field: str = "") -> str:
    """One listed problem; `field` names it as the form does, otherwise the layer's own label is used."""
    return lang.translate(TranslationKeys.FIELD_VALUE_PROBLEM_LINE).format(
        field=field or problem.field_label or problem.field_name,
        value=problem.raw_value,
        expected=expected_text(problem, lang),
    )


def field_value_problems_note(problems: Iterable[FieldValueProblem]) -> str:
    """Which fields stayed empty, what was rejected, what was expected and what to do; empty when nothing was."""
    listed = _unique(problems)
    if not listed:
        return ""
    lang = LanguageManager()
    lines =[lang.translate(TranslationKeys.FIELD_VALUE_PROBLEMS_INTRO)]
    for problem in listed[:MAX_LISTED]:
        lines.append(problem_line(problem, lang))
    if len(listed) > MAX_LISTED:
        lines[-1] += lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=len(listed) - MAX_LISTED)
    lines.append(lang.translate(TranslationKeys.FIELD_VALUE_PROBLEMS_HINT))
    return "\n".join(lines)


def with_field_value_problems(message: str, problems: Iterable[FieldValueProblem]) -> str:
    """`message` followed by the note, so a flow shows one dialog, not its own and then this one."""
    note = field_value_problems_note(problems)
    if not note:
        return message
    return f"{message}\n\n{note}" if message else note


def show_saved(
    dialogs: UserDialogs,
    *,
    title: str,
    message: str,
    problems: Optional[Iterable[FieldValueProblem]],
) -> None:
    """The success message of a save; a warning naming the empty fields when some value was rejected."""
    listed = _unique(problems or ())
    if not listed:
        dialogs.show_info(title, message)
        return
    lang = LanguageManager()
    dialogs.show_warning(
        lang.translate(TranslationKeys.FIELD_VALUE_PROBLEMS_TITLE),
        with_field_value_problems(message, listed),
    )
