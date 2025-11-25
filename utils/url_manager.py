
from enum import Enum

from typing import Dict, Any
import requests
import webbrowser
from ..config.setup import config


class Module(Enum):
    PROJECT = "project"
    CONTRACT = "contract"
    COORDINATION = "coordination"
    LETTER = "letter"
    SPECIFICATION = "specification"
    EASEMENT = "easement"
    ORDINANCE = "ordinance"
    SUBMISSION = "submission"    
    TAGS = "tags"
    STATUSES = "statuses"

    # user related
    USER = "user"

    # task related modules
    ASBUILT = "task"
    WORKS = "works"
    TASK = "task"

    # Properties related
    PROPERTY = "property"

    SETTINGS = "settings"

    HOME = "home"

    SIGNALTEST = "signaltest"


    def singular(self, upper: bool = False) -> str:
        s = self.value
        return s.upper() if upper else s

    def plural(self, upper: bool = False) -> str:
        # Special cases for irregular plurals
        plurals = {
            Module.PROPERTY: "properties",
            Module.CONTRACT: "contracts", 
            Module.PROJECT: "projects",
        }
        plural = plurals.get(self.value, self.value + "s")
        return plural.upper() if upper else plural

    # mugav lühike API:
    def api_key(self) -> str:
        """Sageli vajame API-s ainsust ÜLAKIRJAS (nt BACKEND_ENTITY)."""
        return self.singular(upper=True)

    def api_collection(self) -> str:
        """Sageli vajame API-s mitmust ÜLAKIRJAS (nt statuses where: MODULE=PROJECTS)."""
        return self.plural(upper=True)


class loadWebpage:
    @staticmethod
    def open_webpage(web_link: str):
        """Open a web page in the default browser, following redirects."""
        try:
            response = requests.get(web_link, verify=False, timeout=10)
            webbrowser.open(response.url)
        except requests.exceptions.Timeout:
            # Request timed out
            pass
        except Exception as e:
            try:
                from .logger import error as log_error
                log_error(f"Error opening webpage: {e}")
            except Exception:
                pass
        
class OpenLink:
    def __init__(self):
        self.main = config.get('weblink', '')
        self.privacy = config.get('privacy', '')
        self.terms = config.get('terms', '')

    @staticmethod
    def weblink_by_module(module_path: str) -> str:
        """
        Build a full link like: https://example.com/projects/
        Usage:

        """
        return f"{OpenLink().main}/{module_path}"