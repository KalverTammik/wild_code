from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from ..widgets.theme_manager import ThemeManager  # Use ThemeManager for styling
from ..constants.file_paths import FilePaths  # Use FilePaths for theme paths

class ProjectCard(QWidget):
    def __init__(self, title, description, price, brand, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Apply theme dynamically
        theme_path = FilePaths.get_file_path(FilePaths.LIGHT_THEME)  # Use FilePaths for the theme path
        ThemeManager.apply_theme(self, theme_path)

        # Title
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setWordWrap(True)
        self.layout().addWidget(title_label)

        # Description
        desc_label = QLabel(description[:100] + "...")
        desc_label.setWordWrap(True)
        self.layout().addWidget(desc_label)

        # Price and Brand
        meta_label = QLabel(f"Budget: ${price} | Client: {brand}")
        self.layout().addWidget(meta_label)

        # Buttons
        button_layout = QHBoxLayout()
        details_btn = QPushButton("Details")
        complete_btn = QPushButton("Mark Complete")
        edit_btn = QPushButton("✎ Edit")
        button_layout.addWidget(details_btn)
        button_layout.addWidget(complete_btn)
        button_layout.addWidget(edit_btn)
        self.layout().addLayout(button_layout)
        self.layout().addLayout(button_layout)



