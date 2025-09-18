import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from constants.module_names import PROJECTS_MODULE, CONTRACT_MODULE, SETTINGS_MODULE, PROPERTY_MODULE, DIALOG_SIZE_WATCHER_MODULE

class SideBarButtonNames:
    BUTTONS = {
        PROJECTS_MODULE: "Projects",
        CONTRACT_MODULE: "Contract",
        PROPERTY_MODULE: "Properties",
        SETTINGS_MODULE: "Settings",
        DIALOG_SIZE_WATCHER_MODULE: "Dialog Size Watcher",
        "HOME": "Home"
    }
