from PyQt5.QtWidgets import QWidget

from .ui.mixins.token_mixin import TokenMixin


class BaseModule(TokenMixin):
    def __init__(self, name, display_name, icon, lang_manager, theme_manager):
        TokenMixin.__init__(self)
        self.name = name
        self.display_name = display_name
        self.icon = icon
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.widget = QWidget()

    def activate(self):
        """Activate the module and return the current activation token."""
        return self.mark_activated(self._active_token)

    def deactivate(self):
        """Deactivate the module."""
        self.mark_deactivated(bump_token=True)
        return None

    def run(self):
        """Run the module's main logic."""
        pass

    def reset(self):
        """Reset the module's state."""
        pass

    def is_token_active(self, token: int) -> bool:
        """Check whether a token matches the current active token and module is active."""
        return super().is_token_active(token)

    def get_widget(self):
        """Return the module's main QWidget."""
        return self.widget
