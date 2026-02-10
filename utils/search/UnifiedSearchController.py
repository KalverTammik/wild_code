from typing import Any, Dict, List
import sys
from PyQt5.QtCore import QObject, pyqtSignal

from ...python.api_client import APIClient
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.workers import FunctionWorker, start_worker
from ...Logs.switch_logger import SwitchLogger
from ...Logs.python_fail_logger import PythonFailLogger


class UnifiedSearchController(QObject):
    """Executes unified search requests and guards against stale responses."""

    searchSucceeded = pyqtSignal(object)
    searchFailed = pyqtSignal(str)
    searchStatus = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker = None
        self._thread = None

    def search(self, term: str) -> None:
        cleaned = term.strip()
        if len(cleaned) < 3:
            self.invalidate()
            return

        token = self._current_token()
        self.searchStatus.emit(f'Otsin "{cleaned}"…')
        try:
            PythonFailLogger.log(
                "search_start",
                module=getattr(self.parent(), "module_key", None),
                message=cleaned,
                extra={"token": token},
            )
        except Exception as exc:
            print(f"[UnifiedSearchController] search_start log failed: {exc}", file=sys.stderr)

        worker = FunctionWorker(self._run_search, cleaned)
        worker.active_token = token
        worker.finished.connect(lambda payload, tok=token: self._handle_success(payload, tok))
        worker.error.connect(lambda message, tok=token: self._handle_error(message, tok))

        self._worker = worker
        self._thread = start_worker(worker, on_thread_finished=self._clear_worker_refs)

    def invalidate(self) -> None:
        return

    def _run_search(self, term: str) -> Dict[str, Any]:
        loader = GraphQLQueryLoader()
        gql = loader.load_query_by_module("user", "search.graphql")
        if not gql:
            raise RuntimeError("Unified search query missing")

        api_client = APIClient()
        variables: Dict[str, Any] = {
            "input": {
                "term": term,
                "types": [
                    "PROPERTIES",
                    "PROJECTS",
                    "TASKS",
                    "SUBMISSIONS",
                    "EASEMENTS",
                    "COORDINATIONS",
                    "SPECIFICATIONS",
                    "ORDINANCES",
                    "CONTRACTS",
                ],
                "limit": 5,
            }
        }
        return api_client.send_query(gql, variables=variables)

    def _normalize_payload(self, payload: dict) -> List[Dict[str, Any]]:
        data_section = payload.get("data", payload)
        search_block = data_section.get("search")
        if isinstance(search_block, dict):
            return [search_block]
        if isinstance(search_block, list):
            return search_block
        return []

    def _handle_success(self, payload: Any, token: int | None) -> None:
        if not self._is_token_active(token):
            SwitchLogger.log(
                "search_ignored_inactive_token",
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "search_token_ok",
            extra={"token": token, "current": self._current_token()},
        )
        normalized = self._normalize_payload(payload)
        try:
            PythonFailLogger.log(
                "search_success",
                module=getattr(self.parent(), "module_key", None),
                extra={"token": token, "results": len(normalized)},
            )
        except Exception as exc:
            print(f"[UnifiedSearchController] search_success log failed: {exc}", file=sys.stderr)
        self.searchSucceeded.emit(normalized)

    def _handle_error(self, message: str, token: int | None) -> None:
        if not self._is_token_active(token):
            SwitchLogger.log(
                "search_ignored_inactive_token",
                extra={"token": token, "current": self._current_token()},
            )
            return
        SwitchLogger.log(
            "search_token_ok",
            extra={"token": token, "current": self._current_token()},
        )
        try:
            PythonFailLogger.log(
                "search_error",
                module=getattr(self.parent(), "module_key", None),
                message=message,
            )
        except Exception as exc:
            print(f"[UnifiedSearchController] search_error log failed: {exc}", file=sys.stderr)
        friendly = message or "Otsing ebaõnnestus"
        self.searchFailed.emit(friendly)

    def _clear_worker_refs(self) -> None:
        self._worker = None
        self._thread = None

    def _current_token(self) -> int | None:
        parent = self.parent()
        if parent is None:
            return None
        if hasattr(parent, "_active_token"):
            return getattr(parent, "_active_token", None)
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if token is None:
            return True
        parent = self.parent()
        if parent is None:
            return True
        if hasattr(parent, "is_token_active"):
            try:
                return bool(parent.is_token_active(token))
            except Exception:
                return False
        if hasattr(parent, "_active_token"):
            return bool(getattr(parent, "_activated", False)) and token == getattr(parent, "_active_token", None)
        return True
