from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QDialog, QTextEdit, QScrollArea
from PyQt5.QtGui import QFont
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from .ModuleConfig import ModuleConfigFactory

class ExtraInfoFrame(QFrame):
    def __init__(self, item_id, module_name=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Determine module type from item_id
        layout.addWidget(ExtraInfoWidget(item_id, module_name))

class ExtraInfoWidget(QWidget):
    def __init__(self, item_id, module_name=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.module_name = module_name
        self._lang = LanguageManager()
        self.config = ModuleConfigFactory.create_config(
            module_type=self.module_name,
            item_id=self.item_id,
            lang_manager=self._lang,
        )
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


        expand_btn_frame = QFrame()
        expand_btn_frame.setObjectName("ExpandButtonFrame")

        expand_layout = QHBoxLayout(expand_btn_frame)      # add a layout to the frame
        expand_layout.setContentsMargins(0, 4, 4, 0)       # left, top, right, bottom
        expand_layout.setSpacing(0)

        expand_btn = QPushButton()
        expand_btn.setObjectName("ExpandButton")
        expand_btn.setToolTip(self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP))
        expand_btn.setFixedSize(22, 22)                    # a little tighter
        expand_btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_EYE))
        expand_btn.setIconSize(QSize(14, 14))              # icon fits inside 22x22 nicely
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setAutoDefault(False); expand_btn.setDefault(False)

        expand_layout.addWidget(expand_btn) 

        expand_btn.clicked.connect(self._show_detailed_overview)
        title_layout.addStretch()

        title_layout.addWidget(expand_btn_frame)

        main_layout.addLayout(title_layout)

        # Dynamic column layout based on configuration
        if self.config.columns:
            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(12)

            for column_config in self.config.columns:
                column = self._create_status_columns(
                    column_config['title'],
                    column_config['color'],
                    column_config['activities']
                )
                columns_layout.addWidget(column)

            main_layout.addLayout(columns_layout)
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def _create_status_columns(self, title, color, activities):
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
        title_suffix = self._lang.translate(
            TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX
        )
        dialog.setWindowTitle(f"{self.config.title} - {title_suffix}")
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
        close_label = self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE)
        close_btn = QPushButton(close_label)
        # Prevent button from being triggered by Return key
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
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
