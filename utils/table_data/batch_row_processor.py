from typing import Callable, Iterable, Optional

from PyQt5.QtCore import QTimer, QCoreApplication
from ...Logs.python_fail_logger import PythonFailLogger


class BatchRowProcessor:
    """UI-thread batch processor for large row lists.

    Use this to process or insert rows in small chunks to keep UI responsive.
    """

    def __init__(self, parent=None) -> None:
        self._timer: Optional[QTimer] = None
        self._pending: list = []
        self._batch_size: int = 25
        self._process_events_every: int = 12
        self._processed_since_events: int = 0
        self._process_row: Optional[Callable[[object, int], None]] = None
        self._on_finished: Optional[Callable[[], None]] = None
        self._on_progress: Optional[Callable[[int, int], None]] = None
        self._total: int = 0
        self._parent = parent

    def configure(
        self,
        *,
        batch_size: int = 25,
        interval_ms: int = 0,
        process_events_every: int = 12,
    ) -> None:
        self._batch_size = max(1, int(batch_size or 1))
        self._interval_ms = max(0, int(interval_ms or 0))
        self._process_events_every = max(1, int(process_events_every or 1))

    def start(
        self,
        rows: Iterable,
        *,
        process_row: Callable[[object, int], None],
        on_finished: Optional[Callable[[], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        batch_size: int = 25,
        interval_ms: int = 0,
        process_events_every: int = 12,
    ) -> None:
        self.stop()

        self.configure(
            batch_size=batch_size,
            interval_ms=interval_ms,
            process_events_every=process_events_every,
        )

        self._pending = list(rows or [])
        self._total = len(self._pending)
        self._process_row = process_row
        self._on_finished = on_finished
        self._on_progress = on_progress
        self._processed_since_events = 0

        if not self._pending:
            if self._on_progress is not None:
                self._on_progress(0, 0)
            if self._on_finished is not None:
                self._on_finished()
            return

        timer = QTimer(self._parent)
        timer.setSingleShot(False)
        timer.timeout.connect(self._tick)
        self._timer = timer

        try:
            QTimer.singleShot(0, lambda: timer.start(self._interval_ms))
        except Exception:
            timer.start(self._interval_ms)

    def stop(self) -> None:
        try:
            if self._timer is not None:
                self._timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="batch_row_timer_stop_failed",
            )
        self._timer = None
        self._pending = []
        self._processed_since_events = 0
        self._process_row = None
        self._on_finished = None
        self._on_progress = None
        self._total = 0

    def _tick(self) -> None:
        if not self._pending:
            self.stop()
            if self._on_finished is not None:
                self._on_finished()
            return

        processed = 0
        while self._pending and processed < self._batch_size:
            row = self._pending.pop(0)
            row_index = self._total - len(self._pending) - 1
            if self._process_row is not None:
                self._process_row(row, row_index)
            processed += 1

        if self._on_progress is not None:
            done = self._total - len(self._pending)
            self._on_progress(done, self._total)

        self._processed_since_events += processed
        if self._processed_since_events >= self._process_events_every:
            QCoreApplication.processEvents()
            self._processed_since_events = 0
