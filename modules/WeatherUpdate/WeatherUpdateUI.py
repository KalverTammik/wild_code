from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QFrame, QGridLayout
from PyQt5.QtCore import Qt
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .WeatherUpdateLogic import WeatherUpdateLogic

class WeatherUpdateUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import WEATHER_UPDATE_MODULE
        self.name = WEATHER_UPDATE_MODULE
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
            raise ValueError("theme_dir must be provided to WeatherUpdateUI for theme application.")

    def setup_ui(self):
        self.setObjectName("WeatherUpdateModule")
        layout = QVBoxLayout(self)
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText(self.lang_manager.translate("weather_search_placeholder"))
        self.searchBar.setText("Pärnu")
        self.searchButton = QPushButton(self.lang_manager.translate("weather_search_button"))
        self.searchButton.clicked.connect(self.on_search)
        self.weatherLabel = QLabel(self.lang_manager.translate("weather_info_placeholder"))
        self.forecastFrame = QFrame()
        self.forecastLayout = QGridLayout()
        self.forecastFrame.setLayout(self.forecastLayout)
        searchLayout = QHBoxLayout()
        searchLayout.addWidget(self.searchBar)
        searchLayout.addWidget(self.searchButton)
        layout.addLayout(searchLayout)
        layout.addWidget(self.weatherLabel)
        layout.addWidget(self.forecastFrame)
        self.fetch_weather()

    def on_search(self):
        self.fetch_weather()

    def fetch_weather(self):
        city = self.searchBar.text().strip()
        (temp, description, forecast), _, error = WeatherUpdateLogic.fetch_weather(city)
        if error == "no_city":
            self.weatherLabel.setText(self.lang_manager.translate("weather_enter_city"))
            return
        if error:
            msg = self.lang_manager.translate("weather_error").format(error=error)
            self.weatherLabel.setText(msg)
            return
        label = self.lang_manager.translate("weather_current_label").format(city=city, temp=temp, description=description)
        self.weatherLabel.setText(label)
        self.update_forecast_cards(forecast)

    def update_forecast_cards(self, forecast):
        for i in reversed(range(self.forecastLayout.count())):
            widget = self.forecastLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if not forecast:
            return
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
            cardLayout.addWidget(dateLabel, alignment=Qt.AlignCenter)
            cardLayout.addWidget(descriptionLabel, alignment=Qt.AlignCenter)
            cardLayout.addWidget(tempLabel, alignment=Qt.AlignCenter)
            self.forecastLayout.addWidget(card, i // 3, i % 3)

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.searchBar.setText("Pärnu")
        self.weatherLabel.setText(self.lang_manager.translate("weather_info_placeholder"))
        self.update_forecast_cards([])
    def run(self):
        self.fetch_weather()
    def get_widget(self):
        return self
