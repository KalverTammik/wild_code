"""The home page cards and the requests that fill them, one per module."""
from __future__ import annotations

from functools import partial
from typing import Optional

from qgis.PyQt.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ...python.latest_request import LatestRequest
from ...ui.theme_manager import ThemeManager
from ...utils.api_error_handling import user_message
from .dashboard_cards import PAGE, HomeCard, Snapshot
from .dashboard_counts import SOURCES, ModuleCounts, fetch_counts


class HomeDashboard(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._data = Snapshot()
        self._errors: dict[str, str] = {}
        self._requests: dict[str, LatestRequest] = {}
        for key in SOURCES:
            request = LatestRequest(self)
            request.finished.connect(partial(self._on_counts, key))
            request.error.connect(partial(self._on_failed, key))
            self._requests[key] = request

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.cards: list[HomeCard] = []
        for columns in PAGE:
            row = QHBoxLayout()
            row.setSpacing(12)
            for specs in columns:
                column = QVBoxLayout()
                column.setSpacing(12)
                for spec in specs:
                    card = HomeCard(spec, self._data, self)
                    self.cards.append(card)
                    column.addWidget(card)
                column.addStretch(1)
                row.addLayout(column)
            row.addStretch(1)
            layout.addLayout(row)
        self.retheme()

    def refresh(self) -> None:
        """Read everything again; numbers already on screen stay until the new ones arrive."""
        for key, request in self._requests.items():
            if key in self._data.failed:
                self._data.failed.discard(key)
                self._errors.pop(key, None)
            request.submit(fetch_counts, key)
        self._show()

    def cancel(self) -> None:
        for request in self._requests.values():
            request.invalidate()

    def _on_counts(self, key: str, counts: ModuleCounts) -> None:
        self._data.counts[key] = counts
        self._show()

    def _on_failed(self, key: str, message: str) -> None:
        # A number that could not be read again is not shown as current.
        self._data.counts.pop(key, None)
        self._data.failed.add(key)
        self._errors[key] = user_message(message)
        self._show()

    def _show(self) -> None:
        for card in self.cards:
            messages = [self._errors[key] for key in card.spec.modules if key in self._errors]
            card.setToolTip("\n".join(dict.fromkeys(messages)))
            card.update()

    def retheme(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        for card in self.cards:
            card.dark = dark
            card.update()
