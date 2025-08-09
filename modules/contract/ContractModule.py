from ...ui.ModuleBaseUI import ModuleBaseUI
from PyQt5.QtWidgets import QLabel

class ContractModule(ModuleBaseUI):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_contract() to re-apply QSS after a theme change.
    """
    name = "ContractModule"

    def get_widget(self):
        """Return the widget instance for use in module manager or UI stack."""
        return self

    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        # Centralized theming
        if self.theme_manager:
            from ...widgets.theme_manager import ThemeManager
            from ...constants.file_paths import QssPaths
            ThemeManager.apply_module_style(self, [QssPaths.MAIN])
        # Use lang_manager for translated label if available
        label_text = self.lang_manager.translate("Contract module loaded!") if self.lang_manager else "Contract module loaded!"
        self.display_area.layout().addWidget(QLabel(label_text))

    def activate(self):
        """Activate the module."""
        pass

    def retheme_contract(self):
        """
        Re-applies the correct theme and QSS to the contract module, forcing a style refresh.
        """
        from ...widgets.theme_manager import ThemeManager
        from ...constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])

    def deactivate(self):
        """Deactivate the module."""
        pass
