from typing import Any, Dict, List
from PyQt5.QtCore import QObject, pyqtSignal

from ...python.api_client import APIClient
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.workers import FunctionWorker, start_worker


class UnifiedSearchController(QObject):
    """Executes unified search requests and guards against stale responses."""

    searchSucceeded = pyqtSignal(object)
    searchFailed = pyqtSignal(str)
    searchStatus = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._request_id = 0
        self._worker = None
        self._thread = None

    def search(self, term: str) -> None:
        cleaned = term.strip()
        if len(cleaned) < 3:
            self.invalidate()
            return

        self._request_id += 1
        current_id = self._request_id
        self.searchStatus.emit(f'Otsin "{cleaned}"…')

        worker = FunctionWorker(self._run_search, cleaned)
        worker.finished.connect(lambda payload, rid=current_id: self._handle_success(payload, rid))
        worker.error.connect(lambda message, rid=current_id: self._handle_error(message, rid))

        self._worker = worker
        self._thread = start_worker(worker, on_thread_finished=self._clear_worker_refs)

    def invalidate(self) -> None:
        self._request_id += 1

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

    def _handle_success(self, payload: Any, request_id: int) -> None:
        if request_id != self._request_id:
            return
        normalized = self._normalize_payload(payload)
        self.searchSucceeded.emit(normalized)

    def _handle_error(self, message: str, request_id: int) -> None:
        if request_id != self._request_id:
            return
        friendly = message or "Otsing ebaõnnestus"
        self.searchFailed.emit(friendly)

    def _clear_worker_refs(self) -> None:
        self._worker = None
        self._thread = None
