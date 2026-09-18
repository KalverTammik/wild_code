from __future__ import annotations

from PyQt5 import sip
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .BackendVerifyWorker import BackendVerifyWorker
from ....Logs.python_fail_logger import PythonFailLogger
from ....python.workers import start_worker


class BackendVerifyController(QObject):
    """Owns a BackendVerifyWorker run and re-emits the current worker's signals.

    A stopped worker can still deliver queued signals: a response that was already in
    flight, or the final notification of an interrupted wait. Only the worker started
    last is forwarded, so an old run can neither paint rows onto a newer table nor
    detach the run that replaced it.

    The thread comes from ``start_worker`` and is never a child of this controller, so
    deleting the owning dialog while a request is still in flight cannot destroy a
    running thread. Deleting the controller also stops its current run.
    """

    # Callers pick the run mode without importing the worker themselves.
    MODE_VERIFY = BackendVerifyWorker.MODE_VERIFY
    MODE_LOOKUP = BackendVerifyWorker.MODE_LOOKUP

    rowResult = pyqtSignal(int, str, dict)
    waiting = pyqtSignal(float, str)
    finished = pyqtSignal(dict)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: BackendVerifyWorker | None = None
        # An owner deleted without closing first, e.g. on plugin reload, still stops the run.
        self.destroyed.connect(lambda *_: self.stop())

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
        import_context_by_tunnus: dict | None = None,
        mode: str = BackendVerifyWorker.MODE_VERIFY,
    ) -> None:
        self.stop()

        worker = BackendVerifyWorker(
            rows,
            source=source,
            import_context_by_tunnus=import_context_by_tunnus,
            mode=mode,
        )

        # Connect before starting. Each connection remembers its own worker and is
        # delivered on this (GUI) thread. Signals are passed by name and read only after
        # the guard: reading a signal of an already deleted controller raises.
        worker.rowResult.connect(
            lambda row, tunnus, result, w=worker: self._forward(w, "rowResult", row, tunnus, result)
        )
        worker.waiting.connect(
            lambda seconds, reason, w=worker: self._forward(w, "waiting", seconds, reason)
        )
        worker.finished.connect(lambda summary, w=worker: self._on_worker_finished(w, summary))

        self._worker = worker
        self._thread = start_worker(worker)

    def _is_current(self, worker: BackendVerifyWorker) -> bool:
        return not sip.isdeleted(self) and worker is self._worker

    def _forward(self, worker: BackendVerifyWorker, signal_name: str, *args) -> None:
        if self._is_current(worker):
            getattr(self, signal_name).emit(*args)

    def _on_worker_finished(self, worker: BackendVerifyWorker, summary: dict) -> None:
        if not self._is_current(worker):
            return
        self._worker = None
        self._thread = None
        self.finished.emit(summary)
