from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from ..ui.ToolbarArea import ToolbarArea


# --- ModuleBaseUI class ---
class ModuleBaseUI(QWidget):
    """
    Universal layout for all modules: Toolbar (top), Display (center), Footer (bottom)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.toolbar_area = ToolbarArea(self)
        self.display_area = QWidget(self)
        self.footer_area = QWidget(self)

        self.layout.addWidget(self.toolbar_area)
        self.layout.addWidget(self.display_area, 1)
        self.layout.addWidget(self.footer_area)

        # Example placeholders for display and footer
        self.display_area.setLayout(QVBoxLayout())
        self.display_area.layout().addWidget(QLabel("Display Area (main content)"))
        self.footer_area.setLayout(QVBoxLayout())
        self.footer_area.layout().addWidget(QLabel("Footer Area (actions/info)"))
