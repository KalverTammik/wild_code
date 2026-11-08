from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys

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
        self._update_display()

    def _update_display(self):
        """Update the display with neutral colors."""
        loaded = self._loaded
        total = self._total

        # Use plain text without colors
        if total is None or total == "" or total == -1:
            # Unknown total – show only loaded portion
            self._label.setText(LanguageManager().translate(TranslationKeys.FEED_COUNTER_LOADED).format(loaded=loaded))
        else:
            self._label.setText(
                LanguageManager().translate(TranslationKeys.FEED_COUNTER_LOADED_OF).format(loaded=loaded, total=total)
            )

    def retheme(self):
        """No theme-specific colors needed anymore."""
        pass

    def loaded(self):
        return self._loaded

    def total(self):
        return self._total
