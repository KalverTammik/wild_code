"""The tag catalogs read in this session, so record cards can group their tags without a request."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QObject, pyqtSignal

from ...python.tag_catalog import TagCatalog
from ...utils.SessionManager import SessionManager


class TagCatalogStore(QObject):
    """Whoever reads a catalog puts it here; `changed` names the module."""

    changed = pyqtSignal(str)
    _instance: Optional["TagCatalogStore"] = None

    def __init__(self) -> None:
        super().__init__()
        self._catalogs: dict[str, tuple[str, TagCatalog]] = {}

    @classmethod
    def shared(cls) -> "TagCatalogStore":
        if cls._instance is None:
            cls._instance = TagCatalogStore()
        return cls._instance

    def put(self, module: str, catalog: TagCatalog) -> None:
        key = str(module or "").strip().lower()
        entry = (SessionManager.session_signature(), catalog)
        if not key or self._catalogs.get(key) == entry:
            return
        self._catalogs[key] = entry
        self.changed.emit(key)

    def get(self, module: str) -> TagCatalog:
        """The catalog of the module in the current session; empty when none has been read."""
        signature, catalog = self._catalogs.get(str(module or "").strip().lower(), ("", TagCatalog()))
        return catalog if signature == SessionManager.session_signature() else TagCatalog()
