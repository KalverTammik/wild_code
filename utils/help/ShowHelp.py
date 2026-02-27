from ...constants.help_urls import DEFAULT_HELP_URL, HELP_URLS
from ...utils.url_manager import Module, loadWebpage
from ...module_manager import ModuleManager


class ShowHelp:
    """Utility class for handling help functionality across the application."""

    @staticmethod
    def show_help_for_module():
        """Handle help button click by opening contextual help URL based on active module or page.

        Args:
            active_module: The currently active module dict from moduleManager.getActiveModule()
        """
        module_name = ModuleManager().getActiveModuleName()
        if module_name and module_name == Module.HOME.value:
            help_url = "https://help.kavitro.com/et/collections/10606065-kavitro-qgis-plugin"
            loadWebpage.open_webpage(help_url)
            return

        if module_name:
            help_url = HELP_URLS.get(module_name, DEFAULT_HELP_URL)
            loadWebpage.open_webpage(help_url)
            return

        loadWebpage.open_webpage(DEFAULT_HELP_URL)