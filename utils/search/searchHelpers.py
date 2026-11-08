from ..messagesHelper import ModernMessageDialog
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
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
            lang = LanguageManager()
            ModernMessageDialog.show_info(
                lang.translate(TranslationKeys.SEARCH_OPEN_NOT_AVAILABLE_TITLE),
                lang.translate(TranslationKeys.SEARCH_OPEN_NOT_AVAILABLE_MESSAGE),
            )
            return

        target_name = target_enum.name
        ModuleSwitchHelper.switch_module(target_name, dialog=dialog)

        instance = dialog.moduleManager.getActiveModuleInstance(target_name)
        if instance is None:
            return

        instance.open_item_from_search(module, item_id, title)


class SearchUIController:
    @staticmethod
    def handle_search_result(dialog, module: str, item_id: str, title: str) -> None:
        SearchHeplpers._on_search_result_clicked(dialog, module, item_id, title)

