from ...module_manager import ModuleManager
from ...widgets.theme_manager import ThemeManager
from ...Logs.switch_logger import SwitchLogger
from .cards.SettingsModuleCard import SettingsModuleCard


class SettingsCardFactory:
    @staticmethod
    def create_module_card(*, lang_manager, module_name: str, logic, on_pending_changed):
        translated = lang_manager.translate_module_name(module_name)

        module_manager = ModuleManager()
        supports = module_manager.getModuleSupports(module_name) or (False, False, False, False)
        supports_types, supports_statuses, supports_tags, supports_archive_layer = supports
        module_labels = list(module_manager.getModuleLabels(module_name) or [])

        card = SettingsModuleCard(
            lang_manager,
            module_name,
            translated,
            supports_types,
            supports_statuses,
            supports_tags,
            supports_archive_layer,
            module_labels=module_labels,
            logic=logic,
        )

        card.setObjectName("SetupCard")
        card.setProperty("cardTone", module_name.lower())
        try:
            style = card.style()
            if style is not None:
                style.unpolish(card)
                style.polish(card)
            card.update()
            SwitchLogger.log(
                "settings_card_theme_ready",
                module=module_name.lower(),
                extra={
                    "tone": str(card.property("cardTone") or ""),
                    "theme": ThemeManager.effective_theme(),
                    "stylesheet_len": len(card.styleSheet() or ""),
                },
            )
        except Exception:
            pass
        card.pendingChanged.connect(on_pending_changed)
        return card
