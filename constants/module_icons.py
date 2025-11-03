import os
from .base_paths import PLUGIN_ROOT, RESOURCE, ICON_FOLDER
from .module_names import (
    SETTINGS_MODULE,
    PROJECTS_MODULE,
    CONTRACT_MODULE,
    PROPERTY_MODULE,
)
from ..widgets.theme_manager import ThemeManager
from ..utils.url_manager import Module
from ..utils.logger import debug as log_debug, is_debug as is_global_debug

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

class DateIcons:
    ICON_DATE_OVERDUE = "icons8-schedule-overdue.png"
    ICON_DATE_SOON = "icons8-schedule-soon.png"
    ICON_DATE_CREATED_AT = "icons8-date-created_at.png"
    ICON_DATE_LAST_MODIFIED = "icons8-last_update-.png"

class MiscIcons:
    ICON_IS_PRIVATE = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER,  "icons8-key-isprivate.png")

class ModuleIconPaths:
    MODULE_ICONS = {
        # Core (keep existing module icon mappings; do not change yet)
        SETTINGS_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, ModuleIcons.ICON_SETTINGS),
        PROJECTS_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, ModuleIcons.ICON_PROJECTS),
        CONTRACT_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, ModuleIcons.ICON_CONTRACT),
        Module.HOME: os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, ModuleIcons.ICON_HOME),
        PROPERTY_MODULE: os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, ModuleIcons.ICON_PROPERTY),
    }

    # Simple in-memory cache to avoid repeated filesystem checks during startup
    _ICON_CACHE = {}

    @staticmethod
    def themed(icon_basename: str) -> str:
        """Resolve a themed icon absolute path from a basename using ThemeManager."""
        try:

            return ThemeManager.get_icon_path(icon_basename)
        except Exception:
            # Fallback to base icons folder
            return os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER, icon_basename)

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
            from ..widgets.theme_manager import ThemeManager  # type: ignore
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
        if theme == 'dark':
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
        # Avoid noisy prints; use debug logger if enabled
        if is_global_debug():
            log_debug(f"Resolving icon for module: {module_name}")

        # Try cache first
        cached = ModuleIconPaths._ICON_CACHE.get(module_name, None)
        if cached is not None:
            return cached

        path = ModuleIconPaths.MODULE_ICONS.get(module_name, None)
        resolved = ModuleIconPaths._resolve_themed_icon(path)
        # Cache even None results to avoid repeated lookups for unknown keys
        ModuleIconPaths._ICON_CACHE[module_name] = resolved
        return resolved
