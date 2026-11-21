from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterable, Optional

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...module_manager import ModuleManager
from ...python.responses import DataDisplayExtractors
from ...utils.url_manager import Module
from ..Property.query_cordinator import PropertiesConnectedElementsQueries, PropertyLookupService
from .project_board_status_rules import ProjectBoardStatusRules


class ProjectBoardOverviewService:
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    TODO_COLOR = "#1E88E5"
    IN_PROGRESS_COLOR = "#FBC02D"
    DONE_COLOR = "#43A047"

    @classmethod
    def build_project_board_data(cls, item_data: Optional[dict], *, lang_manager=None) -> dict[str, Any]:
        lang = lang_manager or LanguageManager()
        project = item_data if isinstance(item_data, dict) else {}
        project_id = str(project.get("id") or "").strip()
        property_numbers = cls._project_property_numbers(project)

        todo_title = lang.translate(TranslationKeys.PROJECT_BOARD_COLUMN_NOT_STARTED)
        in_progress_title = lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_IN_PROGRESS)
        done_title = lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_DONE)

        if not property_numbers:
            return {
                "columns": [
                    cls._build_column_data(
                        title=todo_title,
                        color=cls.TODO_COLOR,
                        groups=[],
                        empty_text=lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_TODO),
                    ),
                    cls._build_column_data(
                        title=in_progress_title,
                        color=cls.IN_PROGRESS_COLOR,
                        groups=[],
                        empty_text=lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_IN_PROGRESS),
                    ),
                    cls._build_column_data(
                        title=done_title,
                        color=cls.DONE_COLOR,
                        groups=[],
                        empty_text=lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_DONE),
                    ),
                ],
            }

        module_items, failed_modules = cls._load_connected_module_items(property_numbers, exclude_project_id=project_id)
        bucketed = cls._bucket_module_items(module_items)
        notice = ""
        if failed_modules:
            # An empty column must not claim "nothing linked" when a module behind it did not load.
            notice = lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_FAILED_MODULES).format(
                modules=", ".join(lang.translate_module_name(module_key) for module_key in failed_modules)
            )
            incomplete_text = lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_INCOMPLETE)
            empty_todo = empty_in_progress = empty_done = incomplete_text
        else:
            empty_todo = lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_TODO)
            empty_in_progress = lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_IN_PROGRESS)
            empty_done = lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_DONE)
        return {
            "notice": notice,
            "columns": [
                cls._build_todo_column_data(
                    bucketed[cls.TODO],
                    lang_manager=lang,
                    empty_text=empty_todo,
                ),
                cls._build_bucket_column_data(
                    in_progress_title,
                    bucketed[cls.IN_PROGRESS],
                    lang_manager=lang,
                    empty_text=empty_in_progress,
                    color=cls.IN_PROGRESS_COLOR,
                ),
                cls._build_bucket_column_data(
                    done_title,
                    bucketed[cls.DONE],
                    lang_manager=lang,
                    empty_text=empty_done,
                    color=cls.DONE_COLOR,
                ),
            ],
        }

    @classmethod
    def _project_property_numbers(cls, item_data: dict) -> list[str]:
        numbers: list[str] = []
        for edge in DataDisplayExtractors._edges_from(item_data, "properties"):
            node = DataDisplayExtractors._as_dict(edge).get("node") or {}
            number = str(node.get("cadastralUnitNumber") or "").strip()
            if number and number not in numbers:
                numbers.append(number)
        return numbers

    @classmethod
    def _load_connected_module_items(
        cls,
        property_numbers: Iterable[str],
        *,
        exclude_project_id: str,
    ) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
        """Return the linked items per module and the tracked modules that failed to load for some property.

        Raises the first error when no tracked module loaded for any property, so the board shows a load
        failure instead of an empty board.
        """
        lookup = PropertyLookupService()
        queries = PropertiesConnectedElementsQueries()
        tracked_modules = set(cls._tracked_modules())
        property_ids = [lookup.property_id_by_cadastral(number) for number in property_numbers]
        property_ids = [property_id for property_id in property_ids if property_id]
        if not property_ids:
            return {}, []

        aggregated: dict[str, dict[str, dict[str, Any]]] = {}
        failed_modules: set[str] = set()
        first_error: Optional[Exception] = None
        loaded_any = False
        with ThreadPoolExecutor(max_workers=min(4, len(property_ids))) as executor:
            futures = [executor.submit(queries.fetch_all_module_data, property_id) for property_id in property_ids]

        for property_id, future in zip(property_ids, futures):
            try:
                module_data = future.result()
            except Exception as exc:
                # Nothing is known of this property, so every tracked module counts as not loaded.
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROJECT.value,
                    event="project_board_connected_items_failed",
                    extra={"property_id": property_id},
                )
                failed_modules.update(tracked_modules)
                first_error = first_error or exc
                continue
            property_failed = [module_key for module_key in module_data.errors if module_key in tracked_modules]
            failed_modules.update(property_failed)
            if property_failed and first_error is None:
                first_error = module_data.errors[property_failed[0]]
            if len(property_failed) < len(tracked_modules):
                loaded_any = True
            for module_key, nodes in module_data.nodes_by_module.items():
                if module_key not in tracked_modules:
                    continue
                bucket = aggregated.setdefault(module_key, {})
                for node in nodes or []:
                    normalized = cls._normalize_node_summary(node)
                    if not normalized:
                        continue
                    if module_key == Module.PROJECT.value and normalized.get("id") == exclude_project_id:
                        continue
                    item_id = str(normalized.get("id") or "").strip()
                    dedupe_key = item_id or f"{normalized.get('number') or ''}|{normalized.get('title') or ''}"
                    if dedupe_key:
                        bucket[dedupe_key] = normalized

        if not loaded_any and first_error is not None:
            raise first_error

        items_by_module = {
            module_key: sorted(items.values(), key=lambda entry: str(entry.get("number") or entry.get("title") or "").lower())
            for module_key, items in aggregated.items()
            if items
        }
        return items_by_module, cls._ordered_module_keys(failed_modules)

    @staticmethod
    def _tracked_modules() -> list[str]:
        return ProjectBoardOverviewService._ordered_module_keys(
            list(PropertiesConnectedElementsQueries.module_to_filename.keys())
        )

    @staticmethod
    def _ordered_module_keys(module_keys: Iterable[str]) -> list[str]:
        normalized_keys: list[str] = []
        for module_key in module_keys or []:
            normalized = str(module_key or "").strip().lower()
            if normalized and normalized not in normalized_keys:
                normalized_keys.append(normalized)

        module_manager = ModuleManager()
        registered_order = {
            module_key: index
            for index, module_key in enumerate(module_manager.modules.keys())
        }
        fallback_index = len(registered_order)

        return sorted(
            normalized_keys,
            key=lambda module_key: (
                registered_order.get(module_key, fallback_index),
                normalized_keys.index(module_key),
            ),
        )

    @classmethod
    def _normalize_node_summary(cls, node: Any) -> Optional[dict[str, Any]]:
        if not isinstance(node, dict):
            return None
        status_payload = node.get("status") if isinstance(node.get("status"), dict) else {}
        type_payload = node.get("type") if isinstance(node.get("type"), dict) else {}
        return {
            "id": str(node.get("id") or "").strip(),
            "number": str(node.get("number") or node.get("code") or "").strip(),
            "title": str(node.get("name") or node.get("title") or "").strip(),
            "module_key": str(node.get("moduleKey") or "").strip(),
            "status_id": str(status_payload.get("id") or "").strip(),
            "status": str(status_payload.get("name") or "").strip(),
            "status_color": str(status_payload.get("color") or "cccccc").strip() or "cccccc",
            "status_type": str(status_payload.get("type") or "").strip().upper(),
            "type": str(type_payload.get("name") or node.get("typeName") or "").strip(),
        }

    @classmethod
    def _bucket_module_items(cls, module_items: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
        bucketed = {
            cls.TODO: {},
            cls.DONE: {},
            cls.IN_PROGRESS: {},
        }
        for module_key, items in module_items.items():
            for item in items:
                bucket = cls.TODO if ProjectBoardStatusRules.is_not_started_item(module_key, item) else cls._classify_status(item.get("status_type"))
                bucketed.setdefault(bucket, {}).setdefault(module_key, []).append(item)
        return bucketed

    @classmethod
    def _classify_status(cls, status_name: Any) -> str:
        normalized = str(status_name or "").strip().upper()
        if normalized == "CLOSED":
            return cls.DONE
        return cls.IN_PROGRESS

    @classmethod
    def _build_bucket_column_data(
        cls,
        title: str,
        grouped_items: dict[str, list[dict[str, Any]]],
        *,
        lang_manager: LanguageManager,
        empty_text: str,
        color: str,
    ) -> dict[str, Any]:
        if not grouped_items:
            return cls._build_column_data(
                title=title,
                color=color,
                groups=[],
                empty_text=empty_text,
            )

        groups = []
        for module_key in cls._ordered_module_keys(grouped_items.keys()):
            items = grouped_items.get(module_key) or []
            if not items:
                continue
            groups.append(
                {
                    "title": f"{lang_manager.translate_module_name(module_key)} ({len(items)})",
                    "module_key": module_key,
                    "items": [cls._build_item_payload(item) for item in items],
                }
            )
        return cls._build_column_data(
            title=title,
            color=color,
            groups=groups,
            empty_text=empty_text,
        )

    @classmethod
    def _build_todo_column_data(
        cls,
        grouped_items: dict[str, list[dict[str, Any]]],
        *,
        lang_manager: LanguageManager,
        empty_text: str,
    ) -> dict[str, Any]:
        title = lang_manager.translate(TranslationKeys.PROJECT_BOARD_COLUMN_NOT_STARTED)
        groups: list[dict[str, Any]] = []

        for module_key in cls._ordered_module_keys(grouped_items.keys()):
            items = grouped_items.get(module_key) or []
            if not items:
                continue
            groups.append(
                {
                    "title": f"{lang_manager.translate_module_name(module_key)} ({len(items)})",
                    "module_key": module_key,
                    "items": [cls._build_item_payload(item) for item in items],
                }
            )

        return cls._build_column_data(
            title=title,
            color=cls.TODO_COLOR,
            groups=groups,
            empty_text=empty_text,
        )

    @staticmethod
    def _build_column_data(*, title: str, color: str, groups: list[dict[str, Any]], empty_text: str) -> dict[str, Any]:
        return {
            "title": title,
            "color": color,
            "groups": groups,
            "empty_text": empty_text,
        }

    @classmethod
    def _build_item_payload(cls, item: dict[str, Any]) -> dict[str, str]:
        number = str(item.get("number") or "").strip()
        title = str(item.get("title") or "").strip()
        type_name = str(item.get("type") or "").strip()
        status = str(item.get("status") or "").strip()
        status_color = str(item.get("status_color") or "").strip()

        primary = title or number or type_name or str(item.get("id") or "-").strip() or "-"
        secondary_parts = [value for value in (number, type_name) if value and value != primary]
        secondary = "  •  ".join(secondary_parts)

        if not secondary and title and number and title != primary:
            secondary = number

        return {
            "primary": primary,
            "secondary": secondary,
            "status": status,
            "status_color": status_color,
        }