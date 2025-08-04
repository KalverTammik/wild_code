import requests
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QFrame, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from ..BaseModule import BaseModule
from ..module_manager import WEATHER_UPDATE_MODULE

class WeatherUpdateModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = WEATHER_UPDATE_MODULE
        self.base_url = "https://wttr.in/"

        # Set up the module's UI
        layout = QVBoxLayout()
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Enter city name...")
        self.searchBar.setText("Pärnu")  # Set default location to Pärnu
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.fetch_weather)
        self.weatherLabel = QLabel("Weather information will appear here.")
        self.forecastFrame = QFrame()
        self.forecastLayout = QGridLayout()
        self.forecastFrame.setLayout(self.forecastLayout)

        searchLayout = QHBoxLayout()
        searchLayout.addWidget(self.searchBar)
        searchLayout.addWidget(self.searchButton)

        layout.addLayout(searchLayout)
        layout.addWidget(self.weatherLabel)
        layout.addWidget(self.forecastFrame)
        self.widget.setLayout(layout)

        # Fetch weather for the default location
        self.fetch_weather()

    def fetch_weather(self):
        city = self.searchBar.text().strip()
        if not city:
            self.weatherLabel.setText("Please enter a city name.")
            return

        try:
            # Fetch weather data from wttr.in
            weather_url = f"{self.base_url}{city}?format=j1"
            weather_response = requests.get(weather_url).json()

            # Extract current weather
            current_condition = weather_response["current_condition"][0]
            temp = current_condition["temp_C"]
            description = current_condition["weatherDesc"][0]["value"]
            self.weatherLabel.setText(f"Current Weather in {city}: {temp}°C, {description}")

            # Extract 3-day forecast
            forecast = weather_response["weather"]
            self.update_forecast_cards(forecast)

        except Exception as e:
            self.weatherLabel.setText(f"Error fetching weather data: {str(e)}")

    def update_forecast_cards(self, forecast):
        # Clear existing forecast cards
        for i in reversed(range(self.forecastLayout.count())):
            widget = self.forecastLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add new forecast cards
        for i, day in enumerate(forecast):
            date = day["date"]
            description = day["hourly"][0]["weatherDesc"][0]["value"]
            temp = day["hourly"][0]["tempC"]

            card = QFrame()
            cardLayout = QVBoxLayout()
            card.setLayout(cardLayout)
            card.setStyleSheet("border: 1px solid #ccc; border-radius: 8px; padding: 10px;")

            dateLabel = QLabel(date)
            dateLabel.setStyleSheet("font-weight: bold;")
            descriptionLabel = QLabel(description)
            tempLabel = QLabel(f"{temp}°C")

            # Optionally, add an icon (placeholder for now)
            iconLabel = QLabel()
            iconLabel.setPixmap(QPixmap(":/icons/weather_placeholder.png").scaled(50, 50, Qt.KeepAspectRatio))

            cardLayout.addWidget(iconLabel, alignment=Qt.AlignCenter)
            cardLayout.addWidget(dateLabel, alignment=Qt.AlignCenter)
            cardLayout.addWidget(descriptionLabel, alignment=Qt.AlignCenter)
            cardLayout.addWidget(tempLabel, alignment=Qt.AlignCenter)

            self.forecastLayout.addWidget(card, i // 3, i % 3)  # Arrange cards in a grid
