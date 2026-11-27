"""Qt event accessors that differ between Qt5 and Qt6."""
from qgis.PyQt.QtCore import QPoint


def global_pos(event) -> QPoint:
    """Screen position of a mouse or enter event: Qt6 has no ``globalPos()`` on them."""
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()
