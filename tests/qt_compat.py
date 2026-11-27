"""Small Qt5 / Qt6 differences that only the tests meet."""
from qgis.PyQt.QtGui import QFontDatabase


def font_families() -> list:
    """Installed font families: ``families()`` is static in Qt6 and needs an instance in Qt5."""
    try:
        return QFontDatabase.families()
    except TypeError:
        return QFontDatabase().families()
