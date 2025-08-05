"""
PyQt5 dialog for interacting with GPT-4o.
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

class GptAssistantDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GPT-4o abiline")
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.promptLabel = QLabel("Sisesta küsimus GPT-4o-le:")
        self.layout.addWidget(self.promptLabel)
        self.inputEdit = QTextEdit()
        self.inputEdit.setPlaceholderText("Küsimus või juhis...")
        self.layout.addWidget(self.inputEdit)
        self.askButton = QPushButton("Küsi AI-lt")
        self.layout.addWidget(self.askButton, alignment=Qt.AlignRight)
        self.responseLabel = QLabel("Vastus:")
        self.layout.addWidget(self.responseLabel)
        self.responseEdit = QTextEdit()
        self.responseEdit.setReadOnly(True)
        self.layout.addWidget(self.responseEdit)
        # TODO: Apply theme via ThemeManager

    def setResponse(self, text: str):
        self.responseEdit.setPlainText(text)
