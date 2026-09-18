"""Which buttons the property add dialog allows, decided in one place.

Two rules used to be written out by hand in three methods each: "decisions left by
an import go to the review before anything is added" and "the checked add needs a
finished check". Every new phase had to be added to all of them, and a forgotten
copy left a button quietly in the wrong state instead of failing. Both rules live
here now; the dialog only asks and obeys.

Qt-free on purpose: the dialog passes plain counts and flags, so the rules can be
read and tested without a widget.
"""

from __future__ import annotations

from dataclasses import dataclass


class PropertyDialogPhase:
    """What the dialog is busy with. The first matching phase wins."""

    ADDING = "adding"
    CHECKING = "checking"
    CHECKED = "checked"
    IDLE = "idle"


class AddMode:
    """How an add run was started; decides which guards it must still pass."""

    WITH_CHECKS = "with_checks"
    WITHOUT_CHECKS = "without_checks"
    REVIEW = "review"


class AddAction:
    """Where a request to add properties actually goes."""

    START = "start"
    REVIEW = "review"
    IGNORE = "ignore"


class CancelTarget:
    """What the cancel button stops: the innermost running work, or the dialog."""

    ARCHIVE_LOOKUP = "archive_lookup"
    CHECKS = "checks"
    ADD_RUN = "add_run"
    CLOSE = "close"


@dataclass(frozen=True)
class PropertyDialogState:
    """One immutable answer sheet for the add dialog's buttons and routing.

    The first four flags are the dialog's own stored state. The rest are read off
    the live dialog each time a decision is needed, so a list that was mutated in
    place can never leave a stale count behind.
    """

    add_in_progress: bool = False
    checks_running: bool = False
    checks_completed_for_scope: bool = False
    decisions_from_import: bool = False

    deferred_count: int = 0
    archive_lookup_active: bool = False
    has_add_runner: bool = False
    row_count: int = 0
    selected_count: int = 0

    @property
    def phase(self) -> str:
        if self.add_in_progress:
            return PropertyDialogPhase.ADDING
        if self.checks_running:
            return PropertyDialogPhase.CHECKING
        if self.checks_completed_for_scope:
            return PropertyDialogPhase.CHECKED
        return PropertyDialogPhase.IDLE

    @property
    def import_review_pending(self) -> bool:
        """An import's leftover decisions must be reviewed; a check's must not."""
        return bool(self.decisions_from_import and self.deferred_count > 0)

    # ------------------------------------------------------------------
    # Button rules
    # ------------------------------------------------------------------

    @property
    def can_add_with_checks(self) -> bool:
        return self.selected_count > 0 and self.phase == PropertyDialogPhase.CHECKED

    @property
    def can_add_without_checks(self) -> bool:
        return self.selected_count > 0 and self.phase != PropertyDialogPhase.ADDING

    @property
    def can_run_checks(self) -> bool:
        return self.row_count > 0 and self.phase not in (
            PropertyDialogPhase.ADDING, PropertyDialogPhase.CHECKING)

    @property
    def can_review_additions(self) -> bool:
        return self.phase != PropertyDialogPhase.ADDING and self.deferred_count > 0

    @property
    def scope_controls_enabled(self) -> bool:
        """Selection controls, the table and the location filter freeze only while adding."""
        return self.phase != PropertyDialogPhase.ADDING

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def add_action(self, *, with_checks: bool) -> str:
        """Where a click on one of the two add buttons goes.

        The two paths are deliberately not symmetric, and this is the only place
        that asymmetry is written down: the unchecked add refuses an empty scope
        itself, while the checked add leaves that to its button, which is already
        gated on the same count.
        """

        if self.import_review_pending:
            return AddAction.REVIEW
        if with_checks:
            return AddAction.START if self.phase == PropertyDialogPhase.CHECKED else AddAction.IGNORE
        if self.phase == PropertyDialogPhase.ADDING or self.selected_count <= 0:
            return AddAction.IGNORE
        return AddAction.START

    def batch_add_action(self, *, mode: str) -> str:
        """The runner's own last guard, for a start that did not come from a button."""

        if self.phase == PropertyDialogPhase.ADDING:
            return AddAction.IGNORE
        if self.import_review_pending and mode != AddMode.REVIEW:
            return AddAction.REVIEW
        if mode == AddMode.WITH_CHECKS and self.phase != PropertyDialogPhase.CHECKED:
            return AddAction.IGNORE
        return AddAction.START

    @property
    def cancel_target(self) -> str:
        """An archive lookup, a check and an add run can all be live; stop the innermost.

        This reads the runner rather than `add_in_progress`, because a finished run
        clears the flag first and the runner a moment later.
        """

        if self.archive_lookup_active:
            return CancelTarget.ARCHIVE_LOOKUP
        if self.checks_running:
            return CancelTarget.CHECKS
        if self.has_add_runner:
            return CancelTarget.ADD_RUN
        return CancelTarget.CLOSE
