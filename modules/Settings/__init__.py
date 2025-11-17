# Each module should provide this function in its __init__.py
# Example for modules/Settings/__init__.py

def get_module_metadata():
    from .SettingsUI import SettingsModule
    return SettingsModule()  # Return a SettingsUI instance for registration
