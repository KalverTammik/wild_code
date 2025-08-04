from PyQt5.QtWidgets import QWidget

class BaseModule:
    def __init__(self):
        self.widget = QWidget()

    def activate(self):
        """Activate the module."""
        pass

    def deactivate(self):
        """Deactivate the module."""
        pass

    def run(self):
        """Run the module's main logic."""
        pass

    def reset(self):
        """Reset the module's state."""
        pass

    def get_widget(self):
        """Return the module's main QWidget."""
        return self.widget
