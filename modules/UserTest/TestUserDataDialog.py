import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader
from ...utils.api_client import APIClient
from ...constants.file_paths import QueryPaths, ConfigPaths
from ...languages.language_manager import LanguageManager
from ...utils.SessionManager import SessionManager
from ...constants.module_names import USER_TEST_MODULE



class TestUserDataDialog(QDialog):
    """
    Test dialog to load and display user data (me) from GraphQL API.
    Follows all copilot-prompt.md standards and module interface.
    """
    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None, parent=None):
        super().__init__(parent)
        self.name = USER_TEST_MODULE
        # Ensure we always use LanguageManager_NEW
        if lang_manager is None:
            self.lang = LanguageManager()
        elif not hasattr(lang_manager, 'sidebar_button'):
            language = getattr(lang_manager, 'language', None)
            if language:
                self.lang = LanguageManager(language=language)
            else:
                self.lang = LanguageManager()
        else:
            self.lang = lang_manager
        self.theme_manager = theme_manager
        self.theme_dir = theme_dir
        self.qss_files = qss_files
        self.setWindowTitle(self.lang.translate("test_user_data_title"))
        self.setMinimumSize(400, 300)
        self.query_loader = GraphQLQueryLoader(self.lang)
        self.api_client = APIClient(self.lang, SessionManager(), ConfigPaths.CONFIG)
        self.layout = QVBoxLayout()
        self.result_label = QLabel(self.lang.translate("press_button_to_load"))
        self.layout.addWidget(self.result_label)
        self.load_button = QPushButton(self.lang.translate("load_user_data"))
        self.load_button.clicked.connect(self.load_user_data)
        self.layout.addWidget(self.load_button)
        self.setLayout(self.layout)

    def get_widget(self):
        """Return the main widget for the module (self)."""
        return self

    def load_user_data(self):
        try:
            query = self.query_loader.load_query("USER", "me.graphql")
            data = self.api_client.send_query(query)
            user = data.get("me", {})
            # Display user info
            text = f"<b>ID:</b> {user.get('id', '')}<br>"
            text += f"<b>Name:</b> {user.get('firstName', '')} {user.get('lastName', '')}<br>"
            text += f"<b>Email:</b> {user.get('email', '')}<br>"

            # Group roles by module for better overview
            roles = user.get('roles', [])
            if isinstance(roles, list):
                module_roles = {}
                for role in roles:
                    display_name = role.get('displayName', '')
                    if ':' in display_name:
                        module, role_name = display_name.split(':', 1)
                        module = module.strip()
                        role_name = role_name.strip()
                    else:
                        module = 'Other'
                        role_name = display_name
                    module_roles.setdefault(module, []).append(role_name)

                text += "<b>Roles by Module:</b><br>"
                for module, role_names in module_roles.items():
                    text += f"<u>{module}</u>: {', '.join(role_names)}<br>"
            else:
                text += f"<b>Roles:</b> {roles}<br>"

            # Group abilities (rights) by module for better overview
            import json
            abilities = user.get('abilities', [])
            # If abilities is a string, try to parse it as JSON
            if isinstance(abilities, str):
                try:
                    abilities = json.loads(abilities)
                except Exception:
                    abilities = []
            if isinstance(abilities, list):
                module_abilities = {}
                for ab in abilities:
                    action = ab.get('action', '')
                    subject = ab.get('subject', '')
                    # Try to extract module from subject, fallback to 'Other'
                    if isinstance(subject, list):
                        # If subject is a list, use the first as module, rest as details
                        module = str(subject[0]) if subject else 'Other'
                        subject_str = ', '.join(map(str, subject))
                    else:
                        module = str(subject)
                        subject_str = str(subject)
                    module_abilities.setdefault(module, []).append(action)

                text += "<b>Rights by Module:</b><br>"
                for module, actions in module_abilities.items():
                    text += f"<u>{module}</u>: {', '.join(sorted(set(actions)))}<br>"
            else:
                text += f"<b>Rights:</b> {abilities}<br>"

            self.result_label.setText(text)
        except Exception as e:
            self.result_label.setText(str(e))

    def activate(self):
        """Activate the module."""
        pass

    def deactivate(self):
        """Deactivate the module."""
        pass

