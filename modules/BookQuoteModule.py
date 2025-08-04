import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt
from ..BaseModule import BaseModule  # Assuming BaseModule is the parent class
from ..module_manager import BOOK_QUOTE_MODULE  # Import ModuleManager for module management
class BookQuoteModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = BOOK_QUOTE_MODULE
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Header
        self.titleLabel = QLabel("Raamatu tsitaat hetkel")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.titleLabel)

        # Controls
        self.getQuoteButton = QPushButton("Hangi tsitaat")
        self.layout.addWidget(self.getQuoteButton)

        # Output Area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.resultWidget = QWidget()
        self.resultLayout = QVBoxLayout(self.resultWidget)

        self.originalQuoteLabel = QLabel("Originaal tsitaat ilmub siia.")
        self.originalQuoteLabel.setWordWrap(True)
        self.authorLabel = QLabel("Autor ja raamatu pealkiri ilmuvad siia.")
        self.authorLabel.setAlignment(Qt.AlignRight)

        self.resultLayout.addWidget(self.originalQuoteLabel)
        self.resultLayout.addWidget(self.authorLabel)
        self.scrollArea.setWidget(self.resultWidget)
        self.layout.addWidget(self.scrollArea)

        # Connect signals
        self.getQuoteButton.clicked.connect(self.fetch_quote)

    def activate(self):
        """Activate the module."""
        print(f"{self.name} activated.")

    def deactivate(self):
        """Deactivate the module."""
        print(f"{self.name} deactivated.")

    def reset(self):
        """Reset the module to its initial state."""
        self.originalQuoteLabel.setText("Originaal tsitaat ilmub siia.")
        self.authorLabel.setText("Autor ja raamatu pealkiri ilmuvad siia.")

    def run(self):
        """Run the module's main functionality."""
        self.fetch_quote()

    def get_widget(self):
        """Return the main widget for this module."""
        return self.widget

    def fetch_quote(self):
        """Fetch a random book quote."""
        quote_api_url = "https://zenquotes.io/api/random"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

        try:
            # Fetch the quote
            quote_response = requests.get(quote_api_url, headers=headers, timeout=10)
            print(f"[BookQuoteModule] Quote API response: {quote_response.status_code}")
            print(f"[BookQuoteModule] Raw response content: {quote_response.text}")
            quote_response.raise_for_status()

            if "application/json" not in quote_response.headers.get("Content-Type", ""):
                raise ValueError("Invalid content type from quote API. Expected JSON.")

            quote_data = quote_response.json()
            if not isinstance(quote_data, list) or not quote_data:
                raise ValueError("Invalid response format from quote API.")
            content = quote_data[0].get("q", "No quote available.")
            author = quote_data[0].get("a", "Unknown Author")
            self.originalQuoteLabel.setText(f"“{content}”")
            self.authorLabel.setText(f"- {author}")
        except requests.exceptions.ConnectionError as e:
            print(f"[BookQuoteModule] Connection error: {e}")
            self.display_error("Connection error: Unable to reach the server.")
        except requests.exceptions.Timeout as e:
            print(f"[BookQuoteModule] Timeout error: {e}")
            self.display_error("Timeout error: The request took too long to complete.")
        except ValueError as e:
            print(f"[BookQuoteModule] Value error: {e}")
            self.display_error(f"Error: {e}")
        except Exception as e:
            print(f"[BookQuoteModule] General error: {e}")
            self.display_error(f"Error: {e}")

    def display_error(self, message):
        """Display an error message."""
        print(f"[BookQuoteModule] Displaying error: {message}")
        self.originalQuoteLabel.setText("")
        self.authorLabel.setText(f"<span style='color: red;'>{message}</span>")
 