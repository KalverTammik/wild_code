"""
JokeGeneratorUI: UI for Joke Generator module, following plugin design guidelines.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QTextEdit, QGroupBox, QFrame
from PyQt5.QtCore import Qt

from ....widgets.theme_manager import ThemeManager
from ....languages.language_manager import LanguageManager


def get_lang_manager():
    # Always return a LanguageManager instance, not a string
    pref = LanguageManager.load_language_preference() if hasattr(LanguageManager, 'load_language_preference') else None
    if isinstance(pref, str):
        return LanguageManager(pref)
    return LanguageManager()

lang = get_lang_manager()

class JokeGeneratorUI(QWidget):
    def __init__(self, parent=None, theme_dir=None, qss_files=None):
        super().__init__(parent)
        self.setObjectName("JokeGeneratorUI")
        if theme_dir is not None:
            ThemeManager.apply_theme(self, theme_dir, qss_files)
        self._setup_ui()

    def _setup_ui(self):
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(8, 8, 8, 8)
        mainLayout.setSpacing(8)

        # Group: Joke Controls
        controlsGroup = QGroupBox(lang.translate("joke_controls_group"))
        controlsLayout = QHBoxLayout()
        controlsGroup.setLayout(controlsLayout)
        controlsGroup.setObjectName("JokeControlsGroup")

        self.categoryDropdown = QComboBox()
        self.categoryDropdown.setObjectName("JokeCategoryDropdown")
        self.categoryDropdown.addItems([
            lang.translate("joke_category_random"),
            lang.translate("joke_category_programming"),
            lang.translate("joke_category_uncle_eino")
        ])
        controlsLayout.addWidget(QLabel(lang.translate("joke_category_label")))
        controlsLayout.addWidget(self.categoryDropdown)

        self.getJokeButton = QPushButton(lang.translate("joke_get_button"))
        self.getJokeButton.setObjectName("JokeGetButton")
        controlsLayout.addWidget(self.getJokeButton)

        mainLayout.addWidget(controlsGroup)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        mainLayout.addWidget(divider)

        # Joke Display
        self.jokeDisplay = QTextEdit()
        self.jokeDisplay.setReadOnly(True)
        self.jokeDisplay.setObjectName("JokeDisplay")
        mainLayout.addWidget(self.jokeDisplay)

        # Auto-refresh
        self.autoRefreshCheckbox = QCheckBox(lang.translate("joke_auto_refresh"))
        self.autoRefreshCheckbox.setObjectName("JokeAutoRefreshCheckbox")
        mainLayout.addWidget(self.autoRefreshCheckbox)

        self.setLayout(mainLayout)
