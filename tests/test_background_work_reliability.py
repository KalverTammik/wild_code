from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtTest import QTest
from qgis.core import QgsApplication

from property_fixtures import wait_until as _wait_until

from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
from Kavitro_dev.modules.Property.FlowControllers.BackendVerifyWorker import BackendVerifyWorker
from Kavitro_dev.modules.Property.FlowControllers.MainLayerCheckController import MainLayerCheckController


class _QtTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()

    def wait_until(self, condition, *, message='background work did not complete'):
        _wait_until(self, condition, attempts=200, message=message)


class BackendVerifyWorkerFinishTest(_QtTestCase):
    """The worker must always report the end of its run, whatever a single row does."""

    def context(self, *tunnused):
        return {tunnus: {'data': {'cadastralUnit': {'number': tunnus}, 'address': {}}, 'main_date': None}
                for tunnus in tunnused}

    def run_worker(self, worker):
        results, finished = [], []
        worker.rowResult.connect(lambda row, tunnus, result: results.append((tunnus, result)))
        worker.finished.connect(finished.append)
        worker.run()
        return results, finished

    def test_a_decision_that_raises_still_finishes_the_run_and_keeps_the_other_rows(self):
        # The decision of the first row raises. Before the fix the exception left `run`
        # through the rate-limit context, so `finished` never arrived: the dialog's own
        # state stayed "busy" and its buttons stayed locked until the user cancelled.
        worker = BackendVerifyWorker([(0, '1', '2025-01-01'), (1, '2', '2025-01-01')],
                                     source='test', import_context_by_tunnus=self.context('1', '2'))
        real_classify = worker_module.classify_property_import

        def flaky(data, import_muudet, main_date, backend_info):
            if (data.get('cadastralUnit') or {}).get('number') == '1':
                raise RuntimeError('decision boom')
            return real_classify(data, import_muudet, main_date, backend_info)

        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          return_value={'exists': False}), \
                patch.object(worker_module, 'classify_property_import', side_effect=flaky), \
                patch.object(worker_module.PythonFailLogger, 'log_exception') as logged:
            results, finished = self.run_worker(worker)

        self.assertEqual(len(finished), 1)
        self.assertFalse(finished[0]['stopped'])
        # The undecidable row is reported as needing attention instead of killing the run.
        self.assertEqual([tunnus for tunnus, _result in results], ['1', '2'])
        self.assertEqual(results[0][1]['causes'], [K.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED])
        self.assertTrue(results[0][1]['attention'])
        self.assertEqual([error['tunnus'] for error in finished[0]['errors']], ['1'])
        self.assertIn('decision boom', finished[0]['errors'][0]['error'])
        # The second row keeps its normal verdict.
        self.assertEqual(finished[0]['missing_backend'], ['2'])
        self.assertEqual(logged.call_args.kwargs['event'], 'backend_verify_decision_failed')


class ArchivePlanLookupModeTest(_QtTestCase):
    """The archive plan needs the backend answer only, not an invented import row."""

    def test_lookup_mode_reads_the_backend_answer_without_any_import_context(self):
        worker = BackendVerifyWorker([(0, '7', ''), (1, '8', '')], source='archive_plan',
                                     mode=BackendVerifyWorker.MODE_LOOKUP)
        infos = {'7': {'exists': True, 'active_ids': ['p7']}, '8': {'exists': False}}
        results, finished = [], []
        worker.rowResult.connect(lambda row, tunnus, result: results.append((tunnus, result)))
        worker.finished.connect(finished.append)
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lambda number: infos[number]), \
                patch.object(worker_module, 'classify_property_import') as classify:
            worker.run()

        # No decision is computed, so no fabricated import data can reach one.
        classify.assert_not_called()
        self.assertEqual([tunnus for tunnus, _result in results], ['7', '8'])
        self.assertEqual([result['backend_info'] for _tunnus, result in results], [infos['7'], infos['8']])
        self.assertEqual([result['causes'] for _tunnus, result in results], [[], []])
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]['source'], 'archive_plan')

    def test_verify_mode_still_needs_and_uses_the_real_import_context(self):
        context = {'1': {'data': {'cadastralUnit': {'number': '1'}, 'address': {'street': 'Tee'}},
                         'main_date': '2020-01-01'}}
        worker = BackendVerifyWorker([(0, '1', '2025-01-01')], source='test',
                                     import_context_by_tunnus=context)
        results, finished = [], []
        worker.rowResult.connect(lambda row, tunnus, result: results.append(result))
        worker.finished.connect(finished.append)
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          return_value={'exists': False}):
            worker.run()
        self.assertEqual(results[0]['decision']['action'], 'create')
        self.assertEqual(finished[0]['missing_backend'], ['1'])

    def test_verify_mode_without_an_import_context_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            BackendVerifyWorker([(0, '1', '')], source='test')


class MainLayerCheckTimerTest(_QtTestCase):
    """A restarted check cycle must not leave a second timer running behind it."""

    def controller(self, rows):
        controller = MainLayerCheckController()
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.stop)
        controller.configure(rows_for_verify_by_row={row: (f'T{row}', '') for row in rows},
                             main_layer=None)
        return controller

    def test_restarting_the_same_cycle_reports_the_end_exactly_once(self):
        # This is the reported sequence: the backend check fails to start, so the caller
        # begins the MAIN check a second time inside the same cycle. Before the fix the
        # first run's timer stayed alive and kept emitting `finished` after every tick.
        rows = list(range(40))
        controller = self.controller(rows)
        finished, results = [], []
        controller.finished.connect(lambda: finished.append(1))
        controller.rowResult.connect(lambda row, causes: results.append(row))

        controller.start_pending(rows, batch_size=10)
        controller.start_pending(rows, batch_size=10)

        self.wait_until(lambda: len(results) >= len(rows))
        # Anything the stale timer would still post has to be delivered before counting.
        QTest.qWait(150)
        QCoreApplication.processEvents()

        self.assertEqual(len(finished), 1)
        self.assertEqual(sorted(results), rows)

    def test_a_stopped_run_stays_silent_and_a_later_run_reports_its_own_end(self):
        rows = list(range(30))
        controller = self.controller(rows)
        finished = []
        controller.finished.connect(lambda: finished.append(1))

        controller.start_pending(rows, batch_size=5)
        controller.stop()
        QTest.qWait(100)
        QCoreApplication.processEvents()
        self.assertEqual(finished, [])

        controller.start_pending(rows, batch_size=5)
        self.wait_until(lambda: len(finished) == 1)
        QTest.qWait(100)
        QCoreApplication.processEvents()
        self.assertEqual(len(finished), 1)

    def test_an_empty_run_reports_the_end_once_without_starting_a_timer(self):
        controller = self.controller([])
        finished = []
        controller.finished.connect(lambda: finished.append(1))
        controller.start_pending([])
        QTest.qWait(100)
        QCoreApplication.processEvents()
        self.assertEqual(len(finished), 1)

    def test_the_row_batches_never_pump_the_event_loop_themselves(self):
        # Re-entering the event loop from inside the check is what let the user act on a
        # dialog that was supposed to be locked; the batches must not do it.
        rows = list(range(30))
        controller = self.controller(rows)
        finished = []
        controller.finished.connect(lambda: finished.append(1))
        with patch.object(QCoreApplication, 'processEvents') as pumped:
            controller.start_pending(rows, batch_size=5)
            self.wait_until(lambda: len(finished) == 1)
            controller.ensure_row(99)
        pumped.assert_not_called()


if __name__ == '__main__':
    unittest.main()
