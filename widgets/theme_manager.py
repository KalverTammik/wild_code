from PyQt5.QtCore import QFile, QDir
from PyQt5.QtWidgets import QApplication
import os
from ..constants.file_paths import FilePaths

class ThemeManager:
    @staticmethod
    def apply_theme(widget, theme_path):
        """
        Apply the QSS theme to the specified widget only.

        :param widget: The widget to apply the theme to.
        :param theme_path: Path to the QSS theme file.
        """
        try:
            with open(theme_path, "r") as file:
                theme = file.read()
                widget.setStyleSheet(theme)  # Apply the style only to the widget
        except FileNotFoundError:
            print(f"Theme file not found: {theme_path}")
        except Exception as e:
            print(f"Error applying theme: {e}")

    @staticmethod
    def toggle_theme(widget, current_theme, switch_button):
        """
        Toggle between light and dark themes for the specified widget.

        :param widget: The widget to apply the theme to.
        :param current_theme: The current theme ("light" or "dark").
        :return: The new theme ("light" or "dark").
        """
        if current_theme == "light":
            ThemeManager.apply_dark_theme(widget)
            switch_button.setText("Switch to Light Mode")
            return "dark"
        else:
            ThemeManager.apply_light_theme(widget)
            switch_button.setText("Switch to Dark Mode")
            return "light"

    @staticmethod
    def apply_dark_theme(widget):
        """
        Apply the dark theme to the specified widget.
        """
        dark_theme_path = FilePaths.get_file_path(FilePaths.DARK_THEME)
        ThemeManager.apply_theme(widget, dark_theme_path)

    @staticmethod
    def apply_light_theme(widget):
        """
        Apply the light theme to the specified widget.
        """
        light_theme_path = FilePaths.get_file_path(FilePaths.LIGHT_THEME)
        ThemeManager.apply_theme(widget, light_theme_path)
