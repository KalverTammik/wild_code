import os
from .base_paths import PLUGIN_ROOT, RESOURCE, ICON_FOLDER
from ..widgets.theme_manager import is_dark
from ..utils.url_manager import Module


RANDOM_ICON_NAME = "Valisee_s.png"
VALISEE_V_ICON_NAME = "Valisee_v.png"

ICON_LOGIN = "icons8-login-50.png"
ICON_LOGOUT = "icons8-logout-rounded-left-50.png"
ICON_HELP = "icons8-help-50.png"
ICON_INFO = "icons8-info-50.png"
ICON_FLOW = "icons8-flow-50.png"
ICON_HIERARCHY = "icons8-hierarchy-50.png"
ICON_WRENCH = "icons8-wrench-50.png"
ICON_TASKS = "icons8-tasks-50.png"
ICON_TABLE_GRAPH = "icons8-table-and-graph-50.png"
ICON_CHECK = "icons8-double-tick-50.png"
ICON_ERROR = "icons8-error-50.png"
ICON_WARNING = "icons8-notification-50.png"
ICON_CLEAR = "icons8-clear-search-50.png"
ICON_ADD = "icons8-add-50.png"
ICON_REMOVE = "icons8-remove-50.png"
ICON_WAIT = "icons8-wait-50.png"
ICON_BUFFERING = "icons8-buffering-50.png"

#Module icons 
class ModuleIcons:
    ICON_CONTRACT = "handshake.png"
    ICON_HOME = "home-icon-silhouette.png"
    ICON_SETTINGS = "repairing-service.png"
    ICON_PROJECTS = "team-management2.png"
    ICON_PROPERTY = "menu.png"
    ICON_SIGNAL_TEST = ICON_FLOW
    

class DateIcons:
    ICON_DATE_OVERDUE = "icons8-schedule-overdue.png"
    ICON_DATE_SOON = "icons8-schedule-soon.png"
    ICON_DATE_CREATED_AT = "icons8-date-created_at.png"
    ICON_DATE_LAST_MODIFIED = "icons8-last_update-.png"

class MiscIcons:
    ICON_IS_PRIVATE = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER,  "icons8-key-security-50.png")
    ICON_IS_CLIENT = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER,  "icons8-client-50.png")

class ModuleIconPaths:

    ROOT_ICONS = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER)

    MODULE_ICONS = {
        # Core (keep existing module icon mappings; do not change yet)
        Module.SETTINGS.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_SETTINGS),
        Module.HOME.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_HOME),
        Module.PROJECT.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_PROJECTS),
        Module.CONTRACT.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_CONTRACT),
        Module.PROPERTY.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_PROPERTY),
        Module.SIGNALTEST.name: os.path.join(ROOT_ICONS, ModuleIcons.ICON_SIGNAL_TEST),
    }


    @staticmethod
    def _resolve_themed_icon(path: str) -> str:
        """Return theme-specific icon path if available for a given mapped path.
        Tries resources/icons/Dark|Light/<name>.png then .svg, then falls back to base icons folder
        using the same order, finally returns the provided path.
        """
        if not path:
            return None
        try:
            # Defer import to avoid cyclical imports
            from ..widgets.theme_manager import ThemeManager 
            theme = ThemeManager.load_theme_setting() if hasattr(ThemeManager, 'load_theme_setting') else 'light'
        except Exception:
            theme = 'light'

        base_icons_dir = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER)
        base_name = os.path.basename(path)
        stem, ext = os.path.splitext(base_name)

        # Build candidate basenames, prioritize provided extension then the alternative
        exts = []
        if ext:
            exts.append(ext)
        # Ensure we try both .png and .svg
        if '.png' not in exts:
            exts.append('.png')
        if '.svg' not in exts:
            exts.append('.svg')

        themed_dirs = []
        if is_dark(theme):
            themed_dirs += [os.path.join(base_icons_dir, 'Dark'), os.path.join(base_icons_dir, 'dark')]
        else:
            themed_dirs += [os.path.join(base_icons_dir, 'Light'), os.path.join(base_icons_dir, 'light')]

        # Search themed dirs
        for d in themed_dirs:
            for e in exts:
                themed_path = os.path.join(d, f"{stem}{e}")
                if os.path.exists(themed_path):
                    return themed_path

        # Fallback: base icons dir
        for e in exts:
            candidate = os.path.join(base_icons_dir, f"{stem}{e}")
            if os.path.exists(candidate):
                return candidate

        # Final fallback to original mapping path
        return path

    @staticmethod
    def get_module_icon(module_name):
        # Try cache first — avoid doing any work or logging when we already have a value
        # Only log when we're actually performing resolution (not on every call)
        path = ModuleIconPaths.MODULE_ICONS.get(module_name, None)
        resolved = ModuleIconPaths._resolve_themed_icon(path)
        return resolved
