import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from constants.module_names import PROJECTS_MODULE, CONTRACT_MODULE, SETTINGS_MODULE, PROPERTY_MODULE

class SideBarButtonNames:
    BUTTONS = {
        PROJECTS_MODULE: "Projektid",
        CONTRACT_MODULE: "Lepingud",
        PROPERTY_MODULE: "Kinnistud",
        SETTINGS_MODULE: "Seaded",
        "HOME": "Avaleht"
    }
