from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QDialog, QTextEdit, QScrollArea
from PyQt5.QtGui import QFont, QIcon, QPixmap


class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ExtraInfoWidget(item_data))


class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ExtraInfoWidget(item_data))


class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self._build_ui()

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
        dialog.setWindowTitle("Tegevuste detailne ülevaade")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Tegevuste detailne ülevaade")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)

        # Scrollable text area with Latin sample text
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

        # Sample Latin text content
        latin_content = """
        <h3>Activitas Recens</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>

        <h4>Status Progressionis</h4>
        <ul>
        <li><b>Tehtud:</b> Planeerimine, Koostamine, Ülevaatamine, Kinnitamine</li>
        <li><b>Töös:</b> Testimine, Dokumenteerimine, Optimeerimine</li>
        <li><b>Tegemata:</b> Avaldamine, Jälgimine, Arhiveerimine, Raporteerimine</li>
        </ul>

        <h4>Detalii Addicionales</h4>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>

        <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.</p>

        <h4>Proxima Passus</h4>
        <ol>
        <li>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit</li>
        <li>Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet</li>
        <li>Consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt</li>
        <li>Ut labore et dolore magnam aliquam quaerat voluptatem</li>
        </ol>

        <p>At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.</p>
        """

        text_label = QLabel(latin_content)
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
