"""Pure helpers for resolving project values and rendering folder rules."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional


DEFAULT_PROJECT_FOLDER_RULE = "PROJECT_NUMBER + PROJECT_NAME"
PROJECT_NAME_COMPONENT = "PROJECT_NAME"
PROJECT_NUMBER_COMPONENT = "PROJECT_NUMBER"
SYMBOL_COMPONENT = "SYMBOL"


class MissingProjectNumberError(ValueError):
    """Raised when the active folder rule requires an unavailable number."""


def resolve_project_number(item_data: Any) -> Optional[str]:
    """Return a project number from either supported GraphQL field name."""

    if not isinstance(item_data, Mapping):
        return None

    for key in ("projectNumber", "number"):
        value = item_data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def build_project_folder_name(
    rule: object,
    *,
    project_name: object = "",
    project_number: object = "",
) -> str:
    """Render a saved three-slot project folder naming rule."""

    resolved_rule = str(rule or "").strip() or DEFAULT_PROJECT_FOLDER_RULE
    components = [part.strip() for part in resolved_rule.split(" + ") if part.strip()]
    folder_name_parts: list[str] = []

    for component in components:
        if component.startswith(f"{SYMBOL_COMPONENT}(") and component.endswith(")"):
            symbol = component[len(SYMBOL_COMPONENT) + 1 : -1]
            if symbol:
                folder_name_parts.append(symbol)
        elif component == PROJECT_NUMBER_COMPONENT:
            number_text = str(project_number or "").strip()
            if not number_text:
                raise MissingProjectNumberError()
            folder_name_parts.append(number_text)
        elif component == PROJECT_NAME_COMPONENT:
            folder_name_parts.append(str(project_name or "").strip())

    if not folder_name_parts and resolved_rule != DEFAULT_PROJECT_FOLDER_RULE:
        return build_project_folder_name(
            DEFAULT_PROJECT_FOLDER_RULE,
            project_name=project_name,
            project_number=project_number,
        )

    return "".join(folder_name_parts)
