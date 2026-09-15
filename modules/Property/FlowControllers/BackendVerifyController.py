from __future__ import annotations

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .BackendVerifyWorker import BackendVerifyWorker
from ....Logs.python_fail_logger import PythonFailLogger


class BackendVerifyController(QObject):
    """Owns the QThread + BackendVerifyWorker lifecycle and re-emits the current worker's signals.

    A stopped worker can still deliver queued signals: a response that was already in
    flight, or the final notification of an interrupted wait. Only the worker started
    last is forwarded, so an old run can neither paint rows onto a newer table nor
    detach the run that replaced it.
    """

    rowResult = pyqtSignal(int, str, dict)
    waiting = pyqtSignal(float, str)
    finished = pyqtSignal(dict)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: BackendVerifyWorker | None = None

    def stop(self) -> None:
        worker = self._worker
        thread = self._thread

        self._worker = None
        self._thread = None

        try:
            if worker is not None:
                worker.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="backend_verify_worker_stop_failed",
            )

        try:
            if thread is not None:
                thread.quit()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="backend_verify_thread_quit_failed",
            )

    def start(
        self,
        rows: list[tuple[int, str, str]],
        *,
        source: str,
        import_context_by_tunnus: dict,
    ) -> None:
        self.stop()

        thread = QThread(self)
        worker = BackendVerifyWorker(
            rows,
            source=source,
            import_context_by_tunnus=import_context_by_tunnus,
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        # Each connection remembers its own worker; delivery is queued to this thread.
        worker.rowResult.connect(
            lambda row, tunnus, result, w=worker: self._forward(w, self.rowResult, row, tunnus, result)
        )
        worker.waiting.connect(
            lambda seconds, reason, w=worker: self._forward(w, self.waiting, seconds, reason)
        )
        worker.finished.connect(lambda summary, w=worker: self._on_worker_finished(w, summary))

        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker

        thread.start()

    def _forward(self, worker: BackendVerifyWorker, signal, *args) -> None:
        if worker is self._worker:
            signal.emit(*args)

    def _on_worker_finished(self, worker: BackendVerifyWorker, summary: dict) -> None:
        if worker is not self._worker:
            return
        self._worker = None
        self._thread = None
        self.finished.emit(summary)
