from ...FlowControllers.property_add_flow import MainAddPropertiesFlow
from ...FlowControllers.backend_verify_controller import BackendVerifyController
from .....widgets.property_table.PropertyTableManager import PropertyTableManager
from ...FlowControllers.property_archive_plan import (
    PropertyArchiveScope,
    classify_archive_candidates,
)
from ...FlowControllers.property_dialog_phase import PropertyDialogMode
from .....widgets.DelayHelpers.glow_progress_bar import GlowProgressBar
from .....languages.translation_keys import TranslationKeys
from .....constants.layer_constants import IMPORT_PROPERTY_TAG
from .....utils.MapTools.MapHelpers import MapHelpers
from .....ui.messages_helper import ModernMessageDialog
from .....constants.cadastral_fields import Katastriyksus
from ..PropertyArchivePlanDialog import PropertyArchivePlanDialog
from .....Logs.python_fail_logger import PythonFailLogger
from ...FlowControllers.property_archive_scope_reader import (
    archive_candidate_row,
    find_import_tunnused,
    layer_identity,
    read_scope_features,
)


class PropertyArchivePlanMixin:
    """Archiving the properties that left the import: the scope snapshot, the plan, its
    background backend lookup, the confirmation and the archive call. Mixed into
    AddPropertyDialog, whose __init__ creates the controller and state used here.
    """

    def _invalidate_archive_scope(self) -> None:
        """A new table scope invalidates the archive plan and the previous run's result."""
        self._reset_archive_plan_state()
        self._clear_add_result()

    def _reset_archive_plan_state(self) -> None:
        self._checks_completed_for_scope = False
        self._archive_scope_snapshot = None
        self._archive_scope_blocked_reason = ""
        self._archive_moved_elsewhere = set()
        self._archive_preliminary_missing = set()
        self._archive_candidate_settlement = {}
        self._missing_from_import = set()
        self._archive_backend_plan = {}
        self._archive_map_plan = {}

    def _current_location_scope(self) -> tuple[str, str, tuple[str, ...]]:
        if self._dialog_mode != PropertyDialogMode.BY_LOCATION:
            return ("", "", tuple())
        county = str(self.county_combo.currentData() or "").strip() if self.county_combo else ""
        municipality = (
            str(self.municipality_combo.currentData() or "").strip()
            if self.municipality_combo
            else ""
        )
        settlements = tuple(
            sorted(
                {
                    str(value).strip()
                    for value in (self.city_combo.checkedItems() if self.city_combo else [])
                    if str(value).strip()
                }
            )
        )
        return (county, municipality, settlements)

    def _table_tunnused(self) -> set[str]:
        return PropertyTableManager.get_cadastral_ids(self.properties_table)

    def _capture_archive_scope_snapshot(self, *, load_succeeded: bool) -> None:
        county, municipality, settlements = self._current_location_scope()
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        layer_id, layer_source = layer_identity(import_layer)
        self._archive_scope_snapshot = PropertyArchiveScope.create(
            county=county,
            municipality=municipality,
            settlements=settlements,
            import_tunnused=self._table_tunnused(),
            import_layer_id=layer_id,
            import_layer_source=layer_source,
            load_succeeded=load_succeeded,
        )
        self._archive_scope_blocked_reason = self._archive_scope_snapshot.blocked_reason

    def _compute_scoped_archive_plan(self) -> set[str]:
        scope = self._archive_scope_snapshot
        if scope is None or not scope.complete:
            self._archive_scope_blocked_reason = (
                scope.blocked_reason if scope is not None else "scope_not_loaded"
            )
            return set()

        main_layer = self._plan_main_layer()
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        try:
            main_features = read_scope_features(main_layer, scope)
            preliminary = set(main_features).difference(scope.import_tunnused)
            found_elsewhere = find_import_tunnused(import_layer, preliminary)
            classification = classify_archive_candidates(
                scope=scope,
                main_scope_tunnused=main_features,
                import_tunnused_found_elsewhere=found_elsewhere,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="property_archive_scope_plan_failed",
            )
            self._archive_scope_blocked_reason = "scope_read_failed"
            return set()

        self._archive_scope_blocked_reason = classification.blocked_reason
        self._archive_preliminary_missing = set(preliminary)
        self._archive_moved_elsewhere = set(classification.moved_elsewhere)
        self._archive_candidate_settlement = {
            tunnus: str(main_features[tunnus].attribute(Katastriyksus.ay_nimi) or "").strip()
            for tunnus in classification.candidates
            if tunnus in main_features
        }
        return set(classification.candidates)

    def _archive_scope_is_current(self) -> bool:
        scope = self._archive_scope_snapshot
        if scope is None or not scope.complete or self._current_location_scope() != scope.key:
            return False
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if layer_identity(import_layer) != (scope.import_layer_id, scope.import_layer_source):
            return False
        try:
            current_features = read_scope_features(import_layer, scope)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="property_archive_scope_revalidate_failed",
            )
            return False
        if frozenset(current_features) != scope.import_tunnused:
            return False
        try:
            current_elsewhere = find_import_tunnused(
                import_layer,
                self._archive_preliminary_missing,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="property_archive_candidate_revalidate_failed",
            )
            return False
        return current_elsewhere == self._archive_moved_elsewhere

    def _archive_candidate_row(self, tunnus: str, backend_info) -> dict:
        return archive_candidate_row(
            tunnus,
            backend_info,
            settlement=self._archive_candidate_settlement.get(tunnus, ""),
            translate=self.lang_manager.translate,
        )

    def _plan_main_layer(self):
        """The layer the current run was computed against, or the cached one.

        The archive plan is applied after the run that produced it is already gone,
        and must not resolve the MAIN layer a second time by name (b5).
        """

        run = self._check_run
        return (run.main_layer if run is not None else None) or self._resolve_main_layer_cached()

    def _compute_missing_from_import_set(self) -> set[str]:
        return self._compute_scoped_archive_plan()

    def _run_missing_cleanup_if_any(self, then) -> None:
        """Archive properties missing from the import, then continue with ``then``.

        Backend lookups for the plan run in a worker, so the dialog stays responsive and
        the whole lookup is cancellable; plan review and layer edits stay on the GUI
        thread. ``then`` runs only when nothing is missing or the confirmed plan was
        applied without errors.
        """

        missing = sorted({str(t).strip() for t in (self._missing_from_import or set()) if str(t).strip()})
        if not missing:
            then()
            return

        if not self._archive_scope_is_current():
            self._warn_archive_plan_stale()
            return

        self._archive_lookup = {"missing": missing, "backend_info": {}, "then": then}
        self._set_add_ui_state(active=True)
        self._show_archive_lookup_progress()
        # Missing properties have no import row; the lookup only needs the cadastral number,
        # so it runs in lookup mode instead of inventing an import row to satisfy verify mode.
        self._archive_lookup_controller.start(
            [(index, tunnus, "") for index, tunnus in enumerate(missing)],
            source="archive_plan",
            mode=BackendVerifyController.MODE_LOOKUP,
        )

    def _warn_archive_plan_stale(self) -> None:
        self._reset_archive_plan_state()
        ModernMessageDialog.Warning_messages_modern(
            self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_STALE_TITLE),
            self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_STALE_BODY),
        )

    def _show_archive_lookup_progress(self) -> None:
        lookup = self._archive_lookup
        done, total = len(lookup["backend_info"]), len(lookup["missing"])
        self.check_progress_bar.hide()
        self.add_progress_label.setText(self.lang_manager.translate(
            TranslationKeys.PROPERTY_ARCHIVE_LOOKUP_PROGRESS).format(done=done, total=total))
        self.add_progress_label.show()
        self.add_progress_bar.setRange(0, max(1, total))
        self.add_progress_bar.setValue(done)
        self.add_progress_bar.setState(GlowProgressBar.RUNNING)
        self.add_progress_bar.show()

    def _on_archive_lookup_row(self, _row: int, tunnus: str, result: dict) -> None:
        if self._archive_lookup is None:
            return
        self._archive_lookup["backend_info"][tunnus] = result.get("backend_info")
        self._show_archive_lookup_progress()

    def _on_archive_lookup_waiting(self, seconds: float, reason: str) -> None:
        if self._archive_lookup is not None:
            self._show_request_wait(seconds, reason)

    def _on_archive_lookup_finished(self, summary: dict) -> None:
        lookup, self._archive_lookup = self._archive_lookup, None
        if lookup is None:
            return
        for error in summary.get("errors") or []:
            PythonFailLogger.log_exception(
                RuntimeError(error.get("error")),
                module="property",
                event="property_archive_candidate_backend_check_failed",
                extra={"tunnus": error.get("tunnus")},
            )
        self._hide_detail_label()
        self.add_progress_bar.hide()
        # Stays locked (b4) through the confirmation dialog and the archive call itself,
        # not just through the background backend lookup that precedes them.
        try:
            self._apply_archive_plan(lookup["missing"], lookup["backend_info"], lookup["then"])
        finally:
            self._set_add_ui_state(active=False)

    def _cancel_archive_lookup(self) -> None:
        # Only reads were made: the plan stays intact and the same add can be retried.
        self._archive_lookup = None
        self._archive_lookup_controller.stop()
        self._set_add_ui_state(active=False)
        self._hide_detail_label()
        self.add_progress_bar.hide()
        self.add_progress_label.setText(
            self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_LOOKUP_CANCELLED))
        self.add_progress_label.show()

    def _apply_archive_plan(self, missing: list[str], backend_info: dict, then) -> None:
        # The dialog stayed usable during the lookups, so the import may have changed meanwhile.
        if not self._archive_scope_is_current():
            self._warn_archive_plan_stale()
            return

        candidate_rows = [self._archive_candidate_row(tunnus, backend_info.get(tunnus)) for tunnus in missing]
        self._archive_backend_plan = {
            row["tunnus"]: bool(row.get("backend_allowed")) for row in candidate_rows
        }
        if not PropertyArchivePlanDialog.confirm(
            scope=self._archive_scope_snapshot,
            candidates=candidate_rows,
            parent=self,
        ):
            return

        backend_allowed = {t for t in missing if bool(self._archive_backend_plan.get(t, False))}

        label = self.add_progress_label
        if label is not None:
            label.setVisible(True)
            template = self.lang_manager.translate(TranslationKeys.ARCHIVE_MISSING_PROGRESS_START)
            label.setText(template.format(count=len(missing)))

        try:
            main_layer = self._plan_main_layer()
            summary = MainAddPropertiesFlow.archive_missing_from_import(
                missing, backend_allowed=backend_allowed, main_layer=main_layer)
            archived = int(summary.get("archived_backend") or 0)
            moved = int(summary.get("moved_map") or 0)
            errors = summary.get("errors") or []
            if label is not None:
                template = self.lang_manager.translate(TranslationKeys.ARCHIVE_MISSING_PROGRESS_RESULT)
                errors_suffix = (
                    self.lang_manager.translate(TranslationKeys.ARCHIVE_MISSING_PROGRESS_ERRORS_SUFFIX)
                    if errors
                    else ""
                )
                label.setText(
                    template.format(
                        archived=archived,
                        total=len(missing),
                        moved=moved,
                        errors_suffix=errors_suffix,
                    )
                )
            if errors:
                ModernMessageDialog.Warning_messages_modern(
                    self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_PARTIAL_TITLE),
                    self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_PLAN_PARTIAL_BODY).format(
                        moved=moved,
                        archived=archived,
                        failed=int(summary.get("backend_failed") or len(errors)),
                    ) + "\n\n" + "\n".join(str(error) for error in errors),
                )
                self._reset_archive_plan_state()
                return
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_archive_missing_failed",
            )
            if label is not None:
                template = self.lang_manager.translate(TranslationKeys.ARCHIVE_MISSING_PROGRESS_ERROR)
                label.setText(template.format(count=len(missing)))
            self._reset_archive_plan_state()
            return

        # Run once per check cycle.
        self._missing_from_import = set()
        self._archive_backend_plan = {}
        self._archive_map_plan = {}
        then()
