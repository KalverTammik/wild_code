class SettingsLogic:
    def __init__(self):
        self.settings = {}

    def set_setting(self, key, value):
        self.settings[key] = value

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def get_all_settings(self):
        return self.settings.copy()
