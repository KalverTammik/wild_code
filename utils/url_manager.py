
from enum import Enum

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

    # task related modules
    ASBUILT = "task"
    WORKS = "works"
    TASK = "task"


    # user related
    USER = "user"

    PROPERTY = "property"
    SETTINGS = "settings"
    HOME = "home"
    SIGNALTEST = "signaltest"


    STATUSES = "statuses"
    TYPES = "type"

class ModuleSupports(Enum):
    TAGS = "tags"
    STATUSES = "statuses"
    TYPES = "type"


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