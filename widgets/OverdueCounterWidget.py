from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class OverdueCounterWidget(QWidget):
    """
    Displays the overdue projects count in the footer's right corner.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.set_overdue_count(0)

    def set_overdue_count(self, count):
        self._count = count
        self._label.setText(f'<span style="color:#d70000;font-weight:bold;">Overdue: {count}</span>')

    def count(self):
        return self._count
