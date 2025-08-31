from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QDialog, QTextEdit, QScrollArea
from PyQt5.QtGui import QFont, QIcon, QPixmap

# Import ModuleConfig - handle both relative and absolute imports
try:
    from .ModuleConfig import ModuleConfigFactory
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    module_config_path = os.path.join(current_dir, 'ModuleConfig.py')
    if os.path.exists(module_config_path):
        spec = __import__('importlib.util').util.spec_from_file_location("ModuleConfig", module_config_path)
        module_config = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(module_config)
        ModuleConfigFactory = module_config.ModuleConfigFactory
    else:
        # Create a simple fallback factory
        class ModuleConfigFactory:
            @staticmethod
            def create_config(module_type, item_data=None):
                # Simple fallback configuration
                class Config:
                    def __init__(self):
                        self.title = "Tegevuste ülevaade"
                        self.columns = [
                            {'title': 'Tehtud', 'color': '#4CAF50', 'activities': [('Ülesanne 1', '✓'), ('Ülesanne 2', '✓')]},
                            {'title': 'Töös', 'color': '#FF9800', 'activities': [('Ülesanne 3', '⟳')]},
                            {'title': 'Tegemata', 'color': '#F44336', 'activities': [('Ülesanne 4', '○')]}
                        ]
                        self.detailed_content = "<h3>Ülevaade</h3><p>Detailne informatsioon puudub.</p>"
                return Config()


class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Determine module type from item_data
        module_type = item_data.get('module_type', 'project') if item_data else 'project'
        layout.addWidget(ExtraInfoWidget(item_data, module_type))


class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, module_type="project", parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.module_type = module_type
        self.config = ModuleConfigFactory.create_config(module_type, item_data)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Title with expand button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(self.config.title)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        title_layout.addWidget(title)

        # Add expand button
        expand_btn = QPushButton()
        expand_btn.setFixedSize(20, 20)
        expand_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #4CAF50;
                background: #4CAF50;
                padding: 2px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #45a049;
                border: 1px solid #45a049;
            }
        """)

        # Load icon from resources
        icon_path = "resources/icons/icons8-rocket-48.png"
        if hasattr(self, '_get_resource_path'):
            icon_path = self._get_resource_path(icon_path)
        try:
            expand_btn.setIcon(QIcon(icon_path))
            expand_btn.setIconSize(expand_btn.size() * 0.8)
        except:
            expand_btn.setText("↗")  # Fallback if icon not found

        expand_btn.clicked.connect(self._show_detailed_overview)
        title_layout.addStretch()
        title_layout.addWidget(expand_btn)

        main_layout.addLayout(title_layout)

        # Dynamic column layout based on configuration
        if self.config.columns:
            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(12)

            for column_config in self.config.columns:
                column = self._create_status_column(
                    column_config['title'],
                    column_config['color'],
                    column_config['activities']
                )
                columns_layout.addWidget(column)

            main_layout.addLayout(columns_layout)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Title with expand button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Tegevuste ülevaade")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        title_layout.addWidget(title)

        # Add expand button
        expand_btn = QPushButton()
        expand_btn.setFixedSize(20, 20)
        expand_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border-radius: 3px;
            }
        """)

        # Load icon from resources
        icon_path = "resources/icons/icons8-rocket-48.png"
        if hasattr(self, '_get_resource_path'):
            icon_path = self._get_resource_path(icon_path)
        try:
            expand_btn.setIcon(QIcon(icon_path))
            expand_btn.setIconSize(expand_btn.size() * 0.8)
        except:
            expand_btn.setText("↗")  # Fallback if icon not found

        expand_btn.clicked.connect(self._show_detailed_overview)
        title_layout.addStretch()
        title_layout.addWidget(expand_btn)

        main_layout.addLayout(title_layout)

        # Three column layout
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(12)

        # Column 1: Tehtud (Done) - 4 activities (increased from 3)
        done_column = self._create_status_column("Tehtud", "#4CAF50", [
            ("Planeerimine", "✓"),
            ("Koostamine", "✓"),
            ("Ülevaatamine", "✓"),
            ("Kinnitamine", "✓")
        ])
        columns_layout.addWidget(done_column)

        # Column 2: Töös (In Progress) - 3 activities (increased from 2)
        progress_column = self._create_status_column("Töös", "#FF9800", [
            ("Testimine", "⟳"),
            ("Dokumenteerimine", "⟳"),
            ("Optimeerimine", "⟳")
        ])
        columns_layout.addWidget(progress_column)

        # Column 3: Tegemata (Not Done) - 4 activities (decreased from 5 for better balance)
        todo_column = self._create_status_column("Tegemata", "#F44336", [
            ("Avaldamine", "○"),
            ("Jälgimine", "○"),
            ("Arhiveerimine", "○"),
            ("Raporteerimine", "○")
        ])
        columns_layout.addWidget(todo_column)

        main_layout.addLayout(columns_layout)

    def _create_status_column(self, title, color, activities):
        """Create a status column with title and activity list."""
        column_widget = QWidget()
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(2)  # Reduced spacing between header and list

        # Column title - removed background color, kept text color
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 11px;
            color: {color};
            padding: 2px 4px;
            margin-bottom: 0px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        column_layout.addWidget(title_label)

        # Activity list
        list_widget = QListWidget()
        list_widget.setFixedHeight(120)  # Set fixed height to ensure at least 3 items are visible
        list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #fafafa;
                padding: 2px;
                margin-top: 0px;
            }
            QListWidget::item {
                padding: 3px 6px;
                border-radius: 3px;
                margin: 1px;
                background-color: transparent;
                color: #333;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #d0d0d0;
            }
        """)

        # Add activities
        for activity_name, icon in activities:
            item = QListWidgetItem(f"{icon} {activity_name}")
            item.setFont(QFont("Arial", 10))
            list_widget.addItem(item)

        column_layout.addWidget(list_widget)
        return column_widget

    def _get_resource_path(self, relative_path):
        """Get absolute path to resource file."""
        import os
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        return os.path.join(plugin_dir, relative_path)

    def _show_detailed_overview(self):
        """Show detailed activity overview in a dialog window."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.config.title} - Detailne ülevaade")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel(self.config.title)
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)

        # Scrollable text area with module-specific content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #fafafa;
            }
        """)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)

        # Use module-specific content
        content = self.config.detailed_content or """
        <h3>Üldine Tegevuste Ülevaade</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        """

        text_label = QLabel(content)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            QLabel {
                color: #333;
                line-height: 1.4;
                padding: 10px;
            }
            QLabel h3 {
                color: #2E7D32;
                margin-top: 15px;
                margin-bottom: 8px;
            }
            QLabel h4 {
                color: #1976D2;
                margin-top: 12px;
                margin-bottom: 6px;
            }
            QLabel p {
                margin-bottom: 8px;
            }
            QLabel ul, QLabel ol {
                margin-left: 15px;
                margin-bottom: 8px;
            }
            QLabel li {
                margin-bottom: 3px;
            }
        """)
        text_label.setTextFormat(Qt.RichText)

        text_layout.addWidget(text_label)
        scroll_area.setWidget(text_widget)
        layout.addWidget(scroll_area)

        # Close button
        close_btn = QPushButton("Sulge")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.exec_()
