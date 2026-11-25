import copy
import threading
import time
from collections import OrderedDict
from typing import Dict, Optional

from ...utils.SessionManager import SessionManager
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys

from .query_coordinator import (
    PropertiesConnectedElementsQueries,
    PropertyLookupService,
    PropertyConnectionFormatter,
)


class PropertyDataService:
    """Encapsulates property-related data lookups and formatting."""

    def __init__(self):
        self._lookup = PropertyLookupService()
        self._connections = PropertiesConnectedElementsQueries()
        self._formatter = PropertyConnectionFormatter()
        self._cache_ttl_seconds = 45.0
        self._cache_max_entries = 64
        self._cache_lock = threading.RLock()
        self._connections_cache: OrderedDict = OrderedDict()

    def build_connections_for_cadastral(self, cadastral_number: str) -> Dict[str, object]:
        normalized = (cadastral_number or "").strip()
        cache_key = ("cadastral", normalized, self._session_signature())
        cached_payload = self._read_cache(cache_key)
        if cached_payload is not None:
            return cached_payload

        property_id = self._lookup.property_id_by_cadastral(normalized)
        if not property_id:
            payload = {"entries": [], "message": LanguageManager().translate(TranslationKeys.PROPERTY_NOT_FOUND)}
            self._write_cache(cache_key, payload)
            return payload

        module_data = self._connections.fetch_all_module_data(property_id)
        if module_data.errors and len(module_data.errors) == len(self._connections.module_to_filename):
            # Nothing loaded: the caller shows a load error instead of "no connections".
            raise next(iter(module_data.errors.values()))
        entry = self._formatter.build_entry(normalized, property_id, module_data.nodes_by_module)
        payload = {"entries": [entry]}
        # A partly failed load is not cached, so the next selection asks the failed modules again.
        if not module_data.errors:
            self._write_cache(cache_key, payload)
        return payload

    def _session_signature(self) -> str:
        return SessionManager.session_signature()

    def _read_cache(self, key: tuple) -> Optional[Dict[str, object]]:
        with self._cache_lock:
            self._prune_expired_locked()
            cached = self._connections_cache.get(key)
            if not cached:
                return None
            timestamp, payload = cached
            if (time.monotonic() - timestamp) > self._cache_ttl_seconds:
                self._connections_cache.pop(key, None)
                return None
            self._connections_cache.move_to_end(key)
            return copy.deepcopy(payload)

    def _write_cache(self, key: tuple, payload: Dict[str, object]) -> None:
        with self._cache_lock:
            self._prune_expired_locked()
            self._connections_cache[key] = (time.monotonic(), copy.deepcopy(payload))
            self._connections_cache.move_to_end(key)
            while len(self._connections_cache) > self._cache_max_entries:
                self._connections_cache.popitem(last=False)

    def _prune_expired_locked(self) -> None:
        now = time.monotonic()
        stale_keys = [
            key
            for key, (timestamp, _) in self._connections_cache.items()
            if (now - timestamp) > self._cache_ttl_seconds
        ]
        for key in stale_keys:
            self._connections_cache.pop(key, None)
