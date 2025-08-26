import importlib
import os
import sys
from ..module_manager import ModuleManager
from ..constants.module_names import *

MODULES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules'))

def discover_modules():
    """
    Discover all modules in the modules/ directory that have an __init__.py file.
    Returns a list of (module_name, import_path) tuples.
    """
    modules = []
    for entry in os.scandir(MODULES_PATH):
        if entry.is_dir():
            init_file = os.path.join(entry.path, '__init__.py')
            if os.path.isfile(init_file):
                modules.append((entry.name, f'wild_code.modules.{entry.name}'))
    return modules

def register_all_modules(module_manager):
    """
    Dynamically import and register all modules at startup (metadata only, not instantiation).
    """
    for module_name, import_path in discover_modules():
        try:
            mod = importlib.import_module(import_path)
            if hasattr(mod, 'get_module_metadata'):
                module_info = mod.get_module_metadata()
                module_manager.registerModule(module_info)
        except Exception as e:
            try:
                from ..utils.logger import debug as log_debug
                log_debug(f"Failed to register module {module_name}: {e}")
            except Exception:
                pass
