# Each module should provide this function in its __init__.py
# Example for modules/UserTest/__init__.py

def get_module_metadata():
    from .TestUserDataDialog import TestUserDataDialog
    return TestUserDataDialog()  # Return a TestUserDataDialog instance for registration
