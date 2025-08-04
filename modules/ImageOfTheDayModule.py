import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QScrollArea, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
from ..BaseModule import BaseModule  # Assuming BaseModule is the parent class
from ..module_manager import IMAGE_OF_THE_DAY_MODULE  # Import ModuleManager for module management
class ImageOfTheDayModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = IMAGE_OF_THE_DAY_MODULE
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Header
        self.titleLabel = QLabel("NASA Image of the Day")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.titleLabel)

        # Input Controls
        inputLayout = QHBoxLayout()
        self.dateEdit = QDateEdit(calendarPopup=True)
        self.dateEdit.setDate(QDate.currentDate())
        self.todayButton = QPushButton("Today")
        self.fetchButton = QPushButton("Fetch")
        inputLayout.addWidget(self.dateEdit)
        inputLayout.addWidget(self.todayButton)
        inputLayout.addWidget(self.fetchButton)
        self.layout.addLayout(inputLayout)

        # Output Area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.resultWidget = QWidget()
        self.resultLayout = QVBoxLayout(self.resultWidget)
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.descriptionLabel = QLabel()
        self.descriptionLabel.setWordWrap(True)
        self.resultLayout.addWidget(self.imageLabel)
        self.resultLayout.addWidget(self.descriptionLabel)
        self.scrollArea.setWidget(self.resultWidget)
        self.layout.addWidget(self.scrollArea)

        # Connect signals
        self.todayButton.clicked.connect(self.set_today_date)
        self.fetchButton.clicked.connect(self.fetch_image)

    def activate(self):
        """Activate the module."""
        print(f"{self.name} activated.")

    def deactivate(self):
        """Deactivate the module."""
        print(f"{self.name} deactivated.")

    def reset(self):
        """Reset the module to its initial state."""
        self.dateEdit.setDate(QDate.currentDate())
        self.imageLabel.clear()
        self.descriptionLabel.clear()

    def run(self):
        """Run the module's main functionality."""
        self.fetch_image()

    def get_widget(self):
        """Return the main widget for this module."""
        return self.widget

    def set_today_date(self):
        """Set the date to today."""
        self.dateEdit.setDate(QDate.currentDate())

    def fetch_image(self):
        """Fetch the image and metadata from NASA's APOD API."""
        date = self.dateEdit.date().toString("yyyy-MM-dd")
        api_url = f"https://api.nasa.gov/planetary/apod?date={date}&api_key=DEMO_KEY"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            if data.get("media_type") == "image":
                self.display_image(data["url"], data["title"], data["explanation"])
            else:
                self.display_error("No image available for the selected date.")
        except Exception as e:
            self.display_error(f"Error fetching image: {e}")

    def display_image(self, image_url, title, description):
        """Display the fetched image and metadata."""
        try:
            image_data = requests.get(image_url).content
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.imageLabel.setPixmap(pixmap.scaled(self.scrollArea.width(), self.scrollArea.height(), Qt.KeepAspectRatio))
            self.descriptionLabel.setText(f"<b>{title}</b><br>{description}")
        except Exception as e:
            self.display_error(f"Error displaying image: {e}")

    def display_error(self, message):
        """Display an error message."""
        self.imageLabel.clear()
        self.descriptionLabel.setText(f"<span style='color: red;'>{message}</span>")
