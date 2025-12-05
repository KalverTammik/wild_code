from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel


class ContactsWidget(QFrame):
    """Inline chip list for coordination contacts."""

    def __init__(self, item_data, total=None, parent=None):
        super().__init__(parent)
        names = [n for n in (self.extract_contacts(item_data) or []) if n]
        print(f"[ContactsWidget] Extracted contact names: {names}")
        if not names:
            self.setVisible(False)
            return

        self.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel("Contacts:")
        label.setStyleSheet("font-weight: 600; font-size: 11px; color: #2b3a5a;")
        layout.addWidget(label, 0, Qt.AlignVCenter)

        max_show = 3
        shown = 0
        for name in names[:max_show]:
            chip = QLabel(name)
            chip.setObjectName("ContactChip")
            chip.setStyleSheet(
                "padding: 2px 8px;"
                "border-radius: 10px;"
                "background-color: #eef2ff;"
                "color: #1f3b73;"
                "font-size: 11px;"
            )
            layout.addWidget(chip, 0, Qt.AlignVCenter)
            shown += 1

        remaining = (total or len(names)) - shown
        if remaining > 0:
            more = QLabel(f"+{remaining}")
            more.setStyleSheet(
                "padding: 2px 6px;"
                "border-radius: 10px;"
                "background-color: #e8edf5;"
                "color: #42516b;"
                "font-size: 10px;"
            )
            layout.addWidget(more, 0, Qt.AlignVCenter)
    @staticmethod
    def extract_contacts (item_data):
        """Extract contact names from item data."""
        contacts_conn = item_data.get('contacts') or {}
        if not contacts_conn:
            return []
        contact_edges = contacts_conn.get('edges') or []
        contact_names = [
            (edge.get('node') or {}).get('displayName')
            for edge in contact_edges
            if isinstance(edge, dict) and (edge.get('node') or {}).get('displayName')
        ]
        return contact_names