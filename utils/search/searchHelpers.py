
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
            SearchHeplpers._show_in_signal_tester(dialog, module, item_id, title)
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

        SearchHeplpers._show_in_signal_tester(dialog, module, item_id, title)

    @staticmethod
    def _show_in_signal_tester(dialog, module: str, item_id: str, title: str) -> None:
        """Switch to SignalTestModule and display the clicked search payload."""
        from ...utils.url_manager import Module
        from ..moduleSwitchHelper import ModuleSwitchHelper

        if dialog is None:
            return

        ModuleSwitchHelper.switch_module(Module.SIGNALTEST.name, dialog=dialog)
        mgr = getattr(dialog, "moduleManager", None)
        instance = mgr.getActiveModuleInstance(Module.SIGNALTEST.name) if mgr else None
        if instance and hasattr(instance, "show_external_signal_payload"):
            instance.show_external_signal_payload(
                source="header_search_result",
                module=module,
                item_id=item_id,
                title=title,
            )