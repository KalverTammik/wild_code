# ==== BEGIN ThemeManager v2 ====
from functools import lru_cache
from typing import Any, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from qgis.core import QgsSettings
import os
from PyQt5.QtGui import QColor
from enum import Enum
from ..constants.file_paths import StylePaths, QssPaths
from ..constants.module_icons import IconNames, ModuleIconPaths

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

    _retheme_engine = None

    # Centralized bundles (keep parity between light/dark; order matters)
    APP_BUNDLE = (
        QssPaths.MAIN,
        QssPaths.BUTTONS,
        QssPaths.COMBOBOX,
        QssPaths.SIDEBAR,
        QssPaths.HEADER,
        QssPaths.FOOTER,
        QssPaths.MODULE_INFO,
    )

    MODULE_BUNDLE = APP_BUNDLE + (
        QssPaths.MODULE_TOOLBAR,
        QssPaths.MODULE_CARD,
        QssPaths.SETUP_CARD,
        QssPaths.PILLS,
        QssPaths.POPUP,
        QssPaths.TOOLTIP,
        QssPaths.LAYER_TREE_PICKER,
        QssPaths.SEARCH_RESULTS_WIDGET,
        QssPaths.PROGRESS_DIALOG,
        QssPaths.PROPERTIES_UI,
        QssPaths.DATES,
    )

    LOGIN_BUNDLE = (
        QssPaths.MAIN,
        QssPaths.BUTTONS,
        QssPaths.LOGIN,
    )

    @staticmethod
    def _merge_bundle(base: tuple, extra: list[str] | None = None) -> tuple:
        merged = list(base)
        if extra:
            merged.extend(extra)
        # Preserve order while deduping
        seen = set()
        unique = []
        for item in merged:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return tuple(unique)

    @staticmethod
    def app_bundle(extra: list[str] | None = None) -> tuple:
        return ThemeManager._merge_bundle(ThemeManager.APP_BUNDLE, extra)

    @staticmethod
    def module_bundle(extra: list[str] | None = None) -> tuple:
        return ThemeManager._merge_bundle(ThemeManager.MODULE_BUNDLE, extra)

    @staticmethod
    def login_bundle(extra: list[str] | None = None) -> tuple:
        return ThemeManager._merge_bundle(ThemeManager.LOGIN_BUNDLE, extra)

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
    def get_qicon(icon_name: str) -> QIcon:
        #print(f"Requested icon name: {icon_name}")
        i = IconNames.get_icon(icon_name)
        #print(f"[ThemeManager.get_qicon] resolved icon path: {i}")
        return QIcon(i)

    @staticmethod
    def set_initial_theme(widget, switch_button=None, logout_button=None, qss_files=None) -> str:
        theme = ThemeManager.effective_theme()
        ThemeManager._apply_theme_for(widget, theme, qss_files or ThemeManager.app_bundle())
        ThemeManager._update_header_icons(theme, switch_button, logout_button)
        return theme

    @staticmethod
    def toggle_theme(widget, current_theme, switch_button=None, logout_button=None, qss_files=None) -> str:
        theme_now = current_theme or ThemeManager.effective_theme()
        new_theme = Theme.DARK if theme_now == Theme.LIGHT else Theme.LIGHT
        ThemeManager._apply_theme_for(widget, new_theme, qss_files or ThemeManager.app_bundle())
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
                IconNames.LIGHTNESS_ICON if is_dark(theme) else IconNames.DARKNESS_ICON
            ))
            switch_button.setText("")
        if logout_button is not None:
            logout_button.setIcon(ThemeManager.get_qicon(IconNames.ICON_LOGOUT
            ))

    @staticmethod
    def get_retheme_engine():
        if ThemeManager._retheme_engine is None:
            ThemeManager._retheme_engine = RethemeEngine()
        return ThemeManager._retheme_engine

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
            qss_files = ThemeManager.app_bundle()
        qss_tuple = tuple(qss_files)
        try:
            css = ThemeManager._read_qss(theme_dir, qss_tuple)
            widget.setStyleSheet(css)
        except Exception:
            pass

    @staticmethod
    def apply_module_style(widget, qss_files=None):
        theme = ThemeManager.effective_theme()
        theme_dir = StylePaths.DARK if is_dark(theme) else StylePaths.LIGHT
        bundle = ThemeManager.module_bundle(qss_files)
        ThemeManager.apply_theme(widget, theme_dir, bundle)
# ==== END ThemeManager v2 ====


class RethemeEngine:
    """Central registry-based retheme engine; no per-widget retheme methods required."""

    def __init__(self):
        self._registrations: list[dict[str, Any]] = []

    def register(self, widget: Any, *, qss_files: Any = None, after_apply: Callable | None = None):
        if widget is None:
            return
        # Update if already present
        for reg in self._registrations:
            if reg.get("widget") is widget:
                reg["qss_files"] = qss_files
                reg["after_apply"] = after_apply
                return
        self._registrations.append({"widget": widget, "qss_files": qss_files, "after_apply": after_apply})

    def retheme_all(self):
        theme = ThemeManager.effective_theme()
        theme_dir = StylePaths.DARK if is_dark(theme) else StylePaths.LIGHT
        for reg in list(self._registrations):
            widget = reg.get("widget")
            if widget is None:
                continue
            qss_files = reg.get("qss_files") or ThemeManager.app_bundle()
            ThemeManager.apply_theme(widget, theme_dir, qss_files)
            after = reg.get("after_apply")
            if callable(after):
                try:
                    after(widget, theme)
                except Exception:
                    pass

# ==== BEGIN styleExtras fix ====
# ==== styleExtras (color variables, theme-aware) ====
class styleExtras:

    @staticmethod
    def apply_chip_shadow(element, *, color='standard', blur_radius=15, x_offset=0, y_offset=2, alpha_level='medium'):
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