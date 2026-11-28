"""The tags on a record card, arranged by group as soon as the module's catalog has been read."""
from __future__ import annotations

from typing import Optional, Sequence

from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import QWidget

from ...python.tag_catalog import Tag
from .tag_catalog_store import TagCatalogStore
from .tag_chips import TagChipsView


class RecordTagsView(TagChipsView):
    def __init__(self, module: str, tags: Sequence[Tag], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._module = str(module or "").strip().lower()
        self._tags = tuple(tags)
        self._store = TagCatalogStore.shared()
        # A bound slot of this widget: Qt drops the connection when the card is deleted.
        self._store.changed.connect(self._on_catalog_changed)
        self._render()

    @pyqtSlot(str)
    def _on_catalog_changed(self, module: str) -> None:
        if module == self._module:
            self._render()

    def _render(self) -> None:
        self.show_tags(self._store.get(self._module), [tag.id for tag in self._tags], record_tags=self._tags)
