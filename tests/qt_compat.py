"""Small Qt5 / Qt6 differences that only the tests meet."""
import unittest

from qgis.PyQt.QtCore import QT_VERSION
from qgis.PyQt.QtGui import QFontDatabase

# A known QGIS 4 difference that port stage 4 settles; the mark goes away with it.
qt6_stage4 = unittest.skipIf(QT_VERSION >= 0x060000, "QGIS 4 port stage 4: differs on Qt6")


def font_families() -> list:
    """Installed font families: ``families()`` is static in Qt6 and needs an instance in Qt5."""
    try:
        return QFontDatabase.families()
    except TypeError:
        return QFontDatabase().families()
