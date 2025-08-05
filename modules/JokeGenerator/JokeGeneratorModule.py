"""
JokeGeneratorModule: Main entry point for Joke Generator, following plugin modular guidelines.
"""
from .ui.JokeGeneratorUI import JokeGeneratorUI
from .logic.JokeGeneratorLogic import JokeGeneratorLogic
from ...BaseModule import BaseModule
from PyQt5.QtCore import QTimer, Qt
from ...constants.file_paths import StylePaths

class JokeGeneratorModule(BaseModule):
    def __init__(self, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import JOKE_GENERATOR_MODULE
        self.name = JOKE_GENERATOR_MODULE
        self.logic = JokeGeneratorLogic()
        # Use theme_dir from dialog.py if provided, else fallback to default
        if theme_dir is None:
            theme_dir = StylePaths.DARK
        self.ui = JokeGeneratorUI(theme_dir=theme_dir, qss_files=qss_files)
        self.timer = QTimer()
        self.timer.timeout.connect(self._fetch_and_display_joke)
        self.ui.getJokeButton.clicked.connect(self._fetch_and_display_joke)
        self.ui.autoRefreshCheckbox.stateChanged.connect(self._toggle_auto_refresh)
        self._fetch_and_display_joke()

    def _fetch_and_display_joke(self):
        joke = self.logic.fetch_joke()
        self.ui.jokeDisplay.setText(joke)

    def _toggle_auto_refresh(self, state):
        if state == Qt.Checked:
            self.timer.start(10000)
        else:
            self.timer.stop()

    def activate(self):
        self._fetch_and_display_joke()

    def deactivate(self):
        self.timer.stop()
        self.ui.jokeDisplay.setText("")

    def run(self):
        self._fetch_and_display_joke()

    def reset(self):
        self.timer.stop()
        self.ui.jokeDisplay.clear()
        self.ui.autoRefreshCheckbox.setChecked(False)

    def get_widget(self):
        return self.ui
