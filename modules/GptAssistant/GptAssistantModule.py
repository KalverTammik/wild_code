"""
GptAssistantModule: Main entry point for GPT-4o assistant integration.
"""
from .ui.GptAssistantDialog import GptAssistantDialog
import os
import importlib
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from ...BaseModule import BaseModule
from PyQt5.QtCore import QObject

class GptAssistantModule(BaseModule, QObject):
    def __init__(self, api_key=None, parent=None):
        BaseModule.__init__(self)
        QObject.__init__(self, parent)
        self.name = "GPT_ASSISTANT_MODULE"
        self.dialog = GptAssistantDialog(parent)
        self.client = None
        self.enabled = True

        # Load API key from .env if not provided
        if api_key is None:
            api_key = self._load_api_key_from_env()

        try:
            importlib.import_module("openai")
            from .logic.Gpt4oClient import Gpt4oClient
            self.client = Gpt4oClient(api_key=api_key)
        except ModuleNotFoundError:
            self.enabled = False
            self.show_install_dialog()
        self.dialog.askButton.clicked.connect(self.onAskClicked)

    def _load_api_key_from_env(self):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        api_key = None
        # Try to use python-dotenv if available
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            api_key = os.environ.get("OPENAI_API_KEY")
        except ImportError:
            # Fallback to manual parsing
            if os.path.exists(env_path):
                with open(env_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1]
                            break
        return api_key

    def show_install_dialog(self):
        msg = QMessageBox(self.dialog)
        msg.setWindowTitle("OpenAI Python package missing")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("OpenAI Python package (openai) is not installed in your QGIS environment.\n\nInstall instructions will be shown.\n\nDo you want to see the installation manual?")
        install_btn = msg.addButton("Show Manual", QMessageBox.AcceptRole)
        cancel_btn = msg.addButton("Disable Module", QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton() == install_btn:
            self.show_manual()
        else:
            self.enabled = False

    def show_manual(self):
        # Show the manual in a non-blocking (modeless) dialog
        self.manual_dialog = QDialog(self.dialog)
        self.manual_dialog.setWindowTitle("How to install openai for QGIS")
        layout = QVBoxLayout(self.manual_dialog)
        label = QLabel("Follow these steps to install the OpenAI Python package in your QGIS environment:")
        layout.addWidget(label)
        text = QTextEdit()
        text.setReadOnly(True)
        with open(os.path.join(os.path.dirname(__file__), "README_QGIS_OPENAI.txt"), encoding="utf-8") as f:
            text.setPlainText(f.read())
        layout.addWidget(text)
        ok_btn = QPushButton("OK")
        layout.addWidget(ok_btn)
        ok_btn.clicked.connect(self.on_manual_ok)
        self.manual_dialog.setModal(False)
        self.manual_dialog.show()

    def on_manual_ok(self):
        # Close the manual dialog
        if hasattr(self, 'manual_dialog'):
            self.manual_dialog.close()
            del self.manual_dialog
        # Try to import openai again
        try:
            importlib.import_module("openai")
            from .logic.Gpt4oClient import Gpt4oClient
            self.client = Gpt4oClient()
            self.enabled = True
        except ModuleNotFoundError:
            # Still not installed, show install dialog again
            self.show_install_dialog()

    def activate(self):
        if self.enabled:
            self.dialog.show()

    def deactivate(self):
        if self.enabled:
            self.dialog.hide()

    def run(self):
        if self.enabled:
            self.activate()

    def reset(self):
        if self.enabled:
            self.dialog.inputEdit.clear()
            self.dialog.responseEdit.clear()

    def get_widget(self):
        return self.dialog if self.enabled else None

    def onAskClicked(self):
        if not self.enabled:
            self.dialog.setResponse("See moodul on keelatud, sest OpenAI teek pole paigaldatud.")
            return
        user_text = self.dialog.inputEdit.toPlainText().strip()
        if not user_text:
            self.dialog.setResponse("Palun sisesta küsimus.")
            return
        try:
            response = self.client.ask(user_text)
            self.dialog.setResponse(response)
        except Exception as e:
            self.dialog.setResponse(f"Viga: {e}")
