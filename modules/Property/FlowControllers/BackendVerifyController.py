from __future__ import annotations

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .BackendVerifyWorker import BackendVerifyWorker
from ....Logs.python_fail_logger import PythonFailLogger


class BackendVerifyController(QObject):
    """Owns the QThread + BackendVerifyWorker lifecycle and re-emits worker signals."""

    rowResult = pyqtSignal(int, str, dict)
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
        backend_last_updated_override_by_tunnus: dict[str, str] | None = None,
    ) -> None:
        self.stop()

        thread = QThread(self)
        worker = BackendVerifyWorker(
            rows,
            source=source,
            backend_last_updated_override_by_tunnus=backend_last_updated_override_by_tunnus or {},
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.rowResult.connect(self.rowResult)
        worker.finished.connect(self._on_worker_finished)

        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker

        thread.start()

    def _on_worker_finished(self, summary: dict) -> None:
        self._worker = None
        self._thread = None
        self.finished.emit(summary)
