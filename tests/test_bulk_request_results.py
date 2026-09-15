import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from qgis.core import QgsApplication
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.Property.FlowControllers import BackendPropertyActions as backend
from Kavitro_dev.modules.Property.FlowControllers import MainDeleteProperties as deletion
from Kavitro_dev.python.api_rate_limit import RequestCancelled
from Kavitro_dev.utils.mapandproperties import property_action_service as actions
from Kavitro_dev.widgets.DataDisplayWidgets import TaskFilesDialog as files


class BulkRequestResultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_upload_failure_stops_before_next_file_and_refreshes_actual_list(self):
        dialog = SimpleNamespace(_module_name='works', _item_id='task-1',
                                 _lang=LanguageManager(), _load_files=Mock())
        with patch.object(files.QFileDialog, 'getOpenFileNames', return_value=(['a.txt', 'b.txt', 'c.txt'], '')), \
                patch.object(files.APIModuleActions, 'upload_module_file', side_effect=[{'uuid': 'a'}, None, {'uuid': 'c'}]) as upload, \
                patch.object(files.ModernMessageDialog, 'show_warning') as warning, \
                patch.object(files.ModernMessageDialog, 'show_info') as success:
            files.TaskFilesDialog._upload_files(dialog)
        self.assertEqual(upload.call_count, 2)
        self.assertIn('b.txt', warning.call_args.args[1])
        self.assertIn('c.txt', warning.call_args.args[1])
        dialog._load_files.assert_called_once()
        success.assert_not_called()

    def test_archive_and_restore_stop_on_failed_item_and_report_pending(self):
        for action, helper in (('archive', '_archive_a_propertie'), ('unarchive', '_unarchive_property_data')):
            with self.subTest(action=action), \
                    patch.object(backend.TagsHelpers, 'check_if_tag_exists', return_value='tag'), \
                    patch.object(backend.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                                 return_value={'exists': True, 'active_count': 1, 'property': {'id': 'id'}, 'archived_ids': ['id']}), \
                    patch.object(backend.UpdatePropertyData, helper, side_effect=[True, False, True]) as update:
                if action == 'archive':
                    summary = backend.BackendPropertyActions.archive_properties_by_tunnused(
                        ['T1', 'T2', 'T3'], archive_tag_name='archived', module_name='property')
                else:
                    summary = backend.BackendPropertyActions.unarchive_properties_by_tunnused(['T1', 'T2', 'T3'])
            self.assertEqual(update.call_count, 2)
            self.assertEqual((summary['succeeded'], summary['failed'], summary['pending']), (1, 1, ['T3']))

    def test_uncertain_backend_delete_never_deletes_map_features_or_next_property(self):
        with patch.object(backend.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          return_value={'exists': True, 'active_count': 1, 'property': {'id': 'id'}}), \
                patch.object(backend.deleteProperty, 'delete_single_item', side_effect=[(True, ''), (False, 'Unconfirmed'), (True, '')]) as delete, \
                patch.object(actions.FeatureActions, 'delete_features_by_field_values') as delete_map, \
                patch.object(actions.PythonFailLogger, 'log_exception'):
            result = actions.PropertyActionService.run_action('delete', ['T1', 'T2', 'T3'], main_layer=object())
        self.assertFalse(result.ok)
        self.assertEqual(delete.call_count, 2)
        delete_map.assert_not_called()
        self.assertIn('T2', result.message)
        self.assertIn('T3', result.message)

    def test_delete_requires_matching_server_id_and_handles_cancel_as_failure(self):
        for data, succeeds in (({'id': 'id'}, True), ({}, False), ({'id': 'other'}, False)):
            with self.subTest(data=data), patch.object(deletion.APIClient, 'send_query', return_value={
                    'success': True, 'raw': {'data': {'deleteProperty': data}}}):
                ok, message = deletion.deleteProperty.delete_single_item('id')
            self.assertEqual(ok, succeeds)
        with patch.object(deletion.APIClient, 'send_query', side_effect=RequestCancelled()):
            ok, message = deletion.deleteProperty.delete_single_item('id')
        self.assertFalse(ok)
        self.assertTrue(message)


if __name__ == '__main__':
    unittest.main()
