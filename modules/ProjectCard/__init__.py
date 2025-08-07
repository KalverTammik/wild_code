# Each module should provide this function in its __init__.py
def get_module_metadata():
    from .ProjectCardUI import ProjectCardUI
    return ProjectCardUI()  # Return a ProjectCardUI instance for registration
