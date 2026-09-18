"""One run of the property dialog's checks, kept in one object.

A single press of "Run checks" used to spread itself over about fifteen dialog fields,
reset by hand in up to three places each. Everything a run produces lives here instead:
its scope, its per-row results, its MAIN-layer context and its completion accounting.
Starting a run means creating one of these; stopping a run means dropping it.

Two rules the object owns, because a plain dialog field cannot enforce them:

* a run that was replaced or cancelled accepts nothing more. Every record method answers
  False and changes nothing, so a controller signal that was already queued when the run
  ended can neither paint onto the run that replaced it nor revive the old one.
* a run that never finished never reports completion. `mark_finished` answers True
  exactly once, and never for a cancelled run.

Qt-free on purpose, like `property_dialog_phase`: a run can be built and driven in a test
without a dialog, a table or an event loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class CheckRow:
    """One table row as the run saw it when it started.

    The feature travels with the row because the decisions a finished run offers are
    collected after the attention filter has already changed what the table shows.
    """

    row: int
    tunnus: str
    import_muudet: str = ""
    feature: Any = None


class PropertyCheckRun:
    """Everything one check run knows, from its scope to its completion."""

    def __init__(self, rows: Sequence[CheckRow], *, run_id: int = 0) -> None:
        self.run_id = int(run_id)
        self.rows: Tuple[CheckRow, ...] = tuple(rows or ())

        self._tunnus_by_row: Dict[int, str] = {int(r.row): r.tunnus for r in self.rows}
        self._keys: Set[Any] = set()
        self._row_by_key: Dict[Any, int] = {}
        self._feature_by_key: Dict[Any, Any] = {}
        for entry in self.rows:
            key = self._key(entry.row)
            self._keys.add(key)
            self._row_by_key.setdefault(key, int(entry.row))
            self._feature_by_key.setdefault(key, entry.feature)

        # MAIN-layer context, resolved once per run on the UI thread.
        self.main_layer: Any = None
        self.main_layer_lookup: Dict[str, Any] = {}
        self.main_checks_started: bool = False

        # Results.
        self.backend_causes: Dict[Any, List[str]] = {}
        self.backend_decisions: Dict[Any, Any] = {}
        self.main_causes: Dict[Any, List[str]] = {}
        self.backend_checked: Set[Any] = set()
        self.main_checked: Set[Any] = set()

        # Lifecycle.
        self.cancelled: bool = False
        self.finished: bool = False

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    def _key(self, row: int) -> Any:
        """What a result is filed under: the table row this run started from."""
        return int(row)

    def tunnus_for_row(self, row: int) -> str:
        return self._tunnus_by_row.get(int(row), "")

    def row_indices(self) -> Tuple[int, ...]:
        return tuple(int(entry.row) for entry in self.rows)

    def rows_for_verify_by_row(self) -> Dict[int, Tuple[str, str]]:
        """The scope in the shape the check controllers are configured with."""
        return {int(entry.row): (entry.tunnus, entry.import_muudet) for entry in self.rows}

    def controller_rows(self) -> List[Tuple[int, str, str]]:
        """The scope in the shape BackendVerifyController.start expects."""
        return [(int(entry.row), entry.tunnus, entry.import_muudet) for entry in self.rows]

    def tunnused(self) -> Set[str]:
        return {entry.tunnus for entry in self.rows if entry.tunnus}

    # ------------------------------------------------------------------
    # Accounting
    # ------------------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self._keys)

    def done_count(self) -> int:
        """A row counts as checked only when both the backend and MAIN checks finished."""
        return len(self.backend_checked & self.main_checked)

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and self.done_count() >= self.total

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def accepts(self) -> bool:
        """A replaced, cancelled or finished run takes no further results."""
        return not (self.cancelled or self.finished)

    def cancel(self) -> None:
        self.cancelled = True

    def mark_finished(self) -> bool:
        """Answer True for the one call that may announce this run as finished."""
        if not self.accepts():
            return False
        self.finished = True
        return True

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    def record_backend(self, row: int, causes: Optional[Iterable[Any]], decision: Any) -> bool:
        key = self._accepted_key(row)
        if key is None:
            return False
        self.backend_causes[key] = self._clean_causes(causes)
        self.backend_decisions[key] = decision
        self.backend_checked.add(key)
        return True

    def record_main(self, row: int, causes: Optional[Iterable[Any]]) -> bool:
        key = self._accepted_key(row)
        if key is None:
            return False
        self.main_causes[key] = self._clean_causes(causes)
        self.main_checked.add(key)
        return True

    def mark_backend_all_checked(self) -> bool:
        """The backend run could not start at all; MAIN checks alone drive completion."""
        if not self.accepts():
            return False
        self.backend_checked.update(self._keys)
        return True

    def _accepted_key(self, row: int) -> Optional[Any]:
        if not self.accepts():
            return None
        key = self._key(row)
        return key if key in self._keys else None

    @staticmethod
    def _clean_causes(causes: Optional[Iterable[Any]]) -> List[str]:
        return [text for text in (str(c).strip() for c in (causes or [])) if text]

    # ------------------------------------------------------------------
    # Reading results back
    # ------------------------------------------------------------------
    def causes_for_row(self, row: int) -> Tuple[List[str], List[str]]:
        """(main causes, backend causes) for one row; empty lists for an unknown row."""
        key = self._key(row)
        return (list(self.main_causes.get(key) or []), list(self.backend_causes.get(key) or []))

    def done_for_row(self, row: int) -> Tuple[bool, bool]:
        """(MAIN finished, backend finished) for one row."""
        key = self._key(row)
        return (key in self.main_checked, key in self.backend_checked)

    def unchecked_main_rows(self) -> List[int]:
        return [int(entry.row) for entry in self.rows
                if self._key(entry.row) not in self.main_checked]

    def decisions_in_row_order(self) -> List[Tuple[int, Any, Any]]:
        """(row, decision, feature) for every recorded decision, in table order.

        The feature comes from the run's own snapshot rather than from the table, which
        the attention filter may have changed since.
        """

        entries = [(self._row_by_key.get(key, 0), decision, self._feature_by_key.get(key))
                   for key, decision in self.backend_decisions.items()]
        return sorted(entries, key=lambda entry: entry[0])
