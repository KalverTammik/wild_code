import os
from typing import Any, Optional

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QIcon

from ...constants.base_paths import PLUGIN_ROOT, RESOURCE, ICON_FOLDER


class PropertyTableModel(QAbstractTableModel):
    def __init__(self, headers: list[str], parent=None):
        super().__init__(parent)
        self._headers = headers
        self._rows: list[dict[str, Any]] = []
        self._icons = self._load_icons()

    @staticmethod
    def _load_icons() -> dict[str, QIcon]:
        def _icon(name: str) -> QIcon:
            path = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, name)
            return QIcon(path)

        return {
            "pending": _icon("info (3).png"),
            "ok": _icon("checkmark.png"),
            "error": _icon("warning-sign.png"),
            "warning": _icon("warning-sign.png"),
            "skip": _icon("checkmark.png"),
        }

    def rowCount(self, parent=QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        try:
            return self._headers[section]
        except Exception:
            return None

    def flags(self, index: QModelIndex):  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index: QModelIndex, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._rows):
            return None

        row_data = self._rows[row]

        if role == Qt.UserRole:
            if col == 0:
                return row_data.get("feature")
            return None

        if col <= 3:
            if role == Qt.DisplayRole:
                key = ["cadastral_id", "address", "area", "settlement"][col]
                return str(row_data.get(key, ""))
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignVCenter | Qt.AlignLeft)
            return None

        status_key = {
            4: "backend_attention",
            5: "main_attention",
            6: "archive_backend",
            7: "archive_map",
        }.get(col)

        if not status_key:
            return None

        status = row_data.get(status_key) or {}
        state = status.get("state") or "pending"
        tooltip = status.get("tooltip") or ""

        if role == Qt.DecorationRole:
            return self._icons.get(state) or self._icons["pending"]
        if role == Qt.ToolTipRole:
            return tooltip
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)

        return None

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = [self._normalize_row(r) for r in (rows or [])]
        self.endResetModel()

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(row or {})
        for key in ("backend_attention", "main_attention", "archive_backend", "archive_map"):
            normalized.setdefault(key, {"state": "pending", "tooltip": ""})
        return normalized

    def set_cell_text(self, row: int, col: int, text: str) -> bool:
        if row < 0 or row >= len(self._rows):
            return False
        if col < 0 or col > 3:
            return False

        key = ["cadastral_id", "address", "area", "settlement"][col]
        self._rows[row][key] = str(text or "")
        idx = self.index(row, col)
        self.dataChanged.emit(idx, idx, [Qt.DisplayRole])
        return True

    def set_status(self, row: int, col: int, *, state: str, tooltip: str = "") -> bool:
        if row < 0 or row >= len(self._rows):
            return False

        status_key = {
            4: "backend_attention",
            5: "main_attention",
            6: "archive_backend",
            7: "archive_map",
        }.get(col)
        if not status_key:
            return False

        self._rows[row][status_key] = {"state": state, "tooltip": tooltip}
        idx = self.index(row, col)
        self.dataChanged.emit(idx, idx, [Qt.DecorationRole, Qt.ToolTipRole])
        return True

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:  # type: ignore[override]
        if row < 0 or count <= 0:
            return False
        last = min(row + count - 1, len(self._rows) - 1)
        if last < row:
            return False
        self.beginRemoveRows(parent, row, last)
        del self._rows[row : last + 1]
        self.endRemoveRows()
        return True

    def row_data(self, row: int) -> Optional[dict[str, Any]]:
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]
