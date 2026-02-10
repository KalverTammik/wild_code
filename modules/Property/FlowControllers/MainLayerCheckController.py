from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QCoreApplication, QObject, QTimer, pyqtSignal

from ....constants.cadastral_fields import Katastriyksus
from ....utils.MapTools.MapHelpers import MapHelpers
from ....widgets.DateHelpers import DateHelpers
from ....Logs.python_fail_logger import PythonFailLogger


class MainLayerCheckController(QObject):
    """Runs MAIN-layer checks on the UI thread, optionally in batches.

    QGIS layer/feature access must remain on the UI thread, so this controller uses a QTimer
    to process remaining rows in small chunks.
    """

    rowResult = pyqtSignal(int, list)  # (row, causes)
    finished = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._timer: Optional[QTimer] = None
        self._pending_rows: List[int] = []
        self._batch_size: int = 25

        self._checked_rows: set[int] = set()
        self._rows_for_verify_by_row: Dict[int, Tuple[str, str]] = {}
        self._main_layer = None
        self._main_muudet_override_by_tunnus: Dict[str, str] = {}
        self._main_layer_lookup: Dict[str, Any] = {}
        self._process_events_counter: int = 0
        self._process_events_every: int = 12

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def configure(
        self,
        *,
        rows_for_verify_by_row: Dict[int, Tuple[str, str]],
        main_layer,
        main_muudet_override_by_tunnus: Optional[Dict[str, str]] = None,
        checked_rows: Optional[set[int]] = None,
        main_layer_lookup: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.stop()
        self._rows_for_verify_by_row = dict(rows_for_verify_by_row or {})
        self._main_layer = main_layer
        self._main_muudet_override_by_tunnus = dict(main_muudet_override_by_tunnus or {})
        self._checked_rows = set(checked_rows or set())
        self._main_layer_lookup = dict(main_layer_lookup or {})

    def is_checked(self, row: int) -> bool:
        return int(row) in self._checked_rows

    # ------------------------------------------------------------------
    # Public control
    # ------------------------------------------------------------------
    def ensure_row(self, row: int) -> None:
        row_idx = int(row)
        if row_idx in self._checked_rows:
            return

        causes = self._compute_causes_for_row(row_idx)
        self._checked_rows.add(row_idx)
        self.rowResult.emit(row_idx, causes)

    def start_pending(
        self,
        rows: Sequence[int],
        *,
        batch_size: int = 25,
        interval_ms: int = 0,
    ) -> None:
        self.stop()

        self._batch_size = max(1, int(batch_size or 1))
        self._pending_rows = [int(r) for r in (rows or []) if int(r) not in self._checked_rows]

        if not self._pending_rows:
            self.finished.emit()
            return

        timer = QTimer(self)
        timer.setSingleShot(False)
        timer.timeout.connect(self._tick)
        self._timer = timer

        try:
            QTimer.singleShot(0, lambda: timer.start(max(0, int(interval_ms))))
        except Exception:
            timer.start(max(0, int(interval_ms)))

    def stop(self) -> None:
        try:
            if self._timer is not None:
                self._timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="main_layer_check_timer_stop_failed",
            )
        self._timer = None
        self._pending_rows = []
        self._process_events_counter = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        if not self._pending_rows:
            self.stop()
            self.finished.emit()
            return

        processed = 0
        while self._pending_rows and processed < self._batch_size:
            row_idx = int(self._pending_rows.pop(0))
            processed += 1

            if row_idx in self._checked_rows:
                continue

            causes = self._compute_causes_for_row(row_idx)
            self._checked_rows.add(row_idx)
            self.rowResult.emit(row_idx, causes)

        self._process_events_counter += processed
        if self._process_events_counter >= self._process_events_every:
            QCoreApplication.processEvents()
            self._process_events_counter = 0

    def _compute_causes_for_row(self, row_idx: int) -> List[str]:
        tunnus, import_muudet = self._rows_for_verify_by_row.get(int(row_idx), ("", ""))
        if not tunnus:
            return []

        main_layer = self._main_layer
        if not main_layer:
            return []

        feature = None
        try:
            if self._main_layer_lookup:
                feature = self._main_layer_lookup.get(tunnus)
        except Exception:
            feature = None

        causes: List[str] = []
        if feature is None:
            try:
                matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
            except Exception:
                matches = []

            if not matches:
                causes.append("missing in main layer")
                return causes

            feature = matches[0]
        try:
            main_muudet_raw = feature.attribute(Katastriyksus.muudet)
        except Exception:
            main_muudet_raw = None

        import_dt = DateHelpers.parse_iso(str(import_muudet) if import_muudet is not None else "")

        main_override = self._main_muudet_override_by_tunnus.get(tunnus)
        if main_override is not None:
            main_iso = str(main_override)
        else:
            try:
                main_iso = "" if main_muudet_raw is None else (
                    DateHelpers().date_to_iso_string(main_muudet_raw) or str(main_muudet_raw)
                )
            except Exception:
                main_iso = ""

        main_dt = DateHelpers.parse_iso(str(main_iso) if main_iso is not None else "")

        if import_dt and main_dt and import_dt > main_dt:
            causes.append("main layer older")

        return causes
