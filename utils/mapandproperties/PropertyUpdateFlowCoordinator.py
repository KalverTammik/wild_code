"""Cancellable background reads for the property location hierarchy and selected scope."""
from threading import Event

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from qgis.core import QgsVectorLayerFeatureSource

from ...python.latest_request import LatestRequest
from ...Logs.python_fail_logger import PythonFailLogger
from .PropertyDataLoader import PropertyDataLoader


class PropertyUpdateFlowCoordinator(QObject):
    loaded = pyqtSignal(str, object)
    failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._request = LatestRequest(self)
        self._request.finished.connect(self._on_loaded)
        self._request.error.connect(self._on_failed)
        self._cancelled = Event()
        self.layer_identity = None
        self._kind = None

    def cancel(self):
        self._cancelled.set()
        self._request.invalidate()

    def load_scope(self, layer, scope, *, include_properties):
        self._submit(layer, 'scope', PropertyDataLoader.read_location_scope, scope, include_properties)

    def _submit(self, layer, kind, function, *args):
        self.cancel()
        self._kind = kind
        self._cancelled = Event()
        try:
            if layer is None or not layer.isValid():
                raise ValueError('The property import layer is missing or invalid')
            self.layer_identity = (layer.id(), layer.source())
            # Snapshot creation belongs on the GUI thread; workers never access the live layer.
            source = QgsVectorLayerFeatureSource(layer)
            self._request.submit(function, source, self._cancelled, *args)
        except Exception as exc:
            self._on_failed(str(exc))

    @pyqtSlot(object)
    def _on_loaded(self, result):
        if result is not None:
            self.loaded.emit(self._kind, result)

    @pyqtSlot(str)
    def _on_failed(self, message):
        PythonFailLogger.log_exception(RuntimeError(message), module='property', event='property_location_load_failed')
        self.failed.emit(message)
