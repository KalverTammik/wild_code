# Each module should provide this function in its __init__.py
# Example for modules/ProjectFeed/__init__.py

def get_module_metadata():
    from .ProjectFeedUI import ProjectFeedUI
    return ProjectFeedUI()  # Return a ProjectFeedUI instance for registration
