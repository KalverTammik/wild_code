"""One background request at a time; only the latest request may update the UI."""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .workers import FunctionWorker, start_worker


class LatestRequest(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._revision = 0
        self._running_revision = None
        self._pending = None
        self._worker = None

    @property
    def busy(self):
        return self._running_revision is not None

    def invalidate(self):
        self._revision += 1
        self._pending = None
        if self._worker is not None:
            self._worker.cancel()

    def submit(self, function, *args):
        self.invalidate()
        self._pending = (self._revision, function, args)
        self._start_pending()

    def _start_pending(self):
        if self.busy or self._pending is None:
            return
        revision, function, args = self._pending
        self._pending = None
        self._running_revision = revision
        self._worker = FunctionWorker(function, *args)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        start_worker(self._worker)

    @pyqtSlot(object)
    def _on_finished(self, result):
        current = self._running_revision == self._revision
        self._running_revision = None
        self._worker = None
        if current:
            self.finished.emit(result)
        self._start_pending()

    @pyqtSlot(str)
    def _on_error(self, message):
        current = self._running_revision == self._revision
        self._running_revision = None
        self._worker = None
        if current:
            self.error.emit(message)
        self._start_pending()
