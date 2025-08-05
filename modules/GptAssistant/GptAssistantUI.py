from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .logic.Gpt4oClient import Gpt4oClient

class GptAssistantUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None, api_key=None):
        super().__init__()
        from ...module_manager import GPT_ASSISTANT_MODULE
        self.name = GPT_ASSISTANT_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.api_key = api_key
        self.client = None
        self.api_key_error = False
        try:
            if api_key:
                print(f"[GPT DEBUG] Using provided api_key: {api_key[:6]}... (length: {len(api_key)})")
                self.client = Gpt4oClient(api_key=api_key)
            else:
                import os
                env_key = os.environ.get("OPENAI_API_KEY")
                print(f"[GPT DEBUG] os.environ.get('OPENAI_API_KEY') before dotenv/manual: {env_key}")
                if not env_key:
                    # Always use the same path for dotenv and manual fallback
                    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
                    # Try dotenv first
                    try:
                        from dotenv import load_dotenv
                        print(f"[GPT DEBUG] Attempting to load dotenv from: {env_path}")
                        load_dotenv(env_path)
                        env_key = os.environ.get("OPENAI_API_KEY")
                        print(f"[GPT DEBUG] os.environ.get('OPENAI_API_KEY') after dotenv: {env_key}")
                    except Exception as e:
                        print(f"[GPT DEBUG] Exception loading dotenv: {e}")
                    # Manual fallback if still not found
                    if not env_key:
                        print(f"[GPT DEBUG] Manual fallback: reading .env from {env_path}")
                        if os.path.exists(env_path):
                            with open(env_path, encoding="utf-8") as f:
                                for line in f:
                                    if line.strip().startswith("OPENAI_API_KEY="):
                                        env_key = line.strip().split("=", 1)[1]
                                        print(f"[GPT DEBUG] Found API key in .env: {env_key[:6]}... (length: {len(env_key)})")
                                        break
                if env_key:
                    print(f"[GPT DEBUG] Using env_key: {env_key[:6]}... (length: {len(env_key)})")
                    self.client = Gpt4oClient(api_key=env_key)
                else:
                    print("[GPT DEBUG] API key not found after all attempts.")
                    self.api_key_error = True
        except Exception as e:
            print(f"[GPT DEBUG] Exception in GptAssistantUI init: {e}")
            self.api_key_error = True
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to GptAssistantUI for theme application.")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.inputEdit = QTextEdit()
        self.inputEdit.setPlaceholderText(self.lang_manager.translate("gpt_input_placeholder"))
        self.askButton = QPushButton(self.lang_manager.translate("gpt_ask_button"))
        self.askButton.clicked.connect(self.on_ask)
        self.responseLabel = QLabel()
        self.responseLabel.setWordWrap(True)
        layout.addWidget(self.inputEdit)
        layout.addWidget(self.askButton)
        layout.addWidget(self.responseLabel)
        self.setLayout(layout)

    def on_ask(self):
        user_message = self.inputEdit.toPlainText()
        if not user_message:
            return
        if self.api_key_error or not self.client:
            self.responseLabel.setText(self.lang_manager.translate("gpt_api_key_error"))
            return
        response = self.client.ask(user_message)
        self.responseLabel.setText(response)

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.inputEdit.clear()
        self.responseLabel.clear()
    def run(self):
        pass
    def get_widget(self):
        return self
