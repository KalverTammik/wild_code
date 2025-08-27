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
        self._update_display()

    def _update_display(self):
        """Update the display with current theme colors."""
        count = self._count

        # Get theme-appropriate colors
        try:
            from ..widgets.theme_manager import ThemeManager
            theme = ThemeManager.load_theme_setting()
        except Exception:
            theme = 'light'

        if theme == 'dark':
            overdue_color = '#ff6b6b'  # lighter red for dark theme
        else:
            overdue_color = '#d70000'  # darker red for light theme

        self._label.setText(f'<span style="color:{overdue_color};font-weight:bold;">Overdue: {count}</span>')

    def retheme(self):
        """Update colors based on current theme."""
        self._update_display()

    def count(self):
        return self._count
