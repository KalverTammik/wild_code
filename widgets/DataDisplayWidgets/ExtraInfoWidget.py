from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QDialog, QScrollArea
from ...constants.file_paths import QssPaths
from ...constants.button_props import ButtonVariant, ButtonSize
from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from ...utils.url_manager import Module
from .ModuleConfig import ModuleConfigFactory

class ExtraInfoFrame(QFrame):
    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Determine module type from item_id
        layout.addWidget(ExtraInfoWidget(item_data, module_name, lang_manager=lang_manager))

class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("ExtraInfoWidget")
        self.item_data = item_data if isinstance(item_data, dict) else {}
        self.module_name = module_name
        self._lang = lang_manager or LanguageManager()
        self.config = ModuleConfigFactory.create_config(
            module_type=self.module_name,
            item_id=self.item_data,
            lang_manager=self._lang,
        )
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        is_project = str(self.module_name or "").strip().lower() == Module.PROJECT.value

        # Title with expand button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        if not is_project:
            title = QLabel(self.config.title)
            title.setObjectName("ExtraInfoTitle")
            title_layout.addWidget(title)


        expand_btn_frame = QFrame()
        expand_btn_frame.setObjectName("ExpandButtonFrame")

        expand_layout = QHBoxLayout(expand_btn_frame)      # add a layout to the frame
        expand_layout.setContentsMargins(0, 4, 4, 0)       # left, top, right, bottom
        expand_layout.setSpacing(0)

        expand_btn = QPushButton()
        expand_btn.setObjectName("ExpandButton")
        expand_btn.setToolTip(self._detail_button_tooltip())
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

        if is_project:
            ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])
            return

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
        elif self.config.summary_text:
            summary_label = QLabel(self.config.summary_text)
            summary_label.setObjectName("SetupCardDescription")
            summary_label.setWordWrap(True)
            main_layout.addWidget(summary_label)
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def _detail_button_tooltip(self) -> str:
        base = self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP)
        is_project = str(self.module_name or "").strip().lower() == Module.PROJECT.value
        if not is_project:
            return base

        parts = [str(self.config.title or "").strip(), str(self.config.summary_text or "").strip()]
        parts = [part for part in parts if part]
        return "\n".join(parts) if parts else base

    def _create_status_columns(self, title, color, activities):
        """Create a status column with title and activity list."""
        column_widget = QWidget()
        column_widget.setObjectName("ExtraInfoColumn")
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(2)  # Reduced spacing between header and list

        # Column title - removed background color, kept text color
        title_label = QLabel(title)
        title_label.setObjectName("ExtraInfoColumnTitle")
        title_label.setStyleSheet(f"color: {color};")
        title_label.setAlignment(Qt.AlignCenter)
        column_layout.addWidget(title_label)

        # Activity list
        list_widget = QListWidget()
        list_widget.setObjectName("ExtraInfoList")
        list_widget.setFixedHeight(120)  # Set fixed height to ensure at least 3 items are visible

        # Add activities
        for activity_name, icon in activities:
            item = QListWidgetItem(f"{icon} {activity_name}")
            list_widget.addItem(item)

        column_layout.addWidget(list_widget)
        return column_widget

    def _show_detailed_overview(self):
        """Show detailed activity overview in a dialog window."""
        dialog = QDialog(self)
        dialog.setObjectName("ExtraInfoDialog")
        is_project = str(self.module_name or "").strip().lower() == Module.PROJECT.value
        title_suffix = self._lang.translate(
            TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX
        )
        dialog.setWindowTitle(f"{self.config.title} - {title_suffix}")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Title
        if not is_project:
            title = QLabel(self.config.title)
            title.setObjectName("ExtraInfoDialogTitle")
            layout.addWidget(title)

        # Scrollable text area with module-specific content
        scroll_area = QScrollArea()
        scroll_area.setObjectName("ExtraInfoScroll")
        scroll_area.setWidgetResizable(True)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Use module-specific content
        content = self.config.load_detailed_content() or (
            f"<h3>{self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_OVERVIEW_TITLE)}</h3>"
        )

        if isinstance(content, QWidget):
            content.setParent(text_widget)
            text_layout.addWidget(content)
        else:
            text_label = QLabel(content)
            text_label.setObjectName("ExtraInfoContent")
            text_label.setWordWrap(True)
            text_label.setTextFormat(Qt.RichText)
            text_layout.addWidget(text_label)

        scroll_area.setWidget(text_widget)
        layout.addWidget(scroll_area)

        # Close button
        close_label = self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE)
        close_btn = QPushButton(close_label)
        close_btn.setObjectName("ConfirmButton")
        close_btn.setProperty("variant", ButtonVariant.SUCCESS)
        close_btn.setProperty("btnSize", ButtonSize.MEDIUM)
        # Prevent button from being triggered by Return key
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        ThemeManager.apply_module_style(dialog, [QssPaths.MODULE_INFO])

        dialog.exec_()
