"""Utility helpers for running blocking tasks off the UI thread."""

from typing import Any, Callable, Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class FunctionWorker(QObject):
    """Runs the provided callable with args/kwargs inside a QThread."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = self._func(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - propagate as text
            self.error.emit(str(exc))
            return
        self.finished.emit(result)


def start_worker(
    worker: FunctionWorker,
    *,
    auto_delete: bool = True,
    on_thread_finished: Optional[Callable[[], None]] = None,
) -> QThread:
    """Move worker into a managed QThread and start it."""

    thread = QThread()
    worker.moveToThread(thread)

    def cleanup() -> None:
        if auto_delete:
            worker.deleteLater()
            thread.deleteLater()
        if on_thread_finished:
            on_thread_finished()

    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    thread.finished.connect(cleanup)
    thread.started.connect(worker.run)
    thread.start()
    return thread
