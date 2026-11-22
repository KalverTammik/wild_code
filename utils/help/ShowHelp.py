from ...constants.help_urls import DEFAULT_HELP_URL, HELP_URLS
from ...utils.url_manager import loadWebpage
from ...constants.module_names import Module


class ShowHelp:
    """Utility class for handling help functionality across the application."""

    @staticmethod
    def show_help_for_module(module_name: str | None) -> None:
        """Open the help page of `module_name` (the active module), or the general help page.

        Args:
            module_name: Active module name from ModuleManager.getActiveModuleName(), or None.
        """
        if module_name and module_name == Module.HOME.value:
            help_url = "https://help.kavitro.com/et/collections/10606065-kavitro-qgis-plugin"
            loadWebpage.open_webpage(help_url)
            return

        if module_name:
            help_url = HELP_URLS.get(module_name, DEFAULT_HELP_URL)
            loadWebpage.open_webpage(help_url)
            return

        loadWebpage.open_webpage(DEFAULT_HELP_URL)