"""Utility helpers for running blocking tasks off the UI thread."""

from typing import Any, Callable, Optional
import sys

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from ..Logs.switch_logger import SwitchLogger
from ..Logs.python_fail_logger import PythonFailLogger

_ACTIVE_THREADS: set[QThread] = set()


def _resolve_module_name(func: Callable[..., Any]) -> str | None:
    target = getattr(func, "__self__", None)
    if target is None:
        return None
    for attr in ("module_key", "name", "_module", "_module_key"):
        value = getattr(target, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


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
            SwitchLogger.log("worker_run_start", extra={"func": getattr(self._func, "__name__", "callable")})
            result = self._func(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - propagate as text
            SwitchLogger.log("worker_run_error", extra={"func": getattr(self._func, "__name__", "callable"), "error": str(exc)})
            try:
                PythonFailLogger.log_exception(
                    exc,
                    module=_resolve_module_name(self._func),
                    event="worker_error",
                    extra={"func": getattr(self._func, "__name__", "callable")},
                )
            except Exception as log_exc:
                print(f"[FunctionWorker] Failed to log exception: {log_exc}", file=sys.stderr)
            self.error.emit(str(exc))
            return
        SwitchLogger.log("worker_run_done", extra={"func": getattr(self._func, "__name__", "callable")})
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
    _ACTIVE_THREADS.add(thread)

    def cleanup() -> None:
        SwitchLogger.log("worker_thread_finished", extra={"func": getattr(worker._func, "__name__", "callable")})
        if auto_delete:
            worker.deleteLater()
            thread.deleteLater()
        if on_thread_finished:
            on_thread_finished()
        _ACTIVE_THREADS.discard(thread)

    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    thread.finished.connect(cleanup)
    thread.started.connect(lambda: SwitchLogger.log("worker_thread_started", extra={"func": getattr(worker._func, "__name__", "callable")}))
    thread.started.connect(worker.run)
    thread.start()
    return thread
