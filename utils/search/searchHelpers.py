from ..messagesHelper import ModernMessageDialog
class SearchHeplpers:
    @staticmethod
    def _on_search_result_clicked(dialog, module: str, item_id: str, title: str) -> None:
        """Handle a search result click coming from HeaderWidget using the provided dialog."""
        from ...utils.url_manager import Module
        from ..moduleSwitchHelper import ModuleSwitchHelper

        if dialog is None:
            return

        MODULE_SEARCH_TO_ENUM = {
            "PROJECTS": Module.PROJECT,
            "CONTRACTS": Module.CONTRACT,
            "PROPERTIES": Module.PROPERTY,
            "COORDINATIONS": Module.COORDINATION,
        }

        target_enum = MODULE_SEARCH_TO_ENUM.get(module.upper())
        if target_enum is None:
            ModernMessageDialog.show_info(
                "Not available",
                "This module cannot be opened from search yet.",
            )
            return

        target_name = target_enum.name
        ModuleSwitchHelper.switch_module(target_name, dialog=dialog)

        instance = getattr(dialog, "moduleManager", None)
        instance = instance.getActiveModuleInstance(target_name) if instance else None
        if instance is None:
            return

        if hasattr(instance, "open_item_from_search"):
            instance.open_item_from_search(module, item_id, title)
            return

        ModernMessageDialog.show_info(
            "Not available",
            "This module cannot be opened from search yet.",
        )


class SearchUIController:
    @staticmethod
    def handle_search_result(dialog, module: str, item_id: str, title: str) -> None:
        SearchHeplpers._on_search_result_clicked(dialog, module, item_id, title)

