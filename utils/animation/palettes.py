from PyQt5.QtGui import QColor
from wild_code.widgets.theme_manager import ThemeManager, Theme, is_dark


def get_dev_halo_palette():
    try:
        theme = ThemeManager.effective_theme()
    except Exception:
        theme = 'light'
    if is_dark(theme):
        return QColor(255, 120, 0, 80), QColor(255, 0, 120, 200), QColor(255, 120, 0, 80)
    return QColor(255, 120, 0, 100), QColor(255, 0, 120, 235), QColor(255, 120, 0, 100)


def get_frames_halo_palette():
    try:
        theme = ThemeManager.effective_theme()
    except Exception:
        theme = 'light'
    if is_dark(theme):
        return QColor(0, 210, 255, 80), QColor(0, 255, 180, 200), QColor(0, 210, 255, 80)
    return QColor(0, 210, 255, 100), QColor(0, 255, 180, 235), QColor(0, 210, 255, 100)
