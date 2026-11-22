"""Options of the works create form: types, responsibles, statuses and priorities.

They are preloaded on a worker when capture starts; whatever is still missing when the
form opens is fetched on the GUI thread and named in load_failures.
"""
from __future__ import annotations

from typing import Optional

from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.module_names import Module, ModuleSupports
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from .works_create_dialog import (
    LOAD_FAILED_PRIORITIES,
    LOAD_FAILED_RESPONSIBLES,
    LOAD_FAILED_STATUSES,
    LOAD_FAILED_TYPES,
)
from .works_layer_service import WorksLayerService


class WorksCreateOptionsMixin:
    """Mixed into WorksCreateController, whose __init__ creates the _cached_* state and _load_failures."""

    def preload_dialog_data(self, *, force: bool = False) -> None:
        if self._preload_thread is not None and not force:
            return

        self._preload_request_id += 1
        request_id = self._preload_request_id

        worker = FunctionWorker(self._fetch_preload_payload)
        worker.finished.connect(
            lambda payload, req=request_id: self._handle_preload_success(payload, req)
        )
        worker.error.connect(
            lambda message, req=request_id: self._handle_preload_error(message, req)
        )
        self._preload_worker = worker
        self._preload_thread = start_worker(worker, on_thread_finished=self._cleanup_preload_worker)

    @staticmethod
    def _log_options_load_failed(exc: Exception, event: str) -> None:
        PythonFailLogger.log_exception(exc, module=Module.WORKS.value, event=event)

    def _fetch_preload_payload(self) -> dict[str, object]:
        try:
            raw_types = FilterHelper.get_filter_edges_by_key_and_module(
                ModuleSupports.TYPES.value,
                Module.WORKS.value,
            )
        except Exception as exc:
            # Fallbacks below are kept: the dialog then opens with an empty list instead of failing the preload.
            self._log_options_load_failed(exc, "works_create_type_options_load_failed")
            raw_types = []

        try:
            assignable_users = APIModuleActions.get_assignable_users()
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_assignable_users_load_failed")
            assignable_users = []

        try:
            default_responsible_id = APIModuleActions.get_current_user_id()
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_default_responsible_load_failed")
            default_responsible_id = ""

        try:
            # raise_on_error: a failed read must not look like a module without statuses.
            status_options = self._normalize_status_options(
                APIModuleActions.get_module_status_options(Module.WORKS.value, raise_on_error=True)
            )
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_status_options_load_failed")
            status_options = []

        default_status_id = self._default_status_id_from_options(status_options)
        default_status_color = self._status_color_from_options(default_status_id, status_options)

        # Fetched here: a slow GUI-thread request opens a modal wait that swallows map clicks.
        try:
            priority_options = APIModuleActions.get_task_priority_options(
                lang_manager=self._lang,
                include_empty=True,
            )
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_priority_options_load_failed")
            priority_options = []

        return {
            "type_options": self._normalize_type_options(raw_types),
            "assignable_users": list(assignable_users or []),
            "default_responsible_id": str(default_responsible_id or "").strip(),
            "status_options": status_options,
            "default_status_id": str(default_status_id or "").strip(),
            "default_status_color": str(default_status_color or "").strip(),
            "priority_options": priority_options,
        }

    def _handle_preload_success(self, payload: object, request_id: int) -> None:
        if request_id != self._preload_request_id or not isinstance(payload, dict):
            return

        self._cached_type_options = self._normalize_type_options(payload.get("type_options") or [])
        self._cached_assignable_users = self._normalize_assignable_users(payload.get("assignable_users") or [])
        self._cached_default_responsible_id = str(payload.get("default_responsible_id") or "").strip()
        self._cached_status_options = self._normalize_status_options(payload.get("status_options") or [])
        self._cached_default_status_id = (
            str(payload.get("default_status_id") or "").strip()
            or self._default_status_id_from_options(self._cached_status_options)
        )
        self._cached_default_status_color = (
            str(payload.get("default_status_color") or "").strip()
            or self._status_color_from_options(self._cached_default_status_id, self._cached_status_options)
        )
        self._cached_priority_options = list(payload.get("priority_options") or [])

    def _handle_preload_error(self, message: str, request_id: int) -> None:
        if request_id != self._preload_request_id:
            return
        PythonFailLogger.log_exception(
            RuntimeError(message or "Works create dialog preload failed"),
            module=Module.WORKS.value,
            event="works_create_dialog_preload_failed",
        )

    def _cleanup_preload_worker(self) -> None:
        self._preload_worker = None
        self._preload_thread = None

    def _resolve_dialog_options(self) -> dict[str, object]:
        """Options for WorksCreateDialog, with the lists that failed to load named in load_failures."""
        self._load_failures = set()
        assignable_users = self._resolve_assignable_users()
        priority_options = self._resolve_priority_options()
        default_responsible_id = self._resolve_default_responsible_id()
        status_options = self._resolve_status_options()
        default_status_id = self._resolve_default_status_id(status_options)
        type_options = self._resolve_type_options()
        return {
            "type_options": type_options,
            "assignable_users": assignable_users,
            "status_options": status_options,
            "priority_options": priority_options,
            "default_responsible_id": default_responsible_id,
            "default_status_id": default_status_id,
            "load_failures": sorted(self._load_failures),
        }

    def _resolve_assignable_users(self) -> list[dict[str, str]]:
        if self._cached_assignable_users:
            return list(self._cached_assignable_users)
        try:
            users = self._normalize_assignable_users(APIModuleActions.get_assignable_users())
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_assignable_users_load_failed")
            users = []
        if not users:
            # get_assignable_users logs a failed request and returns what it has; a successful answer
            # always holds the logged-in user, so an empty list means the load failed.
            self._load_failures.add(LOAD_FAILED_RESPONSIBLES)
        return users

    def _resolve_priority_options(self) -> list[dict[str, str]]:
        if self._cached_priority_options:
            return list(self._cached_priority_options)
        try:
            return APIModuleActions.get_task_priority_options(lang_manager=self._lang, include_empty=True)
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_priority_options_load_failed")
            self._load_failures.add(LOAD_FAILED_PRIORITIES)
            return []

    def _resolve_default_responsible_id(self) -> str:
        if self._cached_default_responsible_id:
            return self._cached_default_responsible_id
        try:
            return APIModuleActions.get_current_user_id()
        except Exception as exc:
            # Only the preselected responsible is lost; the list itself is reported by _resolve_assignable_users.
            self._log_options_load_failed(exc, "works_create_default_responsible_load_failed")
            return ""

    def _resolve_status_options(self) -> list[dict[str, object]]:
        if self._cached_status_options:
            return list(self._cached_status_options)
        try:
            self._cached_status_options = self._normalize_status_options(
                APIModuleActions.get_module_status_options(Module.WORKS.value, raise_on_error=True)
            )
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_status_options_load_failed")
            self._load_failures.add(LOAD_FAILED_STATUSES)
            self._cached_status_options = []
        return list(self._cached_status_options)

    def _resolve_default_status_id(self, status_options: Optional[list[dict[str, object]]] = None) -> str:
        if self._cached_default_status_id:
            return self._cached_default_status_id

        options = status_options if status_options is not None else self._resolve_status_options()
        self._cached_default_status_id = self._default_status_id_from_options(options)
        return self._cached_default_status_id

    def _resolve_default_status_color(self) -> str:
        if self._cached_default_status_color:
            return WorksLayerService.normalize_backend_color(self._cached_default_status_color)
        options = self._resolve_status_options()
        default_status_id = self._resolve_default_status_id(options)
        self._cached_default_status_color = self._status_color_from_options(default_status_id, options)
        return WorksLayerService.normalize_backend_color(self._cached_default_status_color)

    def _resolve_type_options(self) -> list[dict[str, str]]:
        if self._cached_type_options:
            return list(self._cached_type_options)
        try:
            raw_types = FilterHelper.get_filter_edges_by_key_and_module(
                ModuleSupports.TYPES.value,
                Module.WORKS.value,
            )
        except Exception as exc:
            self._log_options_load_failed(exc, "works_create_type_options_load_failed")
            self._load_failures.add(LOAD_FAILED_TYPES)
            raw_types = []
        return self._normalize_type_options(raw_types)

    @staticmethod
    def _normalize_assignable_users(users: object) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for user in users or []:
            if not isinstance(user, dict):
                continue
            user_id = str(user.get("id") or "").strip()
            display_name = str(user.get("displayName") or user.get("name") or "").strip()
            if not user_id or not display_name:
                continue
            normalized.append({"id": user_id, "displayName": display_name})
        return normalized

    @staticmethod
    def _normalize_type_options(entries: object) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for entry in entries or []:
            if isinstance(entry, dict):
                type_id = str(entry.get("id") or "").strip()
                label = str(entry.get("label") or "").strip()
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                label = str(entry[0] or "").strip()
                type_id = str(entry[1] or "").strip()
            else:
                continue
            if not type_id or not label:
                continue
            normalized.append({"id": type_id, "label": label})
        return normalized

    @staticmethod
    def _normalize_status_options(options: object) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for option in options or []:
            if not isinstance(option, dict):
                continue

            status_id = str(option.get("id") or "").strip()
            label = str(option.get("name") or option.get("label") or "").strip()
            if not status_id or not label:
                continue

            normalized.append(
                {
                    "id": status_id,
                    "name": label,
                    "label": label,
                    "color": WorksLayerService.normalize_backend_color(option.get("color")),
                    "type": str(option.get("type") or "").strip().upper(),
                    "description": str(option.get("description") or "").strip(),
                    "isDefault": bool(option.get("isDefault")),
                    "sortOrder": option.get("sortOrder"),
                }
            )
        return normalized

    @staticmethod
    def _default_status_id_from_options(options: object) -> str:
        first_status_id = ""
        for option in options or []:
            if not isinstance(option, dict):
                continue

            status_id = str(option.get("id") or "").strip()
            if status_id and not first_status_id:
                first_status_id = status_id
            if status_id and option.get("isDefault"):
                return status_id
        return first_status_id

    @staticmethod
    def _status_color_from_options(status_id: object, options: object) -> str:
        status_id_text = str(status_id or "").strip()
        first_color = ""
        for option in options or []:
            if not isinstance(option, dict):
                continue

            color = str(option.get("color") or "").strip()
            if color and not first_color:
                first_color = color
            if status_id_text and str(option.get("id") or "").strip() == status_id_text and color:
                return WorksLayerService.normalize_backend_color(color)
        return WorksLayerService.normalize_backend_color(first_color)
