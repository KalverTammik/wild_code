"""
PyQt5 dialog for interacting with GPT-4o.
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

from ....languages.language_manager import LanguageManager

class GptAssistantDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(LanguageManager.translate("gptassistant_title"))
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.promptLabel = QLabel(LanguageManager.translate("gptassistant_prompt_label"))
        self.layout.addWidget(self.promptLabel)
        self.inputEdit = QTextEdit()
        self.inputEdit.setPlaceholderText(LanguageManager.translate("gptassistant_placeholder"))
        self.layout.addWidget(self.inputEdit)
        self.askButton = QPushButton(LanguageManager.translate("gptassistant_ask_button"))
        self.layout.addWidget(self.askButton, alignment=Qt.AlignRight)
        self.responseLabel = QLabel(LanguageManager.translate("gptassistant_response_label"))
        self.layout.addWidget(self.responseLabel)
        self.responseEdit = QTextEdit()
        self.responseEdit.setReadOnly(True)
        self.layout.addWidget(self.responseEdit)
        # TODO: Apply theme via ThemeManager

    def setResponse(self, text: str):
        self.responseEdit.setPlainText(text)
