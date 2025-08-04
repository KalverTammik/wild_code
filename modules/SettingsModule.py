from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from ..BaseModule import BaseModule  # Import the base module class
from ..module_manager import SETTINGS_MODULE, ModuleManager  # Import the unique identifier for the SettingsModule
class SettingsModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = SETTINGS_MODULE
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        module_name = ModuleManager.get_module_name(self.name)
        
        # Heading label
        self.heading = QLabel(module_name)
        self.heading.setObjectName("settingsHeading")
        self.layout.addWidget(self.heading)

        # Text edit for notes/configuration
        self.textEdit = QTextEdit()
        self.textEdit.setObjectName("settingsTextEdit")
        self.layout.addWidget(self.textEdit)

        # Apply dark theme styling dynamically
        self.apply_theme()

    def apply_theme(self):
        # Placeholder for theme application logic
        pass

    def activateSettingsModule(self):
        """Activate the SettingsModule."""
        # Call show() on the widget of the SettingsModule instance
        self.get_widget().show()

    def deactivate(self):
        # Logic to deactivate the module
        pass

    def run(self):
        # Placeholder for run logic
        pass

    def reset(self):
        # Logic to reset the module
        self.textEdit.clear()

    def get_widget(self):
        return self.widget
