"""Utility helpers for running blocking tasks off the UI thread."""

import time
from typing import Any, Callable, Optional
from threading import Event

from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from ..Logs.switch_logger import SwitchLogger
from ..Logs.python_fail_logger import PythonFailLogger
from .api_rate_limit import api_request_context, RequestCancelled

# Running thread -> its worker. An entry leaves in cleanup() once the thread
# has finished, or in stop_all_workers(). A dict keeps the membership checks
# ("thread in _ACTIVE_THREADS", "not _ACTIVE_THREADS") of the tests working.
_ACTIVE_THREADS: dict[QThread, QObject] = {}
# Threads stopped by stop_all_workers() whose cleanup() has not run yet. The
# reference keeps a thread that outlived the wait from being destroyed while
# still running, and cleanup() skips the owner callback for these: the owner
# is being unloaded.
_STOPPED_THREADS: set[QThread] = set()


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
        self._detached = False

    def cancel(self) -> None:
        """Stop the request before it is sent. The outcome (error) is still delivered."""
        self._cancel_event.set()

    def detach(self) -> None:
        """Drop the outcome: neither finished nor error is emitted after this.

        Used when the owner is going away (plugin unload). cancel() alone must
        keep delivering, because LatestRequest waits for the error of a
        cancelled request to start the next one.
        """
        self._detached = True

    @pyqtSlot()
    def run(self) -> None:
        func_name = getattr(self._func, "__name__", "callable")
        try:
            SwitchLogger.log("worker_run_start", extra={"func": func_name})
            with api_request_context(cancel_event=self._cancel_event, on_wait=self.waiting.emit):
                result = self._func(*self._args, **self._kwargs)
        except RequestCancelled as exc:
            if not self._detached:
                self.error.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - propagate as text
            SwitchLogger.log("worker_run_error", extra={"func": func_name, "error": str(exc)})
            PythonFailLogger.log_exception(
                exc,
                module=_resolve_module_name(self._func),
                event="worker_error",
                extra={"func": func_name},
            )
            if not self._detached:
                self.error.emit(str(exc))
            return
        SwitchLogger.log("worker_run_done", extra={"func": func_name})
        if self._detached:
            SwitchLogger.log("worker_result_dropped", extra={"func": func_name})
            return
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
    _ACTIVE_THREADS[thread] = worker

    def cleanup() -> None:
        SwitchLogger.log("worker_thread_finished", extra={"func": name})
        if auto_delete:
            worker.deleteLater()
            thread.deleteLater()
        _ACTIVE_THREADS.pop(thread, None)
        stopped = thread in _STOPPED_THREADS
        _STOPPED_THREADS.discard(thread)
        if on_thread_finished and not stopped:
            on_thread_finished()

    worker.finished.connect(thread.quit)
    error = getattr(worker, "error", None)
    if error is not None:
        error.connect(thread.quit)
    thread.finished.connect(cleanup)
    thread.started.connect(lambda: SwitchLogger.log("worker_thread_started", extra={"func": name}))
    thread.started.connect(worker.run)
    thread.start()
    return thread


def stop_all_workers(timeout_ms: int = 2000) -> None:
    """Stop every running worker because their owners are being unloaded.

    Each worker is detached (its outcome is never emitted) and cancelled, its
    thread is told to quit, and all threads together get ``timeout_ms`` to
    finish. The registry is emptied right away. A thread still running after
    the wait stays referenced in ``_STOPPED_THREADS`` until its cleanup runs,
    so it is never destroyed while running; its result is dropped by the
    detached worker.
    """
    entries = list(_ACTIVE_THREADS.items())
    _ACTIVE_THREADS.clear()
    if not entries:
        return
    SwitchLogger.log("workers_stop_all", extra={"count": str(len(entries))})
    for thread, worker in entries:
        _STOPPED_THREADS.add(thread)
        detach = getattr(worker, "detach", None)
        if callable(detach):
            detach()
        cancel = getattr(worker, "cancel", None)
        if callable(cancel):
            cancel()
        thread.quit()
    deadline = time.monotonic() + max(0, timeout_ms) / 1000.0
    for thread, worker in entries:
        remaining_ms = int(max(0.0, deadline - time.monotonic()) * 1000)
        if not thread.wait(remaining_ms):
            func = getattr(worker, "_func", None)
            SwitchLogger.log(
                "worker_thread_stop_timeout",
                extra={"func": getattr(func, "__name__", type(worker).__name__)},
            )
