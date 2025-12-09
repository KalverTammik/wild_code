from ...constants.help_urls import DEFAULT_HELP_URL, HELP_URLS
from ...utils.url_manager import Module
from ...module_manager import ModuleManager


import webbrowser


class ShowHelp:
    """Utility class for handling help functionality across the application."""

    @staticmethod
    def show_help_for_module():
        """Handle help button click by opening contextual help URL based on active module or page.

        Args:
            active_module: The currently active module dict from moduleManager.getActiveModule()
        """
        module_name = ModuleManager().getActiveModuleName()
        try:
            # First check if Home module is currently active
            if module_name and module_name == Module.HOME.value:
                # Home/Welcome page is active - open general QGIS plugin help
                help_url = "https://help.kavitro.com/et/collections/10606065-kavitro-qgis-plugin"
                webbrowser.open(help_url)
                return

            # Check for other active modules
            if module_name:   
                # Get the help URL for the active module, fallback to default if not found
                help_url = HELP_URLS.get(module_name, DEFAULT_HELP_URL)
                webbrowser.open(help_url)
            else:
                # No active module and not on welcome page, open main help page
                webbrowser.open(DEFAULT_HELP_URL)
        except Exception as e:
            # Log error but don't crash - fallback to main help page
            try:
                webbrowser.open(DEFAULT_HELP_URL)
            except Exception:
                pass