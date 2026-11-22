"""Settings "remove property" map flow and the table-to-map selection sync.

Pins the user-visible order of the remove flow's messages after it moved next to the
other Settings delete UI, and that the add dialog hands its selected table features to
the map helper.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication

from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.modules.Property.FlowControllers import property_remove_flow as flow_module
from Kavitro_dev.modules.Property.FlowControllers.property_action_service import (
    PropertyActionResult,
    PropertyActionService,
)
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.MapTools.item_selector_tools import PropertiesSelectors
sys.path.insert(0, str(Path(__file__).resolve().parent))
from property_fixtures import LocationFilterTestCase, close_dialog  # noqa: E402


class _FakeOrchestrator:
    """Stands in for the map selection tool; the test fires its callback by hand."""

    started = True

    def __init__(self, parent=None):
        self.parent = parent
        self.on_selected = None

    def start_selection_for_layer(self, layer, *, on_selected, **_kwargs):
        self.on_selected = on_selected
        return type(self).started


class _Feature:
    def __init__(self, fid):
        self._fid = fid

    def id(self):
        return self._fid


class SettingsRemoveFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self):
        self.events = []
        dialogs = flow_module.ModernMessageDialog
        self.patches = [
            patch.object(dialogs, 'Info_messages_modern',
                         side_effect=lambda title, message: self.events.append(('info', title, message))),
            patch.object(dialogs, 'Warning_messages_modern',
                         side_effect=lambda title, message: self.events.append(('warning', title, message))),
            patch.object(flow_module, 'MapSelectionOrchestrator', _FakeOrchestrator),
            patch.object(flow_module.PropertyRowBuilder, 'rows_from_features',
                         side_effect=lambda feats, log_prefix: [{'cadastral_id': f.cadastral} for f in feats]),
            patch.object(flow_module.PropertyPromptHelpers, 'prompt_backend_action',
                         side_effect=self._prompt),
            patch.object(PropertyActionService, 'run_action', side_effect=self._run_action),
        ]
        for item in self.patches:
            item.start()
        self.prompt_answer = 'archive'
        self.result = PropertyActionResult(ok=True, title='Done', message='All archived', action='archive')
        _FakeOrchestrator.started = True

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def _prompt(self, parent, rows, *, title):
        self.events.append(('prompt', title, [row['cadastral_id'] for row in rows]))
        return self.prompt_answer

    def _run_action(self, action, tunnused, *, main_layer, module_name):
        self.events.append(('run', action, list(tunnused), main_layer))
        return self.result

    def _start(self):
        return flow_module.PropertySelectionActionService.start_settings_remove_flow(
            parent=None,
            main_layer='main-layer',
            translate=lambda key: f'<{key}>',
            prompt_title='Pick action',
            on_restore_ui=lambda: self.events.append(('restore',)),
            on_minimize_ui=lambda: self.events.append(('minimize',)),
            on_flow_finished=lambda: self.events.append(('finished',)),
        )

    @staticmethod
    def _features(*numbers):
        features = []
        for number in numbers:
            feature = Mock()
            feature.cadastral = number
            features.append(feature)
        return features

    def test_selected_properties_run_the_chosen_action_and_report_it(self):
        orchestrator = self._start()
        self.assertEqual(self.events, [
            ('info', f'<{K.SELECT_PROPERTIES}>', f'<{K.SELECT_PROPERTIES_MAP_INSTRUCTION}>'),
            ('minimize',),
        ])
        self.events.clear()
        orchestrator.on_selected('layer', self._features('T1', 'T2', 'T1'))
        self.assertEqual(self.events, [
            ('restore',),
            ('prompt', 'Pick action', ['T1', 'T2', 'T1']),
            ('run', 'archive', ['T1', 'T2'], 'main-layer'),
            ('info', 'Done', 'All archived'),
            ('finished',),
        ])

    def test_failed_action_is_a_warning(self):
        self.result = PropertyActionResult(ok=False, title='Partly', message='1 failed', action='archive')
        self._start().on_selected('layer', self._features('T1'))
        self.assertEqual(self.events[-2:], [('warning', 'Partly', '1 failed'), ('finished',)])

    def test_empty_selection_says_so_and_runs_nothing(self):
        orchestrator = self._start()
        self.events.clear()
        orchestrator.on_selected('layer', [])
        self.assertEqual(self.events, [
            ('restore',),
            ('info', f'<{K.NO_SELECTION}>', f'<{K.MAP_SELECTION_NONE}>'),
            ('finished',),
        ])

    def test_cancelled_prompt_runs_nothing(self):
        self.prompt_answer = None
        orchestrator = self._start()
        self.events.clear()
        orchestrator.on_selected('layer', self._features('T1'))
        self.assertEqual(self.events, [('restore',), ('prompt', 'Pick action', ['T1']), ('finished',)])

    def test_selection_tool_that_does_not_start_warns_after_finishing(self):
        _FakeOrchestrator.started = False
        self.assertIsNone(self._start())
        self.assertEqual(self.events, [
            ('info', f'<{K.SELECT_PROPERTIES}>', f'<{K.SELECT_PROPERTIES_MAP_INSTRUCTION}>'),
            ('finished',),
            ('warning', f'<{K.SELECTION_FAILED_TITLE}>', f'<{K.MAP_SELECTION_START_FAILED}>'),
        ])


class ShowFeaturesOnMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_selects_each_feature_id_once(self):
        layer = object()
        with patch.object(PropertiesSelectors, '_resolve_property_layer', return_value=layer), \
                patch.object(MapHelpers, 'ensure_layer_visible') as visible, \
                patch.object(MapHelpers, 'select_features_by_ids') as select:
            result = PropertiesSelectors.show_features_on_map(
                [_Feature(3), _Feature(1), _Feature(3), object()], use_shp=True)
        self.assertIs(result, layer)
        visible.assert_called_once_with(layer, make_active=True)
        select.assert_called_once_with(layer, [3, 1], zoom=True)

    def test_no_features_leaves_the_map_alone(self):
        layer = object()
        with patch.object(PropertiesSelectors, '_resolve_property_layer', return_value=layer), \
                patch.object(MapHelpers, 'select_features_by_ids') as select:
            self.assertIs(PropertiesSelectors.show_features_on_map([], use_shp=True), layer)
        select.assert_not_called()


class AddDialogMapSyncTest(LocationFilterTestCase):
    def test_map_sync_timer_sends_the_selected_table_features(self):
        dialog = self.open_dialog_with_village_scope()
        try:
            # Location mode turns table selection off, so the selection read is stubbed.
            from Kavitro_dev.widgets.property_table.PropertyTableManager import PropertyTableManager
            expected = [_Feature(7)]
            with patch.object(PropertyTableManager, 'get_selected_features', return_value=expected) as read, \
                    patch.object(PropertiesSelectors, 'show_features_on_map') as show:
                dialog._map_update_timer.timeout.emit()
            read.assert_called_once_with(dialog.properties_table)
            show.assert_called_once_with(expected, use_shp=True)
        finally:
            close_dialog(self, dialog)


if __name__ == '__main__':
    unittest.main()
