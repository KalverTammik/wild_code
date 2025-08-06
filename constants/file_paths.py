

import os
from .base_paths import BASE_DIR, PLUGIN_ROOT, CONFIG_DIR, RESOURCE, STYLES, MODULES, FLOW_MODULE, DATA_DIR
from .module_names import HINNAPAKKUJA_MODULE, GPT_ASSISTANT_MODULE

# Data paths (for module data files)
class DataPaths:
    TYPICAL_NODES = os.path.join(PLUGIN_ROOT, MODULES, HINNAPAKKUJA_MODULE, DATA_DIR, 'typical_nodes.json')
    PRICE_CACHE = os.path.join(PLUGIN_ROOT, MODULES, HINNAPAKKUJA_MODULE, DATA_DIR, 'price_cache.json')

# GptAssistant module paths
class GptAssistantPaths:
    ENV = os.path.join(PLUGIN_ROOT, MODULES, GPT_ASSISTANT_MODULE, '.env')
    README = os.path.join(PLUGIN_ROOT, MODULES, GPT_ASSISTANT_MODULE, 'README_QGIS_OPENAI.txt')



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

# Theme directory paths (for modular theme loading)
class StylePaths:
    DARK = os.path.join(PLUGIN_ROOT, STYLES, "Dark")
    LIGHT = os.path.join(PLUGIN_ROOT, STYLES, "Light")

# Config, metadata, manuals, etc.
class ConfigPaths:
    CONFIG = os.path.join(PLUGIN_ROOT, CONFIG_DIR, "config.json")
    METADATA = os.path.join(PLUGIN_ROOT, "metadata.txt")
    USER_MANUAL = os.path.join(PLUGIN_ROOT, MODULES, "PizzaOrderModuleUserManual.html")



