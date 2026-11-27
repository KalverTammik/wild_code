# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QCheckBox


class SelectAllCheckBox(QCheckBox):
    """Tri-state checkbox that never allows user-clicked PartiallyChecked state."""

    def nextCheckState(self) -> None:  # type: ignore[override]
        current = self.checkState()
        if current == Qt.Checked:
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(Qt.Checked)
