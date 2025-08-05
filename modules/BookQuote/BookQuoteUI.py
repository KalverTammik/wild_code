from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .BookQuoteLogic import BookQuoteLogic


class BookQuoteUI(QWidget):
    def activate(self):
        """Activate the module."""
        pass

    def deactivate(self):
        """Deactivate the module."""
        pass

    def reset(self):
        """Reset the module to its initial state."""
        self.originalQuoteLabel.setText(self.lang_manager.translate("book_quote_placeholder"))
        self.authorLabel.setText(self.lang_manager.translate("book_quote_author_placeholder"))

    def run(self):
        """Run the module's main functionality."""
        self.on_get_quote()
    def get_widget(self):
        """Return the main widget for this module (self)."""
        return self
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import BOOK_QUOTE_MODULE
        self.name = BOOK_QUOTE_MODULE  # Unique name for module registration
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.theme_dir = theme_dir
        self.qss_files = qss_files or ["main.qss", "sidebar.qss"]
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to BookQuoteUI for theme application.")

    def setup_ui(self):
        self.setObjectName("BookQuoteModule")
        layout = QVBoxLayout(self)

        # Header
        self.titleLabel = QLabel(self.lang_manager.translate("book_quote_title"))
        self.titleLabel.setObjectName("DialogTitle")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.titleLabel)

        # Controls
        self.getQuoteButton = QPushButton(self.lang_manager.translate("book_quote_get_button"))
        self.getQuoteButton.setObjectName("PrimaryButton")
        layout.addWidget(self.getQuoteButton)

        # Output Area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.resultWidget = QWidget()
        self.resultLayout = QVBoxLayout(self.resultWidget)

        self.originalQuoteLabel = QLabel(self.lang_manager.translate("book_quote_placeholder"))
        self.originalQuoteLabel.setWordWrap(True)
        self.authorLabel = QLabel(self.lang_manager.translate("book_quote_author_placeholder"))
        self.authorLabel.setAlignment(Qt.AlignRight)

        self.resultLayout.addWidget(self.originalQuoteLabel)
        self.resultLayout.addWidget(self.authorLabel)
        self.scrollArea.setWidget(self.resultWidget)
        layout.addWidget(self.scrollArea)

        self.getQuoteButton.clicked.connect(self.on_get_quote)

    def on_get_quote(self):
        content, author, error = BookQuoteLogic.fetch_quote()
        if error:
            self.display_error(error)
        else:
            self.originalQuoteLabel.setText(f"“{content}”")
            self.authorLabel.setText(f"- {author}")

    def display_error(self, message):
        self.originalQuoteLabel.setText("")
        self.authorLabel.setText(f"<span style='color: red;'>{self.lang_manager.translate('book_quote_error')}: {message}</span>")
