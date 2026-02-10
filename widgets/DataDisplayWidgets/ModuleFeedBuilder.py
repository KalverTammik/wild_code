from ...ui.module_card_factory import ModuleCardFactory

"""ModuleFeedBuilder

Responsibility: build card widgets only.
Insertion, theming, counter updates handled elsewhere (e.g., ModuleBaseUI).
"""


# ================== Module Feed ==================
class ModuleFeedBuilder:

    @staticmethod
    def create_item_card(item, module_name=None, lang_manager=None):
        return ModuleCardFactory.create_item_card(
            item,
            module_name=module_name,
            lang_manager=lang_manager,
        )
