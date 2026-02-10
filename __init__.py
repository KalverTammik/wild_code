# Kavitro package initializer

from .main import WildCodePlugin

def classFactory(iface):
    """QGIS calls this to instantiate the plugin."""
    return WildCodePlugin(iface)
