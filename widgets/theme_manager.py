from PyQt5.QtCore import QFile, QDir
from PyQt5.QtWidgets import QApplication
import os
from ..constants.file_paths import ResourcePaths

import glob

class ThemeManager:
    @staticmethod
    def save_theme_setting(theme_name):
        from qgis.core import QgsSettings
        settings = QgsSettings()
        settings.setValue("wild_code/theme", theme_name)

    @staticmethod
    def load_theme_setting():
        from qgis.core import QgsSettings
        settings = QgsSettings()
        theme = settings.value("wild_code/theme", "light")
        return theme

    @staticmethod
    def set_initial_theme(widget, switch_button, theme_base_dir, qss_files=None):
        """
        Loads the theme from QGIS settings and applies it, updating the switch button icon.
        Returns the theme name ("light" or "dark").
        """
        from PyQt5.QtGui import QIcon
        # Support for logout icon
        header_widget = getattr(widget, 'header_widget', None)
        theme = ThemeManager.load_theme_setting()
        if theme == "dark":
            ThemeManager.apply_dark_theme(widget, theme_base_dir, qss_files)
            icon_path = ResourcePaths.LIGHTNESS_ICON
            if switch_button is not None:
                switch_button.setIcon(QIcon(icon_path))
                switch_button.setText("")
            if header_widget:
                logout_icon_path = ResourcePaths.LOGOUT_BRIGHT
                if logout_icon_path:
                    header_widget.set_logout_icon(QIcon(logout_icon_path))
        else:
            ThemeManager.apply_light_theme(widget, theme_base_dir, qss_files)
            icon_path = ResourcePaths.DARKNESS_ICON
            if switch_button is not None:
                switch_button.setIcon(QIcon(icon_path))
                switch_button.setText("")
            if header_widget:
                logout_icon_path = ResourcePaths.LOGOUT_DARK
                if logout_icon_path:
                    header_widget.set_logout_icon(QIcon(logout_icon_path))
        return theme
    @staticmethod
    def apply_theme(widget, theme_dir, qss_files=None):
        """
        Apply the QSS theme(s) from the specified theme directory to the widget.

        :param widget: The widget to apply the theme to.
        :param theme_dir: Path to the theme directory (e.g., styles/Dark/ or styles/Light/).
        :param qss_files: List of QSS filenames to load (e.g., ["main.qss", "sidebar.qss"]). If None, loads all .qss files in the directory.
        """
        try:
            theme = ""
            if qss_files is None:
                # Load all .qss files in the directory, sorted alphabetically
                qss_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(theme_dir, "*.qss"))])
            for qss_file in qss_files:
                qss_path = os.path.join(theme_dir, qss_file)
                if os.path.exists(qss_path):
                    with open(qss_path, "r", encoding="utf-8") as file:
                        theme += file.read() + "\n"
            widget.setStyleSheet(theme)
        except Exception as e:
            print(f"Error applying theme from {theme_dir}: {e}")

    @staticmethod
    def toggle_theme(widget, current_theme, switch_button, theme_base_dir, qss_files=None):
        """
        Toggle between light and dark themes for the specified widget, updating the switch button icon only.
        Saves the new theme to QGIS settings.
        """
        from PyQt5.QtGui import QIcon
        header_widget = getattr(widget, 'header_widget', None)
        if current_theme == "light":
            ThemeManager.apply_dark_theme(widget, theme_base_dir, qss_files)
            icon_path = ResourcePaths.LIGHTNESS_ICON
            switch_button.setIcon(QIcon(icon_path))
            switch_button.setText("")
            if header_widget:
                logout_icon_path = ResourcePaths.LOGOUT_BRIGHT
                if logout_icon_path:
                    header_widget.set_logout_icon(QIcon(logout_icon_path))
            ThemeManager.save_theme_setting("dark")
            return "dark"
        else:
            ThemeManager.apply_light_theme(widget, theme_base_dir, qss_files)
            icon_path = ResourcePaths.DARKNESS_ICON
            switch_button.setIcon(QIcon(icon_path))
            switch_button.setText("")
            if header_widget:
                logout_icon_path = ResourcePaths.LOGOUT_DARK
                if logout_icon_path:
                    header_widget.set_logout_icon(QIcon(logout_icon_path))
            ThemeManager.save_theme_setting("light")
            return "light"

    @staticmethod
    def apply_dark_theme(widget, theme_base_dir, qss_files=None):
        """
        Apply the dark theme to the specified widget.
        :param theme_base_dir: The base styles directory (e.g., styles/).
        :param qss_files: List of QSS files to load (optional).
        """
        dark_theme_dir = os.path.join(theme_base_dir, "Dark")
        ThemeManager.apply_theme(widget, dark_theme_dir, qss_files)

    @staticmethod
    def apply_light_theme(widget, theme_base_dir, qss_files=None):
        """
        Apply the light theme to the specified widget.
        :param theme_base_dir: The base styles directory (e.g., styles/).
        :param qss_files: List of QSS files to load (optional).
        """
        light_theme_dir = os.path.join(theme_base_dir, "Light")
        ThemeManager.apply_theme(widget, light_theme_dir, qss_files)
