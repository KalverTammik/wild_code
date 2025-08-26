from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class FeedCounterWidget(QWidget):
    """
    Displays a counter: Loaded <loaded> of <total>, with independent styling for numbers and text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = 0
        self._total = 0
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.set_loaded_total(0, 0)

    def set_loaded_total(self, loaded, total):
        self._loaded = loaded
        self._total = total
        # Use HTML for independent styling
        if total is None or total == "" or total == -1:
            # Unknown total – show only loaded portion
            self._label.setText(
                f'<span>Loaded </span>'
                f'<span style="color:#0078d7;font-weight:bold;">{loaded}</span>'
            )
        else:
            self._label.setText(
                f'<span>Loaded </span>'
                f'<span style="color:#0078d7;font-weight:bold;">{loaded}</span>'
                f'<span> of </span>'
                f'<span style="color:#d70078;font-weight:bold;">{total}</span>'
            )

    def loaded(self):
        return self._loaded

    def total(self):
        return self._total
