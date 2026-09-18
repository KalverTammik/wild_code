"""Run a new test against the old behaviour, restored in-process with patches.

Source files stay untouched, so the regular suite can run at the same time.
Each scenario must FAIL; a pass would mean the test does not guard the fix.

Not named ``test_*.py`` on purpose: this is an argv-driven standalone runner, not
a test module, and ``unittest discover`` must skip it.

Usage::

    QT_QPA_PLATFORM=offscreen python-qgis-ltr.bat tests/negative_checks.py <scenario>

The plugin is imported from the checkout this file lives in, not from a fixed
profile directory, so the script tests whatever tree it is run from.
"""
import contextlib
import importlib.util
import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The plugin is imported by package name, so its PARENT goes on the path -- and in
# front of everything, or QGIS' own profile plugins directory would win.
sys.path.insert(0, os.path.dirname(PLUGIN))
# The test modules import ``property_fixtures`` as a plain top level module.
sys.path.insert(0, os.path.join(PLUGIN, 'tests'))

CONTROLLER_TEST = 'CheckedPropertyAddTest.test_check_controller_interrupts_rate_limit_wait_and_ignores_a_replaced_run'
DIALOG_TEST = ('PropertyLocationDialogFlowTest.'
               'test_real_dialog_shows_check_rate_limit_wait_and_cancel_keeps_the_dialog_open')
OWNER_DELETION_TEST = 'CheckedPropertyAddTest.test_check_controller_survives_owner_deletion_during_a_request_or_a_pause'
NULL_ADDRESS_DIALOG_TEST = ('PropertyLocationDialogFlowTest.'
                            'test_check_treats_a_missing_cadastral_address_as_agreement_with_the_settlement')


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PLUGIN, 'tests', name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def no_context(**_kwargs):
    return contextlib.nullcontext()


scenario = sys.argv[1]
if scenario == 'old_controller':
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyController as ctl

    def old_forward(self, _worker, signal_name, *args):
        getattr(self, signal_name).emit(*args)

    def old_finished(self, _worker, summary):
        self._worker = None
        self._thread = None
        self.finished.emit(summary)

    patches = [patch.object(ctl.BackendVerifyController, '_forward', old_forward),
               patch.object(ctl.BackendVerifyController, '_on_worker_finished', old_finished)]
    name = CONTROLLER_TEST
elif scenario == 'worker_without_context':
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as wk
    patches = [patch.object(wk, 'api_request_context', no_context)]
    name = CONTROLLER_TEST
elif scenario == 'dialog_without_wait_notice':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as wk
    patches = [patch.object(wk, 'api_request_context', no_context)]
    name = DIALOG_TEST
elif scenario == 'dialog_cancel_closes':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog

    def old_cancel(self):
        self._stop_attention_checks(clear_attention=False)
        self.reject()

    patches = [patch.object(AddPropertyDialog, '_on_cancel_clicked', old_cancel)]
    name = DIALOG_TEST
elif scenario == 'dialog_lookup_cancel_closes':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog

    def cancel_without_lookup_branch(self):
        if self._checks_running:
            self._cancel_attention_checks()
            return
        self._stop_attention_checks(clear_attention=False)
        if self._add_runner is not None:
            self._add_runner.cancel()
            return
        self.reject()

    patches = [patch.object(AddPropertyDialog, '_on_cancel_clicked', cancel_without_lookup_branch)]
    name = ('PropertyLocationDialogFlowTest.'
            'test_real_dialog_archive_lookup_shows_progress_and_cancel_changes_nothing')
elif scenario == 'dialog_lookup_without_scope_recheck':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
    original_apply = AddPropertyDialog._apply_archive_plan

    def apply_without_recheck(self, missing, backend_info, then):
        with patch.object(self, '_archive_scope_is_current', return_value=True):
            original_apply(self, missing, backend_info, then)

    patches = [patch.object(AddPropertyDialog, '_apply_archive_plan', apply_without_recheck)]
    name = ('PropertyLocationDialogFlowTest.'
            'test_real_dialog_rechecks_the_archive_scope_after_the_background_lookup')
elif scenario == 'controller_thread_parented':
    # Expected outcome is a Qt abort: a running thread is destroyed with its parent.
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyController as ctl
    original_start = ctl.BackendVerifyController.start

    def start_with_parented_thread(self, *args, **kwargs):
        original_start(self, *args, **kwargs)
        self._thread.setParent(self)

    patches = [patch.object(ctl.BackendVerifyController, 'start', start_with_parented_thread)]
    name = OWNER_DELETION_TEST
elif scenario == 'controller_no_stop_on_destroy':
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyController as ctl
    patches = [patch.object(ctl.BackendVerifyController, 'stop', lambda self: None)]
    name = OWNER_DELETION_TEST
elif scenario == 'controller_eager_signal_lookup':
    # Expected outcome is a Qt abort: the lambda reads a signal of the deleted controller.
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyController as ctl

    def forward_signal_object(self, worker, signal, *args):
        if self._is_current(worker):
            signal.emit(*args)

    def start_reading_signals_early(self, rows, *, source, import_context_by_tunnus):
        self.stop()
        worker = ctl.BackendVerifyWorker(rows, source=source, import_context_by_tunnus=import_context_by_tunnus)
        worker.rowResult.connect(
            lambda row, tunnus, result, w=worker: self._forward(w, self.rowResult, row, tunnus, result))
        worker.waiting.connect(lambda seconds, reason, w=worker: self._forward(w, self.waiting, seconds, reason))
        worker.finished.connect(lambda summary, w=worker: self._on_worker_finished(w, summary))
        self._worker = worker
        self._thread = ctl.start_worker(worker)

    patches = [patch.object(ctl.BackendVerifyController, '_forward', forward_signal_object),
               patch.object(ctl.BackendVerifyController, 'start', start_reading_signals_early)]
    name = OWNER_DELETION_TEST
elif scenario == 'old_address_comparison':
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import property_import_decisions as decisions

    def exact_display_match(display_address, street, full_street):
        return str(display_address or '').strip() in (street, full_street)

    patches = [patch.object(decisions, '_address_matches', exact_display_match)]
    name = 'CheckedPropertyAddTest.test_composed_backend_address_matches_the_cadastral_address'
elif scenario == 'dialog_check_without_decisions':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
    patches = [patch.object(AddPropertyDialog, '_collect_check_decisions', lambda self: [])]
    name = ('PropertyLocationDialogFlowTest.'
            'test_check_offers_decisions_before_adding_and_apply_takes_the_current_layers')
elif scenario == 'verify_by_tag_only':
    tests = load('test_property_archive_execution')
    from Kavitro_dev.modules.Property.FlowControllers import MainAddProperties as flow

    patches = [patch.object(flow.BackendPropertyVerifier, '_is_archived',
                            lambda node: flow.BackendPropertyVerifier._is_archived_by_tag(node))]
    name = 'PropertyArchiveExecutionTest.test_verify_splits_records_by_status_with_one_query'
elif scenario == 'status_update_guessing':
    tests = load('test_property_archive_execution')
    from Kavitro_dev.modules.Property.FlowControllers import UpdatePropertyData as update_module

    def old_status_update(item_id, *, status_name):
        item_id = str(item_id or '').strip()
        status_name = str(status_name or '').strip().upper()
        mutation = update_module.GraphQLQueryLoader().load_query_by_module(
            module=update_module.Module.PROPERTY.name, query_filename='UpdateProperty.graphql')
        client = update_module.APIClient()
        for payload in ({'id': item_id, 'status': status_name},
                        {'id': item_id, 'status': status_name.lower()}):
            try:
                client.send_query(mutation, {'input': payload})
                return True
            except Exception:
                continue
        return False

    patches = [patch.object(update_module.UpdatePropertyData, '_set_backend_property_status',
                            old_status_update)]
    name = 'PropertyArchiveExecutionTest.test_archive_status_uses_the_documented_status_field'
elif scenario == 'old_address_split':
    tests = load('test_property_location_rules')
    from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
    import re as _re

    def split_at_first_digit(street):
        data = {}
        match = _re.search(r'\d', street)
        if match:
            data['street'] = street[:match.start()].strip()
            data['house'] = street[match.start():].strip()
        else:
            data['street'] = street.strip()
        return data

    patches = [patch.object(PropertyDataLoader, 'get_address_details_from_street', split_at_first_digit)]
    name = 'PropertyLocationRulesTest.test_address_split_separates_only_a_trailing_house_number'
elif scenario == 'dialog_without_column_tooltips':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog

    patches = [patch.object(AddPropertyDialog, '_column_tooltip',
                            lambda self, causes, done, ok_key, issues_key: '')]
    name = 'PropertyLocationDialogFlowTest.test_each_status_column_explains_itself_on_hover'
elif scenario == 'county_read_without_choices':
    tests = load('test_property_location_filter')
    from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
    original_scope_read = PropertyDataLoader.read_location_scope

    def scope_read_without_tree(source, cancelled, scope, include_properties):
        result = original_scope_read(source, cancelled, scope, include_properties)
        if result is not None:
            result['tree'] = None
        return result

    patches = [patch.object(PropertyDataLoader, 'read_location_scope', scope_read_without_tree)]
    name = 'PropertyLocationFilterTest.test_hierarchy_is_scoped_and_cached_between_choices'
elif scenario == 'null_address_compared_as_street':
    tests = load('test_checked_property_add')
    from Kavitro_dev.modules.Property.FlowControllers import property_import_decisions as decisions

    def street_only(display_address, street, full_street, location=''):
        parts = [part for part in (s.strip() for s in str(display_address or '').split(',')) if part]
        shown = {decisions._normalize(display_address), decisions._normalize(parts[0] if parts else ''),
                 decisions._normalize(' '.join(parts[:2]))}
        return decisions._normalize(street) in shown or decisions._normalize(full_street) in shown

    patches = [patch.object(decisions, '_address_matches', street_only)]
    name = 'CheckedPropertyAddTest.test_missing_cadastral_address_is_agreement_unless_the_backend_has_a_street'
elif scenario == 'null_address_generic_reason':
    tests = load('test_checked_property_add')
    from Kavitro_dev.languages.translation_keys import TranslationKeys as K
    from Kavitro_dev.modules.Property.FlowControllers import property_import_decisions as decisions
    from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as runner_module
    original_classify = decisions.classify_property_import

    def generic_reason(*args, **kwargs):
        result = original_classify(*args, **kwargs)
        if result['reason'] == K.PROPERTY_IMPORT_ADDRESS_MISSING:
            result['reason'] = K.PROPERTY_ADD_BACKEND_DIFFERS
        return result

    patches = [patch.object(decisions, 'classify_property_import', generic_reason),
               patch.object(runner_module, 'classify_property_import', generic_reason)]
    name = 'CheckedPropertyAddTest.test_missing_cadastral_address_is_agreement_unless_the_backend_has_a_street'
elif scenario == 'null_address_not_approvable':
    tests = load('test_checked_property_add')
    from Kavitro_dev.languages.translation_keys import TranslationKeys as K
    from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as runner_module
    from Kavitro_dev.widgets import property_import_review_dialog as review_module
    only_differs = (K.PROPERTY_ADD_BACKEND_DIFFERS,)
    patches = [patch.object(runner_module, 'ADDRESS_REASONS', only_differs),
               patch.object(review_module, 'ADDRESS_REASONS', only_differs)]
    name = 'CheckedPropertyAddTest.test_missing_address_decision_offers_and_applies_the_import_only_when_approved'
elif scenario == 'null_address_approval_without_runner':
    tests = load('test_checked_property_add')
    from Kavitro_dev.languages.translation_keys import TranslationKeys as K
    from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as runner_module
    patches = [patch.object(runner_module, 'ADDRESS_REASONS', (K.PROPERTY_ADD_BACKEND_DIFFERS,))]
    name = 'CheckedPropertyAddTest.test_missing_address_decision_offers_and_applies_the_import_only_when_approved'
elif scenario == 'dialog_check_without_location':
    # Old behaviour: "Run check" sent only street and house number, so a cadastral unit
    # without an address could not agree with the settlement the import would send.
    # Rewritten for the current seam: the per-row location parts used to be read by
    # `AddPropertyDialog._check_location_parts`, which step 8 replaced with the shared
    # `PropertyDataLoader.build_import_address` that check and import now both use.
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
    original_build_address = PropertyDataLoader.build_import_address

    def address_without_location_parts(feature):
        full = original_build_address(feature)
        return {'street': full['street'], 'houseNumber': full.get('houseNumber', '')}

    patches = [patch.object(PropertyDataLoader, 'build_import_address',
                            staticmethod(address_without_location_parts))]
    name = NULL_ADDRESS_DIALOG_TEST
elif scenario == 'dialog_main_address_null_text':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
    from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F

    def old_collect(self):
        # Old behaviour: the main-layer address went through a plain str(), so an empty
        # one reached the review as the text NULL instead of as nothing.
        run = self._check_run
        if run is None:
            return []
        result = []
        for _row_idx, decision, feature in run.decisions_in_row_order():
            if not isinstance(decision, dict) or decision.get('action') != 'needs_decision':
                continue
            main = run.main_layer_lookup.get(str(decision.get('tunnus') or ''))
            result.append(dict(decision, fid=feature.id() if feature is not None else None,
                               main_address=(str(main[F.l_aadress]) if main is not None
                                             and main.fields().lookupField(F.l_aadress) >= 0 else '')))
        return result

    patches = [patch.object(dialog_module.AddPropertyDialog, '_collect_check_decisions', old_collect)]
    name = NULL_ADDRESS_DIALOG_TEST
elif scenario == 'dialog_null_reason_without_tooltip':
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.modules.Property.FlowControllers import AttentionDisplayRules as rules_module
    original_translate = rules_module.AttentionDisplayRules._translate_cause_text

    def without_new_key(cause, translate=None):
        if str(cause) == rules_module.TranslationKeys.PROPERTY_IMPORT_ADDRESS_MISSING:
            return str(cause)
        return original_translate(cause, translate=translate)

    patches = [patch.object(rules_module.AttentionDisplayRules, '_translate_cause_text', staticmethod(without_new_key))]
    name = NULL_ADDRESS_DIALOG_TEST

# ---------------------------------------------------------------------------
# Maintenance step 3: session expiry is noticed, reported and recovered on every
# thread. Three separate guarantees, one mutant each.
# ---------------------------------------------------------------------------
elif scenario == 'session_worker_thread_not_invalidated':
    # Old behaviour: `send_query` guarded its 401 handling with `is_main_thread`, so a
    # worker never invalidated the session. The guard was an inline condition with no
    # seam of its own, so it is restored at the call boundary instead.
    tests = load('test_session_expiry')
    from Kavitro_dev.python import api_client as api_client_module
    original_send_query = api_client_module.APIClient.send_query

    def send_query_without_worker_invalidation(self, *args, **kwargs):
        from PyQt5.QtCore import QThread
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        on_main_thread = app is None or QThread.currentThread() == app.thread()
        if on_main_thread:
            return original_send_query(self, *args, **kwargs)
        with patch.object(api_client_module.SessionManager, 'invalidate_session',
                          lambda *a, **k: None):
            return original_send_query(self, *args, **kwargs)

    patches = [patch.object(api_client_module.APIClient, 'send_query',
                            send_query_without_worker_invalidation)]
    name = 'BackgroundThreadInvalidationTest.test_worker_thread_401_also_invalidates_session'
elif scenario == 'session_cancel_silences_user_login':
    # Old behaviour: `request_login` had no `user_initiated` flag, so one cancelled
    # prompt silenced that reason forever -- including a login the user asked for.
    tests = load('test_session_expiry')
    from Kavitro_dev.utils import SessionManager as session_module
    original_request_login = session_module.SessionManager.request_login

    def request_login_ignoring_user_intent(parent=None, reason=None, user_initiated=False):
        return original_request_login(parent, reason, user_initiated=False)

    patches = [patch.object(session_module.SessionManager, 'request_login',
                            staticmethod(request_login_ignoring_user_intent))]
    name = 'LoginPromptSuppressionTest.test_user_initiated_prompt_survives_cancel'
elif scenario == 'session_error_by_english_substring':
    # Old behaviour: the Settings page matched English substrings against a message
    # built from a translated key, so an Estonian expiry message read as "not auth".
    tests = load('test_session_expiry')
    from Kavitro_dev.modules.Settings import SettingsUI as settings_ui_module

    def old_is_session_error(message):
        text = str(message or '').lower()
        return any(marker in text for marker in
                   ('unauthenticated', 'unauthorized', 'session expired', 'invalid token'))

    patches = [patch.object(settings_ui_module.SettingsModule, '_is_session_error_message',
                            staticmethod(old_is_session_error))]
    name = 'LocalizedSessionErrorTest.test_estonian_expiry_message_is_recognised'

# ---------------------------------------------------------------------------
# Maintenance step 4 (bug b1): the add dialog with no import layer.
# ---------------------------------------------------------------------------
elif scenario == 'dialog_without_missing_layer_bailout':
    # Old behaviour: no early bail-out -- the full UI was built with no import layer,
    # which raised AttributeError instead of showing a message and a Close button.
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog

    def build_full_ui_anyway(self):
        self._create_ui()

    patches = [patch.object(AddPropertyDialog, '_build_missing_import_layer_ui', build_full_ui_anyway)]
    name = 'PropertyLocationDialogFlowTest.test_add_dialog_missing_import_layer_shows_close_only'

# ---------------------------------------------------------------------------
# Maintenance step 5: NULL-safe attribute reading.
# ---------------------------------------------------------------------------
elif scenario == 'attribute_read_leaks_null_text':
    # Old `_safe_attr`: only Python None was handled, so the QGIS NULL sentinel and a
    # literal "NULL" in the source file both reached the user as the word NULL.
    tests = load('test_property_row_builder_null_handling')
    from Kavitro_dev.utils.mapandproperties.property_row_builder import PropertyRowBuilder

    def old_safe_attr(value):
        return '' if value is None else str(value).strip()

    patches = [patch.object(PropertyRowBuilder, 'read_value', staticmethod(old_safe_attr))]
    name = ('PropertyRowBuilderNullHandlingTest.'
            'test_qgis_null_reads_as_empty_text_not_the_word_null')

# ---------------------------------------------------------------------------
# Maintenance step 6 (bug b5): plan and execution must agree on the main layer.
# ---------------------------------------------------------------------------
elif scenario == 'archive_reresolves_main_layer_by_name':
    # Old behaviour: `_prepare_layers` always looked the main layer up by name, so the
    # archive could act on a different instance than the plan was computed against.
    tests = load('test_property_archive_execution')
    from Kavitro_dev.modules.Property.FlowControllers import MainAddProperties as flow
    original_prepare_layers = flow.MainAddPropertiesFlow._prepare_layers

    def prepare_layers_by_name_only(main_layer=None):
        return original_prepare_layers(None)

    patches = [patch.object(flow.MainAddPropertiesFlow, '_prepare_layers',
                            staticmethod(prepare_layers_by_name_only))]
    name = 'PropertyArchiveExecutionTest.test_archive_uses_the_exact_main_layer_the_plan_was_built_on'

# ---------------------------------------------------------------------------
# Maintenance step 7: the dialog's button rules live in one place.
# ---------------------------------------------------------------------------
elif scenario == 'add_without_checks_not_busy_gated':
    # Old behaviour: the "add without checks" rule was duplicated per method and one
    # copy left out the busy gate, so the button stayed live during a running add.
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.utils.mapandproperties import property_dialog_phase as phase_module

    patches = [patch.object(phase_module.PropertyDialogState, 'can_add_without_checks',
                            property(lambda self: self.selected_count > 0))]
    name = ('PropertyLocationDialogFlowTest.'
            'test_button_rules_hold_for_every_phase_with_and_without_rows')

# ---------------------------------------------------------------------------
# Maintenance step 8 (bug b6): the filter must not throw the finished check away.
# ---------------------------------------------------------------------------
elif scenario == 'filter_untick_drops_the_check':
    # Old behaviour: the filter deleted rows, so unticking had to reload the table,
    # which ran _after_table_update -> _stop_attention_checks and dropped the run.
    tests = load('test_property_location_dialog_flow')
    from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module

    def clear_filter_by_reloading(self):
        dialog_module.PropertyTableManager.show_all_rows(self.properties_table)
        self._table_filtered_to_attention = False
        # What the reload did: _after_table_update -> _stop_attention_checks dropped the
        # finished run with its decisions. Spelled out rather than called, because
        # _stop_attention_checks clears the filter again and would recurse.
        self._check_run = None
        self._checks_completed_for_scope = False
        self._deferred_additions = []

    patches = [patch.object(dialog_module.AddPropertyDialog, '_clear_attention_filter',
                            clear_filter_by_reloading)]
    name = ('PropertyLocationDialogFlowTest.'
            'test_turning_the_attention_filter_off_keeps_the_finished_check_result')
elif scenario == 'check_run_replaced_still_accepts':
    # Old behaviour: a replaced run had no way to refuse results, so a controller
    # signal already queued painted onto the run that replaced it.
    tests = load('test_property_check_run')
    from Kavitro_dev.utils.mapandproperties.property_check_run import PropertyCheckRun

    patches = [patch.object(PropertyCheckRun, 'accepts', lambda self: True)]
    name = 'PropertyCheckRunTest.test_a_replaced_run_sends_nothing_and_keeps_its_own_results'
elif scenario == 'check_run_finishes_more_than_once':
    # Old behaviour: completion was a plain flag, so the end of a run could be
    # announced more than once (and for a cancelled run).
    tests = load('test_property_check_run')
    from Kavitro_dev.utils.mapandproperties.property_check_run import PropertyCheckRun

    patches = [patch.object(PropertyCheckRun, 'mark_finished', lambda self: True)]
    name = 'PropertyCheckRunTest.test_completion_is_announced_exactly_once'
else:
    raise SystemExit(f'unknown scenario {scenario}')

if os.environ.get('KEEP_DIALOG') == '1' and scenario.startswith('dialog'):
    # Deleting the dialog destroys its still-running check QThread, which aborts Qt
    # before the verdict is printed. Keep it alive until the hard exit below.
    from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
    patches.append(patch.object(AddPropertyDialog, 'deleteLater', lambda self: None))

suite = unittest.defaultTestLoader.loadTestsFromName(name, tests)
with contextlib.ExitStack() as stack:
    for item in patches:
        stack.enter_context(item)
    result = unittest.TextTestRunner(stream=open(os.devnull, 'w')).run(suite)

verdict = 'FAILED_AS_EXPECTED' if not result.wasSuccessful() else 'UNEXPECTEDLY_PASSED'
print('SCENARIO', scenario, verdict)
for _test, trace in result.failures + result.errors:
    print('  ', trace.strip().splitlines()[-1][:200])
sys.stdout.flush()
# Old behaviour can leave a worker blocked in a 30 s wait; do not hang on shutdown.
os._exit(0)
