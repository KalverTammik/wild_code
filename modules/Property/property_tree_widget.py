from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QTreeView, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem


class PropertyTreeWidget(QFrame):
    """Displays module-level connections for a selected property."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertyTree")
        self.setFrameStyle(QFrame.StyledPanel)
        self._current_entries: List[Dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(6)

        title = QLabel("Kinnistuga seotud andmed")
        title.setObjectName("TreeTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)

        self.tree_view = QTreeView(self)
        self.tree_view.setObjectName("PropertyTreeView")
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Andmetüüp", "Väärtus", "Kuupäev", "Staatus"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setColumnWidth(0, 220)
        self.tree_view.setColumnWidth(1, 200)
        self.tree_view.setColumnWidth(2, 140)
        self.tree_view.setColumnWidth(3, 120)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setRootIsDecorated(True)
        layout.addWidget(self.tree_view)

        controls = QHBoxLayout()
        self.expand_btn = QPushButton("Laienda kõik", self)
        self.expand_btn.clicked.connect(self.tree_view.expandAll)
        controls.addWidget(self.expand_btn)

        self.collapse_btn = QPushButton("Ahenda kõik", self)
        self.collapse_btn.clicked.connect(self.tree_view.collapseAll)
        controls.addWidget(self.collapse_btn)

        self.refresh_btn = QPushButton("Värskenda puu", self)
        self.refresh_btn.clicked.connect(self.refresh_tree_data)
        controls.addWidget(self.refresh_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.show_message("Vali kinnistu kaardilt")

    def show_message(self, message: str):
        self._current_entries = []
        self._set_single_row(message)

    def show_loading(self, message: str = "Laen seotud andmeid..."):
        self._set_single_row(message)

    def load_connections(self, entries: List[Dict[str, Any]]):
        self._current_entries = entries or []
        self._rebuild_tree_from_entries()
        self.tree_view.expandAll()

    def refresh_tree_data(self):
        if self._current_entries:
            self._rebuild_tree_from_entries()
            self.tree_view.expandAll()
        else:
            self.show_message("Andmed puuduvad")

    # --- Internal helpers -------------------------------------------------

    def _set_single_row(self, message: str):
        self.tree_model.removeRows(0, self.tree_model.rowCount())
        row = self._create_row([message, "", "", ""], bold=True)
        for item in row:
            item.setFlags(Qt.ItemIsEnabled)
        self.tree_model.appendRow(row)

    def _rebuild_tree_from_entries(self):
        self.tree_model.removeRows(0, self.tree_model.rowCount())
        if not self._current_entries:
            self.show_message("Andmeid ei leitud")
            return

        for entry in self._current_entries:
            cadastral = entry.get("cadastralNumber") or "Kinnistu"
            property_id = entry.get("propertyId") or "-"
            top_row = self._create_row([
                f"Katastritunnus {cadastral}",
                property_id,
                "",
                "",
            ], bold=True)
            self.tree_model.appendRow(top_row)
            top_item = top_row[0]

            if entry.get("error"):
                self._append_info_row(top_item, entry["error"], italic=True)
                continue

            modules = entry.get("moduleConnections") or {}
            if not modules:
                self._append_info_row(top_item, "Seoseid ei leitud", italic=True)
                continue

            for module_key, module_info in modules.items():
                self._append_module_group(top_item, module_key, module_info)

    def _append_module_group(self, parent: QStandardItem, module_key: str, module_info: Dict[str, Any]):
        module_title = module_key.capitalize()
        count = module_info.get("count", 0)
        module_row = self._create_row([
            module_title,
            f"{count} kirjet",
            "",
            "",
        ], bold=True)
        parent.appendRow(module_row)
        module_item = module_row[0]

        items = module_info.get("items") or []
        if not items:
            self._append_info_row(module_item, "Kirjeid ei ole", italic=True)
            return

        for node in items:
            row_items = self._create_row(self._build_item_columns(node))
            row_items[0].setData(node.get("raw", node), Qt.UserRole)
            module_item.appendRow(row_items)

    def _append_info_row(self, parent: QStandardItem, message: str, italic: bool = False):
        row = self._create_row([message, "", "", ""], italic=italic)
        parent.appendRow(row)

    def _build_item_columns(self, node: Dict[str, Any]) -> List[str]:
        number = node.get("number") or node.get("id") or "-"
        title = node.get("title") or ""
        updated = node.get("updatedAt") or node.get("raw", {}).get("updatedAt") or ""
        status = node.get("status") or ""
        return [number, title, updated, status]

    def _create_row(self, columns: List[str], bold: bool = False, italic: bool = False) -> List[QStandardItem]:
        row: List[QStandardItem] = []
        for text in columns:
            item = QStandardItem(text or "")
            font = QFont()
            if bold:
                font.setBold(True)
            if italic:
                font.setItalic(True)
            item.setFont(font)
            row.append(item)
        return row
