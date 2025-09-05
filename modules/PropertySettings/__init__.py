# PropertySettings module initialization
# Provides property data management functionality for users with update permissions

def get_module_metadata():
    from .PropertySettingsUI import PropertySettingsUI
    return PropertySettingsUI()  # Return a PropertySettingsUI instance for registration
