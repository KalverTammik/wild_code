from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QDateEdit, QScrollArea, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QDate
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .ImageOfTheDayLogic import ImageOfTheDayLogic

class ImageOfTheDayUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import IMAGE_OF_THE_DAY_MODULE
        self.name = IMAGE_OF_THE_DAY_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to ImageOfTheDayUI for theme application.")

    def setup_ui(self):
        self.setObjectName("ImageOfTheDayModule")
        layout = QVBoxLayout(self)
        self.dateEdit = QDateEdit(QDate.currentDate())
        self.dateEdit.setCalendarPopup(True)
        self.fetchButton = QPushButton(self.lang_manager.translate("image_of_the_day_fetch_button"))
        self.fetchButton.clicked.connect(self.on_fetch)
        self.imageLabel = QLabel(self.lang_manager.translate("image_of_the_day_placeholder"))
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel = QLabel()
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.explanationLabel = QLabel()
        self.explanationLabel.setWordWrap(True)
        layout.addWidget(self.dateEdit)
        layout.addWidget(self.fetchButton)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.explanationLabel)
        self.on_fetch()

    def on_fetch(self):
        date = self.dateEdit.date().toString("yyyy-MM-dd")
        url, title, explanation, error = ImageOfTheDayLogic.fetch_image(date)
        if error:
            self.imageLabel.setText(self.lang_manager.translate("image_of_the_day_error").format(error=error))
            self.titleLabel.setText("")
            self.explanationLabel.setText("")
            return
        self.titleLabel.setText(title or "")
        if url:
            self.imageLabel.setText(f'<a href="{url}">{self.lang_manager.translate("image_of_the_day_view_image")}</a>')
            self.imageLabel.setOpenExternalLinks(True)
        else:
            self.imageLabel.setText(self.lang_manager.translate("image_of_the_day_no_image"))
        self.explanationLabel.setText(explanation or "")

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.dateEdit.setDate(QDate.currentDate())
        self.imageLabel.setText(self.lang_manager.translate("image_of_the_day_placeholder"))
        self.titleLabel.setText("")
        self.explanationLabel.setText("")
    def run(self):
        self.on_fetch()
    def get_widget(self):
        return self
