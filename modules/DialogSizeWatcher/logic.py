
from ...BaseModule import BaseModule
from .ui import DialogSizeWatcherUI
from ...utils.dialog_geometry_watcher import DialogGeometryWatcher

class DialogSizeWatcherModule(BaseModule):
    def __init__(self, name, display_name, icon, lang_manager, theme_manager):
        super().__init__(name, display_name, icon, lang_manager, theme_manager)
        self.widget = DialogSizeWatcherUI(lang_manager, theme_manager)
        self._dialog = None
        self._unsubscribe = None

    def activate(self):
        from wild_code.dialog import PluginDialog
        self._dialog = PluginDialog.get_instance()
        print("[DialogSizeWatcher] activate called", self._dialog)
        if self._dialog is not None and hasattr(self._dialog, 'subscribe_geometry_updates'):
            self._unsubscribe = self._dialog.subscribe_geometry_updates(self.widget.update_size)

    def deactivate(self):
        print("[DialogSizeWatcher] deactivate called")
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None
        self._dialog = None

    def run(self):
        pass

    def reset(self):
        self.widget.update_size("", "", "", "")

    def get_widget(self):
        return self.widget
