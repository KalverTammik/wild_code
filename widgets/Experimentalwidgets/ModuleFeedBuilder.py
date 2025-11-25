from pathlib import Path
from typing import Optional

from PyQt5 import QtWidgets, uic


class ModuleFeedCard(QtWidgets.QFrame):
    """Lightweight ModuleInfoCard built entirely from a .ui file."""

    _UI_FILE = Path(__file__).with_name("untitled.ui")

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        uic.loadUi(str(self._UI_FILE), self)


class ModuleFeedBuilderExperimental:
    """UI-only copy of ModuleFeedBuilder that keeps the original signature."""

    @staticmethod
    def create_item_card(*_, parent: Optional[QtWidgets.QWidget] = None, **__):
        """Return a ModuleFeedCard instance without binding business logic."""
        return ModuleFeedCard(parent=parent)
