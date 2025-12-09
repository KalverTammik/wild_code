import os
from .base_paths import PLUGIN_ROOT, RESOURCE, ICON_FOLDER
from ..utils.url_manager import Module

class IconNames:
    RANDOM_ICON_NAME = "Valisee_s.png"
    VALISEE_V_ICON_NAME = "Valisee_v.png"

    ICON_LOGOUT = "Logout.png"
    ICON_HELP = "Otsing.png"
    ICON_INFO = "Abikeskus1.png"
    ICON_ADD = "Add.png"
    ICON_REFRESH = "Reset2.png"
    LIGHTNESS_ICON = "brightness.png"
    DARKNESS_ICON = "darkness.png"
    LOGOUT_BRIGHT = "logout_bright.png"
    LOGOUT_DARK = "logout_dark.png"
    ICON_EYE = "show.png"
    ICON_SETTINGS = "Seaded.png"
    ICON_FOLDERICON = "Folder.png"
    ICON_CONTACTCT = "Kontaktid.png"
    ICON_SHOW_ON_MAP = "Mine kaardile.png"
    ICON_LIST = "down-arrow.png"


    def get_icon(icon_name):
        ROOT_ICONS = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER)
        path = os.path.join(ROOT_ICONS, icon_name)
        return path


#Module icons 
class ModuleIcons:
    ICON_CONTRACT = "Lepingud.png"
    ICON_HOME = "Avaleht.png"
    ICON_SETTINGS = "Seaded.png"
    ICON_PROJECTS = "Projektid.png"
    ICON_PROPERTY = "Kinnistud.png"
    ICON_SIGNAL_TEST = "Abikeskus1.png"
    ICON_COORDINATION = "Kooskõlastused.png"
    

class MiscIcons:
    ICON_IS_PRIVATE = "show.png"
    ICON_IS_CLIENT = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER,  "icons8-client-50.png")

class ModuleIconPaths:

    ROOT_ICONS = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER)

    MODULE_ICONS = {
        # Core (keep existing module icon mappings; do not change yet)
        Module.SETTINGS.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_SETTINGS),
        Module.HOME.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_HOME),
        Module.PROJECT.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_PROJECTS),
        Module.CONTRACT.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_CONTRACT),
        Module.PROPERTY.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_PROPERTY),
        Module.SIGNALTEST.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_SIGNAL_TEST),
        Module.COORDINATION.value: os.path.join(ROOT_ICONS, ModuleIcons.ICON_COORDINATION),
    }

    @staticmethod
    def get_module_icon(module_name) -> str:
        module_name = module_name.lower()
        path = ModuleIconPaths.MODULE_ICONS.get(module_name)
        return path
    
