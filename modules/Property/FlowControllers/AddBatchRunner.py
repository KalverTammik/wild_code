from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import sip

from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from .MainAddProperties import MainAddPropertiesFlow
from ....Logs.python_fail_logger import PythonFailLogger


class AddBatchRunner(QObject):
    """Runs property adds in small batches on the UI thread.

    Keeps UI responsive by chunking work and scheduling the next batch via QTimer.
    """

    progress = pyqtSignal(int, int, str, str)  # done, total, phase, last_tunnus
    finished = pyqtSignal(dict)  # {"canceled": bool, "done": int, "total": int}

    def __init__(
        self,
        table,
        *,
        batch_size: int = 1,
        rest_every: int = 25,
        rest_ms: int = 1000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._table = table
        self._batch_size = max(1, int(batch_size or 1))
        self._rest_every = max(1, int(rest_every or 1))
        self._rest_ms = max(0, int(rest_ms or 0))

        self._queue: List = []
        self._done = 0
        self._total = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._tick)
        self._stop_requested = False
        self._paused = False
        self._batches_processed = 0

    def _dispose_timer(self) -> None:
        if sip.isdeleted(self):
            return
        try:
            if self._timer is not None:
                self._timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_timer_stop_failed",
            )
        try:
            if self._timer is not None:
                self._timer.timeout.disconnect()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_timer_disconnect_failed",
            )
        try:
            if self._timer is not None:
                self._timer.deleteLater()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_timer_delete_failed",
            )
        self._timer = None

    def start(self) -> None:
        MainAddPropertiesFlow.reset_cancel()
        MainAddPropertiesFlow.reset_yes_to_all_flags()
        mgr = PropertyTableManager()
        try:
            self._queue = list(mgr.get_selected_features(self._table) or [])
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_get_selected_failed",
            )
            self._queue = []

        self._total = len(self._queue)
        self._done = 0
        self._batches_processed = 0
        self._stop_requested = False
        self._paused = False

        if not self._queue:
            self.finished.emit({"canceled": False, "done": 0, "total": 0})
            return

        self.progress.emit(0, self._total, "starting", "")
        self._timer.start(0)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        if not self._paused:
            return
        self._paused = False
        if not self._timer.isActive():
            self._timer.start(0)

    def cancel(self) -> None:
        self._stop_requested = True
        self._queue = []
        MainAddPropertiesFlow.request_cancel()
        try:
            self._timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_timer_stop_failed",
            )

        try:
            if self._timer is not None:
                self._timer.timeout.disconnect()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_timer_disconnect_failed",
            )

        # If no tick is pending, emit finished now so UI can unwind immediately.
        if not self._timer.isActive():
            self._dispose_timer()
            if not sip.isdeleted(self):
                self.finished.emit({"canceled": True, "done": self._done, "total": self._total})

    # ------------------------------------------------------------------
    def _tick(self) -> None:
        if sip.isdeleted(self) or self._timer is None or sip.isdeleted(getattr(self, "_timer", None)):
            return

        if self._stop_requested:
            self._dispose_timer()
            if not sip.isdeleted(self):
                self.finished.emit({"canceled": True, "done": self._done, "total": self._total})
            return

        if self._paused:
            # Stay idle until resumed.
            return

        if not self._queue:
            self._dispose_timer()
            if not sip.isdeleted(self):
                self.finished.emit({"canceled": False, "done": self._done, "total": self._total})
            return

        # Process one batch.
        batch = self._queue[: self._batch_size]
        self._queue = self._queue[self._batch_size :]

        last_tunnus = ""
        try:
            for f in batch:
                try:
                    last_tunnus = str(f.attribute("tunnus")) if f is not None else ""
                except Exception:
                    last_tunnus = ""

            # This call is synchronous but limited to the batch size to keep UI responsive.
            MainAddPropertiesFlow.start_adding_properties(selected_features=batch)
        except Exception:
            # Continue; errors are surfaced via dialogs in the flow.
            pass

        self._done += len(batch)
        self._batches_processed += 1

        if not sip.isdeleted(self):
            self.progress.emit(self._done, self._total, "processing", last_tunnus)

        if self._stop_requested:
            self._dispose_timer()
            if not sip.isdeleted(self):
                self.finished.emit({"canceled": True, "done": self._done, "total": self._total})
            return

        if not self._queue:
            self._dispose_timer()
            if not sip.isdeleted(self):
                self.finished.emit({"canceled": bool(self._stop_requested), "done": self._done, "total": self._total})
            return

        # Respect backend rest window: after N batches, wait rest_ms before next batch.
        if self._batches_processed % self._rest_every == 0:
            self._timer.start(self._rest_ms)
        else:
            self._timer.start(0)
