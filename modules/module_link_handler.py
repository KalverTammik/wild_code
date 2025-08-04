from enum import Enum
from typing import Dict, Any

class Module(Enum):
    """Enumeration of available modules."""
    PROJECT = "project"
    CONTRACT = "contract"
    USER = "user"
    # Add more modules as needed

class WebModules:
    """
    Class containing URL paths for each module and methods to retrieve web links.
    """
    PROJECTS = '/projects/'
    CONTRACTS = '/contracts/'
    USERS = '/users/'
    # Add more module paths as needed

    _web_links_by_module = {
        Module.PROJECT: PROJECTS,
        Module.CONTRACT: CONTRACTS,
        Module.USER: USERS,
        # Extend as needed
    }

    def get_web_link(self, module: Module) -> str:
        """
        Get the web link path for a given module.
        Raises ValueError if the module is invalid.
        """
        if module not in self._web_links_by_module:
            raise ValueError(f"Invalid module name: {module}")
        return self._web_links_by_module[module]

    @staticmethod
    def weblink_privacy(config: Dict[str, Any]) -> str:
        """Return the privacy policy link from config."""
        return config.get('privacy', '')

    @staticmethod
    def weblink_terms_of_use(config: Dict[str, Any]) -> str:
        """Return the terms of use link from config."""
        return config.get('terms', '')

class OpenLink:
    """
    Handler for building and retrieving full web links using configuration.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with main, privacy, and terms links from the config.
        """
        self.main = config.get('weblink', '')
        self.privacy = config.get('privacy', '')
        self.terms = config.get('terms', '')

    def build_full_link(self, module_path: str) -> str:
        """
        Build a full link by appending a module path to the main URL.
        """
        return f"{self.main.rstrip('/')}" + module_path

    def weblink_by_module(self, module: Module) -> str:
        """
        Get the full web link for a given module.
        """
        module_path = WebModules().get_web_link(module)
        return self.build_full_link(module_path)

    def get_module_link(self, module: Module) -> str:
        """
        Alias for weblink_by_module for compatibility.
        """
        return self.weblink_by_module(module)

# Example usage:
if __name__ == "__main__":
    # Assume config is already loaded as a dictionary
    config = {
        "weblink": "https://example.com",
        "privacy": "https://example.com/privacy",
        "terms": "https://example.com/terms"
    }

    open_link = OpenLink(config)
    print(open_link.weblink_by_module(Module.PROJECT))  # https://example.com/projects/
    print(WebModules().get_web_link(Module.CONTRACT))   # /contracts/
    print(WebModules.weblink_privacy(config))           # https://example.com/privacy
    print(WebModules.weblink_terms_of_use(config))      # https://example.com/terms
