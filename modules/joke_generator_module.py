import requests
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QHBoxLayout, QTextEdit
from PyQt5.QtCore import QTimer, Qt
from ..BaseModule import BaseModule
from ..module_manager import JOKE_GENERATOR_MODULE

class JokeGeneratorModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = JOKE_GENERATOR_MODULE
        self.api_url = "https://icanhazdadjoke.com/"
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_joke)

        # Set up the module's UIf
        layout = QVBoxLayout()
        self.categoryDropdown = QComboBox()
        self.categoryDropdown.addItems(["Juhuslik", "Programmeerimine", "Onu Eino"])
        self.getJokeButton = QPushButton("Näita nali")
        self.getJokeButton.clicked.connect(self.fetch_joke)
        self.jokeDisplay = QTextEdit()
        self.jokeDisplay.setReadOnly(True)
        self.autoRefreshCheckbox = QCheckBox("Automaatne värskendamine iga 10 sekundi järel")
        self.autoRefreshCheckbox.stateChanged.connect(self.toggle_auto_refresh)

        headerLayout = QHBoxLayout()
        headerLayout.addWidget(QLabel("Kategooria:"))
        headerLayout.addWidget(self.categoryDropdown)
        headerLayout.addWidget(self.getJokeButton)

        layout.addLayout(headerLayout)
        layout.addWidget(self.jokeDisplay)
        layout.addWidget(self.autoRefreshCheckbox)
        self.widget.setLayout(layout)

    def fetch_joke(self):
        try:
            headers = {"Accept": "application/json"}
            response = requests.get(self.api_url, headers=headers)
            if response.status_code == 200:
                joke = response.json().get("joke", "No joke found.")
                self.jokeDisplay.setText(joke)
            else:
                self.jokeDisplay.setText(f"Error: Unable to fetch joke (Status {response.status_code})")
        except Exception as e:
            self.jokeDisplay.setText(f"Error: {str(e)}")

    def toggle_auto_refresh(self, state):
        if state == Qt.Checked:
            self.timer.start(10000)  # 10 seconds
        else:
            self.timer.stop()

    def activate(self):
        self.jokeDisplay.setText("Joke Generator Activated")

    def deactivate(self):
        self.timer.stop()
        self.jokeDisplay.setText("Joke Generator Deactivated")

    def reset(self):
        self.timer.stop()
        self.jokeDisplay.clear()
        self.autoRefreshCheckbox.setChecked(False)

    def get_widget(self):
        return self.widget
