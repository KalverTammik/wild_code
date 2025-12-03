from typing import Dict, List, Optional

from .query_cordinator import (
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

    def build_connections_for_cadastral(self, cadastral_number: str) -> Dict[str, object]:
        property_id = self._lookup.property_id_by_cadastral(cadastral_number)
        if not property_id:
            return {"entries": [], "message": "Kinnistut ei leitud"}
        return self._build_entry_payload(cadastral_number, property_id)

    def build_connections_for_property_id(
        self,
        property_id: str,
        *,
        cadastral_number: Optional[str] = None,
    ) -> Dict[str, object]:
        if not property_id:
            return {"entries": [], "message": "Kinnistut ei leitud"}
        resolved = cadastral_number or ""
        return self._build_entry_payload(resolved, property_id)

    def _build_entry_payload(self, cadastral_number: str, property_id: str) -> Dict[str, object]:
        module_data = self._connections.fetch_all_module_data(property_id)
        entry = self._formatter.build_entry(cadastral_number, property_id, module_data)
        return {"entries": [entry]}
