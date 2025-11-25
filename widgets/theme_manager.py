# ==== BEGIN ThemeManager v2 ====
from functools import lru_cache
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from qgis.core import QgsSettings
import os
from PyQt5.QtGui import QColor
from enum import Enum
from ..constants.file_paths import ResourcePaths, StylePaths, QssPaths
from ..constants.base_paths import PLUGIN_ROOT, RESOURCE, ICON_FOLDER

settings = QgsSettings()

class Theme(str):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "standard"  # optional

def is_dark(value: str) -> bool:
    return value == Theme.DARK

class ThemeManager(QObject):
    # Emits Theme.LIGHT or Theme.DARK (effective mode)
    themeChanged = pyqtSignal(str)

    # Semantic icon basenames (keep yours; truncated here for brevity)
    ICON_SETTINGS_GEAR = "icons8-gear-100.png"
    ICON_LIST = "icons8-list-50.png"
    ICON_SEARCH = "icons8-search-location-50.png"
    ICON_SAVE = "icons8-save-50.png"
    ICON_TREE = "icons8-tree-structure-50.png"
    ICON_USER = "icons8-username-50.png"
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
    ICON_FOLDER = "icons8-folder-50.png"
    ICON_ADD = "icons8-add-50.png"
    ICON_REMOVE = "icons8-remove-50.png"
    ICON_WAIT = "icons8-wait-50.png"
    ICON_BUFFERING = "icons8-buffering-50.png"
    VALISEE_V_ICON_NAME = "Valisee_v.png"

    @staticmethod
    def save_theme_setting(theme_name: str):
        settings.setValue("wild_code/theme", theme_name)

    @staticmethod
    def load_theme_setting() -> str:
        return settings.value("wild_code/theme", Theme.LIGHT)

    @staticmethod
    def effective_theme() -> str:
        theme = ThemeManager.load_theme_setting()
        if theme == Theme.SYSTEM:
            from PyQt5.QtWidgets import QApplication
            pal = QApplication.instance().palette()
            return Theme.DARK if pal.base().color().value() < 128 else Theme.LIGHT
        return theme

    @staticmethod
    @lru_cache(maxsize=256)
    def resolve_icon_path(icon_name_or_path: str) -> str:
        if not icon_name_or_path:
            return None
        theme = ThemeManager.effective_theme()
        base_icons_dir = os.path.join(PLUGIN_ROOT, RESOURCE, ICON_FOLDER)

        if os.path.isabs(icon_name_or_path):
            basename = os.path.basename(icon_name_or_path)
            fallback = icon_name_or_path
        else:
            basename = icon_name_or_path
            fallback = os.path.join(base_icons_dir, basename)

        stem, ext = os.path.splitext(basename)
        exts = [ext] if ext else []
        if '.png' not in exts: exts.append('.png')
        if '.svg' not in exts: exts.append('.svg')

        theme_dir_name = os.path.basename(StylePaths.DARK) if is_dark(theme) else os.path.basename(StylePaths.LIGHT)
        themed_dir = os.path.join(base_icons_dir, theme_dir_name)
        for e in exts:
            p = os.path.join(themed_dir, f"{stem}{e}")
            if os.path.exists(p):
                return p

        for e in exts:
            p = os.path.join(base_icons_dir, f"{stem}{e}")
            if os.path.exists(p):
                return p
        return fallback

    @staticmethod
    def get_qicon(icon_name_or_path: str) -> QIcon:
        p = ThemeManager.resolve_icon_path(icon_name_or_path)
        return QIcon(p) if p else QIcon()

    @staticmethod
    def set_initial_theme(widget, switch_button, logout_button, qss_files=None) -> str:
        theme = ThemeManager.effective_theme()
        ThemeManager._apply_theme_for(widget, theme, qss_files)
        ThemeManager._update_header_icons(theme, switch_button, logout_button)
        return theme

    @staticmethod
    def toggle_theme(widget, current_theme, switch_button, logout_button, qss_files=None) -> str:
        theme_now = current_theme or ThemeManager.effective_theme()
        new_theme = Theme.DARK if theme_now == Theme.LIGHT else Theme.LIGHT
        ThemeManager._apply_theme_for(widget, new_theme, qss_files)
        ThemeManager._update_header_icons(new_theme, switch_button, logout_button)
        ThemeManager.save_theme_setting(new_theme)
        # Emit change for listeners
        try:
            # if a shared instance exists in your app, emit on that; otherwise this is a static utility
            # you can wire a shared instance in your app bootstrap and pass it around
            pass
        finally:
            return new_theme

    @staticmethod
    def _apply_theme_for(widget, theme: str, qss_files=None):
        theme_dir = StylePaths.DARK if is_dark(theme) else StylePaths.LIGHT
        ThemeManager.apply_theme(widget, theme_dir, qss_files)

    @staticmethod
    def _update_header_icons(theme: str, switch_button, logout_button):
        if switch_button is not None:
            switch_button.setIcon(ThemeManager.get_qicon(
                ResourcePaths.LIGHTNESS_ICON if is_dark(theme) else ResourcePaths.DARKNESS_ICON
            ))
            switch_button.setText("")
        if logout_button is not None:
            logout_button.setIcon(ThemeManager.get_qicon(
                ResourcePaths.LOGOUT_BRIGHT if is_dark(theme) else ResourcePaths.LOGOUT_DARK
            ))

    @staticmethod
    @lru_cache(maxsize=64)
    def _read_qss(theme_dir: str, qss_files_tuple: tuple) -> str:
        css = ""
        for qss_file in qss_files_tuple:
            qss_path = os.path.join(theme_dir, qss_file)
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as fh:
                    css += fh.read() + "\n"
        return css

    @staticmethod
    def apply_theme(widget, theme_dir, qss_files=None):
        if widget is None:
            return
        if not qss_files:
            qss_files = [QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.SIDEBAR]
        qss_tuple = tuple(qss_files)
        try:
            css = ThemeManager._read_qss(theme_dir, qss_tuple)
            widget.setStyleSheet(css)
        except Exception:
            pass

    @staticmethod
    def apply_module_style(widget, qss_files):
        theme = ThemeManager.effective_theme()
        theme_dir = StylePaths.DARK if is_dark(theme) else StylePaths.LIGHT
        ThemeManager.apply_theme(widget, theme_dir, qss_files)
# ==== END ThemeManager v2 ====

# ==== BEGIN styleExtras fix ====
# ==== styleExtras (color variables, theme-aware) ====
class styleExtras:

    @staticmethod
    def apply_chip_shadow(element, *, color='standard', blur_radius=20, x_offset=0, y_offset=2, alpha_level='medium'):
        """Apply a theme-aware shadow/glow to any QWidget with standardized alpha levels.

        Args:
            element: The QWidget to apply shadow to
            color: Shadow color theme - 'standard', 'red', 'green', 'gray', 'blue', 'accent' (default: 'standard')
            blur_radius: Shadow blur radius (default: 20)
            x_offset: Horizontal shadow offset (default: 0)
            y_offset: Vertical shadow offset (default: 2)
            alpha_level: Shadow intensity - 'low', 'medium', 'high', 'extra_high' (default: 'medium')
        """
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        # Get standardized alpha value
        alpha_values = {
            IntensityLevels.LOW: AlphaLevel.LOW,
            IntensityLevels.MEDIUM: AlphaLevel.MEDIUM,
            IntensityLevels.HIGH: AlphaLevel.HIGH,
            IntensityLevels.EXTRA_HIGH: AlphaLevel.EXTRA_HIGH
        }
        alpha = alpha_values.get(alpha_level, AlphaLevel.MEDIUM)

        col = ShadowIntensityEngine._resolve_shadow_color(color=color, alpha=alpha)
        eff = QGraphicsDropShadowEffect(element)
        eff.setBlurRadius(blur_radius)
        eff.setXOffset(x_offset)
        eff.setYOffset(y_offset)
        eff.setColor(col)
        element.setGraphicsEffect(eff)





class ThemeShadowColors(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    STANDARD = "standard"
    GRAY = "gray"
    ACCENT = "accent"

class AlphaLevel(int, Enum):
    LOW        = 60
    MEDIUM     = 90
    HIGH       = 128
    EXTRA_HIGH = 150



class IntensityLevels(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    EXTRA_HIGH = 'extra_high'

class ShadowIntensityEngine:
    @staticmethod
    def _resolve_shadow_color(color=ThemeShadowColors.STANDARD, alpha: int = None):
        """Return a QColor for the requested color variable, adjusted for current theme.
        - color: str name ('standard','red','green','gray','blue','accent', '#RRGGBB') or QColor
        - alpha: optional 0..255 override
        """

        theme = ThemeManager.effective_theme()
        mode = Theme.DARK if is_dark(theme) else Theme.LIGHT

        # If already a QColor, optionally override alpha and return
        if isinstance(color, QColor):
            if alpha is not None:
                c = QColor(color)
                c.setAlpha(alpha)
                return c
            return color

        # If a hex color string, parse directly
        if isinstance(color, str) and color.strip().startswith('#'):
            c = QColor(color.strip())
            if alpha is not None:
                c.setAlpha(alpha)
            return c

        # Theme-aware named palette (consistent with main.qss color scheme)
        palette = {
            ThemeShadowColors.STANDARD: {
                Theme.DARK:  QColor(255, 255, 255,  alpha),  # light glow on dark
                Theme.LIGHT: QColor(9, 144, 143,  alpha),  # dark shadow on light
            },
            ThemeShadowColors.RED: {
                Theme.DARK:  QColor(255, 100, 100, alpha),
                Theme.LIGHT: QColor(139,   0,   0, alpha),
            },
            ThemeShadowColors.GREEN: {
                Theme.DARK:  QColor(100, 255, 100, alpha),
                Theme.LIGHT: QColor(  0, 100,   0, alpha),
            },
            ThemeShadowColors.GRAY: {
                Theme.DARK:  QColor(150, 150, 150, alpha),
                Theme.LIGHT: QColor(80, 80, 80, alpha),
            },

            ThemeShadowColors.BLUE: {
                Theme.DARK:  QColor(100, 100, 255, alpha),
                Theme.LIGHT: QColor(  9, 132, 227, alpha),
            },

            ThemeShadowColors.ACCENT: {
                Theme.DARK:  QColor(  0, 120, 212, alpha),  
                Theme.LIGHT: QColor(  0, 120, 212, alpha),
            },
        }



        base = palette.get(color, palette[ThemeShadowColors.STANDARD])[mode]
        if alpha is not None:
            c = QColor(base)
            c.setAlpha(alpha)
            return c
        return base