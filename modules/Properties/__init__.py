# Properties module initialization
# Provides property management functionality including SHP file loading

def get_module_metadata():
    from .PropertiesUI import PropertiesUI
    return PropertiesUI()  # Return a PropertiesUI instance for registration
