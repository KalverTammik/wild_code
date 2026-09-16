"""Utility helpers for running blocking tasks off the UI thread."""

from typing import Any, Callable, Optional
import sys
from threading import Event

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from ..Logs.switch_logger import SwitchLogger
from ..Logs.python_fail_logger import PythonFailLogger
from .api_rate_limit import api_request_context, RequestCancelled

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
    waiting = pyqtSignal(float, str)

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._cancel_event = Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    @pyqtSlot()
    def run(self) -> None:
        try:
            SwitchLogger.log("worker_run_start", extra={"func": getattr(self._func, "__name__", "callable")})
            with api_request_context(cancel_event=self._cancel_event, on_wait=self.waiting.emit):
                result = self._func(*self._args, **self._kwargs)
        except RequestCancelled as exc:
            self.error.emit(str(exc))
            return
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
    worker: QObject,
    *,
    auto_delete: bool = True,
    on_thread_finished: Optional[Callable[[], None]] = None,
) -> QThread:
    """Move worker into a managed QThread and start it.

    Accepts a FunctionWorker or any QObject with a ``run`` slot and a ``finished``
    signal. The thread has no parent and stays referenced until it finishes, so
    deleting the owner of a running worker never destroys its thread.
    """

    func = getattr(worker, "_func", None)
    name = getattr(func, "__name__", "callable") if func is not None else type(worker).__name__
    thread = QThread()
    worker.moveToThread(thread)
    _ACTIVE_THREADS.add(thread)

    def cleanup() -> None:
        SwitchLogger.log("worker_thread_finished", extra={"func": name})
        if auto_delete:
            worker.deleteLater()
            thread.deleteLater()
        if on_thread_finished:
            on_thread_finished()
        _ACTIVE_THREADS.discard(thread)

    worker.finished.connect(thread.quit)
    error = getattr(worker, "error", None)
    if error is not None:
        error.connect(thread.quit)
    thread.finished.connect(cleanup)
    thread.started.connect(lambda: SwitchLogger.log("worker_thread_started", extra={"func": name}))
    thread.started.connect(worker.run)
    thread.start()
    return thread
