"""The check run on its own: no dialog, no table, no event loop.

These are the rules a dialog field could not enforce and that only showed up as symptoms
before: a run that was replaced went on writing into the fields the new run had just
filled, and a cancelled run could still reach the code that announces a finished check.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.utils.mapandproperties.property_check_run import CheckRow, PropertyCheckRun


def make_run(*tunnused: str, run_id: int = 1) -> PropertyCheckRun:
    rows = [CheckRow(row=index, tunnus=tunnus, import_muudet='2026-01-01', feature='f' + tunnus)
            for index, tunnus in enumerate(tunnused)]
    return PropertyCheckRun(rows, run_id=run_id)


class PropertyCheckRunTest(unittest.TestCase):
    def test_a_run_is_complete_only_when_both_checks_answered_for_every_row(self):
        run = make_run('1', '2')
        self.assertEqual((run.total, run.done_count(), run.is_complete), (2, 0, False))

        run.record_backend(0, ['missing in backend'], {'action': 'needs_decision'})
        run.record_backend(1, [], None)
        self.assertEqual((run.done_count(), run.is_complete), (0, False))

        run.record_main(0, ['missing in main layer'])
        self.assertEqual((run.done_count(), run.is_complete), (1, False))

        run.record_main(1, [])
        self.assertEqual((run.done_count(), run.is_complete), (2, True))

    def test_an_empty_run_is_never_complete(self):
        run = PropertyCheckRun([])
        self.assertEqual(run.total, 0)
        self.assertFalse(run.is_complete)

    def test_results_and_progress_read_back_per_row(self):
        run = make_run('1', '2')
        run.record_backend(0, ['  backend lookup failed  ', '', '   '], {'action': 'skip'})
        run.record_main(1, ['main layer older'])

        self.assertEqual(run.causes_for_row(0), ([], ['backend lookup failed']))
        self.assertEqual(run.done_for_row(0), (False, True))
        self.assertEqual(run.causes_for_row(1), (['main layer older'], []))
        self.assertEqual(run.done_for_row(1), (True, False))
        self.assertEqual(run.unchecked_main_rows(), [0])
        self.assertEqual(run.tunnus_for_row(1), '2')

    def test_a_replaced_run_sends_nothing_and_keeps_its_own_results(self):
        """The old run is cancelled the moment a new one starts; its late signals stop here."""

        old = make_run('1', '2', run_id=1)
        old.record_backend(0, ['missing in backend'], {'action': 'needs_decision'})
        new = make_run('1', '2', run_id=2)

        old.cancel()

        # Everything a late controller signal could still call is refused.
        self.assertFalse(old.record_backend(1, ['import newer'], {'action': 'add'}))
        self.assertFalse(old.record_main(1, ['main layer older']))
        self.assertFalse(old.mark_backend_all_checked())
        self.assertFalse(old.mark_finished())

        # The old run changed neither itself nor the run that replaced it.
        self.assertEqual(old.causes_for_row(1), ([], []))
        self.assertEqual(old.done_count(), 0)
        self.assertEqual(old.causes_for_row(0), ([], ['missing in backend']))
        self.assertEqual((new.done_count(), new.backend_causes, new.main_causes), (0, {}, {}))

        # The new run is unaffected by any of it.
        self.assertTrue(new.record_backend(1, ['import newer'], {'action': 'add'}))
        self.assertTrue(new.record_main(1, []))
        self.assertEqual(new.causes_for_row(1), ([], ['import newer']))

    def test_a_cancelled_run_never_reports_completion(self):
        run = make_run('1')
        run.record_backend(0, [], None)
        run.record_main(0, [])
        self.assertTrue(run.is_complete)

        run.cancel()

        # Complete on paper, but cancelled: the finished signal must never go out.
        self.assertTrue(run.is_complete)
        self.assertFalse(run.mark_finished())
        self.assertFalse(run.finished)

    def test_completion_is_announced_exactly_once(self):
        run = make_run('1')
        run.record_backend(0, [], None)
        run.record_main(0, [])

        self.assertTrue(run.mark_finished())
        self.assertFalse(run.mark_finished())

        # A finished run is closed for results too, so a late row cannot reopen it.
        self.assertFalse(run.record_main(0, ['main layer older']))
        self.assertEqual(run.causes_for_row(0), ([], []))

    def test_a_row_outside_the_run_is_refused(self):
        run = make_run('1')
        self.assertFalse(run.record_backend(7, ['missing in backend'], None))
        self.assertFalse(run.record_main(7, ['main layer older']))
        self.assertEqual(run.done_count(), 0)

    def test_a_failed_backend_start_leaves_completion_to_the_main_checks(self):
        run = make_run('1', '2')
        self.assertTrue(run.mark_backend_all_checked())
        self.assertFalse(run.is_complete)

        run.record_main(0, [])
        run.record_main(1, [])
        self.assertTrue(run.is_complete)

    def test_decisions_come_back_in_table_order_with_the_features_the_run_captured(self):
        run = make_run('1', '2', '3')
        run.record_backend(2, [], {'tunnus': '3'})
        run.record_backend(0, [], {'tunnus': '1'})

        self.assertEqual(run.decisions_in_row_order(),
                         [(0, {'tunnus': '1'}, 'f1'), (2, {'tunnus': '3'}, 'f3')])

    def test_the_scope_is_handed_to_the_controllers_in_their_own_shapes(self):
        run = make_run('1', '2')
        self.assertEqual(run.rows_for_verify_by_row(),
                         {0: ('1', '2026-01-01'), 1: ('2', '2026-01-01')})
        self.assertEqual(run.controller_rows(),
                         [(0, '1', '2026-01-01'), (1, '2', '2026-01-01')])
        self.assertEqual(run.tunnused(), {'1', '2'})
        self.assertEqual(run.row_indices(), (0, 1))


if __name__ == '__main__':
    unittest.main()
