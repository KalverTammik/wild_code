import os

# Base directory of the plugin
BASE_DIR = os.path.dirname(__file__)
PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))
RESOURCE = "resources"
STYLES = "styles"
MODULES = "modules"
FLOW_MODULE = "flowmodule"

class FilePaths:
    ICON = "icon"
    EYE_ICON = "eye_icon"
    LIGHT_THEME = "light_theme"
    DARK_THEME = "dark_theme"
    SIDEBAR = "sidebar"
    LOGIN_DIALOG = "login_dialog"
    
    MODULE_ICONS = {
        "SettingsModule": os.path.join(PLUGIN_ROOT, RESOURCE, "icon.png"),
        "ProjectCardModule": os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee.png"),
        "ProjectFeedModule": os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_s.png"),
        "JokeGeneratorModule": os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        "WeatherUpdateModule": os.path.join(PLUGIN_ROOT, RESOURCE, "weather_icon.png"),
        "ImageOfTheDayModule": os.path.join(PLUGIN_ROOT, RESOURCE, "image_of_the_day.png"),
        "BookQuoteModule": os.path.join(PLUGIN_ROOT, RESOURCE, "book_quote.png"),
    }

    @staticmethod
    def get_module_icon(module_name):
        """Retrieve the icon path for a given module name."""
        return FilePaths.MODULE_ICONS.get(module_name, None)  # Return None if no icon is found

    @staticmethod
    def get_file_path(file_key):
        paths = {
            FilePaths.ICON: os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png"),
            FilePaths.EYE_ICON: os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
            FilePaths.LIGHT_THEME: os.path.join(PLUGIN_ROOT, STYLES, "LightTheme.qss"),
            FilePaths.DARK_THEME: os.path.join(PLUGIN_ROOT, STYLES, "DarkTheme.qss"),
            FilePaths.SIDEBAR: os.path.join(PLUGIN_ROOT, STYLES, "Sidebar.qss"),
            FilePaths.LOGIN_DIALOG: os.path.join(PLUGIN_ROOT, STYLES, "LoginTheme.qss"),
        }
        return paths.get(file_key, None)  # Return None if the key is not found

