# Each module should provide this function in its __init__.py
# Example for modules/projects/__init__.py

def get_module_metadata():
    from .ProjectsModule import ProjectsModule
    return ProjectsModule()  # Return a ProjectsModule instance for registration
