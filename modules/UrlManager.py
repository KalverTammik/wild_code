from enum import Enum
from typing import Dict, Any
import requests
import webbrowser

class Module(Enum):
    """Enumeration of available modules."""
    PROJECT = "project"
    CONTRACT = "contract"
    USER = "user"
    # Add more modules as needed

class WebModules:
    """
    Provides URL paths for each module.
    """
    PROJECTS = '/projects/'
    CONTRACTS = '/contracts/'
    USERS = '/users/'
    _module_paths = {
        Module.PROJECT: PROJECTS,
        Module.CONTRACT: CONTRACTS,
        Module.USER: USERS,
    }

    @classmethod
    def get_module_path(cls, module: Module) -> str:
        """Get the URL path for a given module."""
        if module not in cls._module_paths:
            raise ValueError(f"Invalid module name: {module}")
        return cls._module_paths[module]

class OpenLink:
    """
    Builds full web and API links for modules using config.
    """
    def __init__(self, config: Dict[str, Any]):
        self.web_base = config.get('weblink', '')
        self.api_base = config.get('api_base', '')

    def web_link_by_module(self, module: Module) -> str:
        """Return the full web link for a module."""
        return f"{self.web_base.rstrip('/')}" + WebModules.get_module_path(module)

    def api_link_by_module(self, module: Module) -> str:
        """Return the full API link for a module."""
        return f"{self.api_base.rstrip('/')}" + WebModules.get_module_path(module)


class WebLinks:
    """
    Holds static links from config (home, privacy, terms).
    """
    def __init__(self, config: Dict[str, Any]):
        self.home = config.get('weblink', '')
        self.privacy = config.get('privacy', '')
        self.terms = config.get('terms', '')

class loadWebpage:
    @staticmethod
    def open_webpage(web_link: str):
        """Open a web page in the default browser, following redirects."""
        try:
            response = requests.get(web_link, verify=False, timeout=10)
            webbrowser.open(response.url)
        except requests.exceptions.Timeout:
            print("Request timed out")
        except Exception as e:
            print(f"Error opening webpage: {e}")
        
