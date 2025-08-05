import os

# Base directory of the plugin
BASE_DIR = os.path.dirname(__file__)
PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))

CONFIG_DIR = "config"
RESOURCE = "resources"
STYLES = "styles"
MODULES = "modules"
FLOW_MODULE = "flowmodule"



# Resource paths (icons, images, etc.)
class ResourcePaths:
    ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png")
    EYE_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png")
    LIGHTNESS_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "brightness.png")
    DARKNESS_ICON = os.path.join(PLUGIN_ROOT, RESOURCE, "darkness.png")
    LOGOUT_BRIGHT = os.path.join(PLUGIN_ROOT, RESOURCE, "logout_bright.png")
    LOGOUT_DARK = os.path.join(PLUGIN_ROOT, RESOURCE, "logout_dark.png")

# QSS file names (for modular theme loading)
class QssPaths:
    MAIN = "main.qss"
    SIDEBAR = "sidebar.qss"
    HEADER = "header.qss"
    FOOTER = "footer.qss"
    LOGIN = "login.qss"
    LIGHT_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LightTheme.qss")
    DARK_THEME = os.path.join(PLUGIN_ROOT, STYLES, "DarkTheme.qss")
    SIDEBAR_THEME = os.path.join(PLUGIN_ROOT, STYLES, "Sidebar.qss")
    LOGIN_THEME = os.path.join(PLUGIN_ROOT, STYLES, "LoginTheme.qss")

# Config, metadata, manuals, etc.
class ConfigPaths:
    CONFIG = os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json")
    METADATA = os.path.join(PLUGIN_ROOT, "metadata.txt")
    USER_MANUAL = os.path.join(PLUGIN_ROOT, MODULES, "PizzaOrderModuleUserManual.html")

# Module-specific icons
class ModuleIconPaths:
    MODULE_ICONS = {
        "SettingsModule": os.path.join(PLUGIN_ROOT, RESOURCE, "icon.png"),
        "ProjectCardModule": os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee.png"),
        "ProjectFeedModule": os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_s.png"),
        "JokeGeneratorModule": os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        "WeatherUpdateModule": os.path.join(PLUGIN_ROOT, RESOURCE, "weather_icon.png"),
        "ImageOfTheDayModule": os.path.join(PLUGIN_ROOT, RESOURCE, "image_of_the_day.png"),
        "BookQuoteModule": os.path.join(PLUGIN_ROOT, RESOURCE, "book_quote.png"),
        "GPT_ASSISTANT_MODULE": os.path.join(PLUGIN_ROOT, RESOURCE, "eye_icon.png"),
        "HINNAPAKKUJA_MODULE": os.path.join(PLUGIN_ROOT, RESOURCE, "Valisee_u.png"),
    }

    @staticmethod
    def get_module_icon(module_name):
        return ModuleIconPaths.MODULE_ICONS.get(module_name, None)

