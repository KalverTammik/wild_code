from PyQt5.QtGui import QColor
from wild_code.widgets.theme_manager import ThemeManager


def get_dev_halo_palette():
    try:
        theme = ThemeManager.load_theme_setting()
    except Exception:
        theme = 'light'
    if theme == 'dark':
        return QColor(255, 120, 0, 80), QColor(255, 0, 120, 200), QColor(255, 120, 0, 80)
    return QColor(255, 120, 0, 100), QColor(255, 0, 120, 235), QColor(255, 120, 0, 100)


def get_frames_halo_palette():
    try:
        theme = ThemeManager.load_theme_setting()
    except Exception:
        theme = 'light'
    if theme == 'dark':
        return QColor(0, 210, 255, 80), QColor(0, 255, 180, 200), QColor(0, 210, 255, 80)
    return QColor(0, 210, 255, 100), QColor(0, 255, 180, 235), QColor(0, 210, 255, 100)
