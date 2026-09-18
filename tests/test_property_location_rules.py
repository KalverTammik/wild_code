from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtCore import QCoreApplication, QEvent, QThread, QTimer, Qt, QVariant
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialog, QPushButton, QTableView, QVBoxLayout, QWidget
from qgis.core import (QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVariantUtils, QgsVectorLayer,
                       QgsVectorLayerFeatureSource)

from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableManager
from Kavitro_dev.utils.mapandproperties.property_dialog_phase import (AddAction, AddMode, CancelTarget,
                                                                      PropertyDialogPhase as P,
                                                                      PropertyDialogState)
from Kavitro_dev.widgets.LocationFilterWidget import LocationFilterHelper, LocationFilterWidget
sys.path.insert(0, str(Path(__file__).resolve().parent))
from property_fixtures import (LocationFilterTestCase, add_fields, add_import_fields,
                               backend_info, close_dialog, dialog_open, make_main_layer,
                               missing_info, open_dialog, unknown_info)


class PropertyLocationRulesTest(LocationFilterTestCase):
    """Address matching, splitting and classification -- the rules behind the widgets."""

    def test_import_review_sets_the_same_decision_for_every_property(self):
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        decisions = [{'tunnus': '1', 'reason': K.PROPERTY_ADD_BACKEND_DIFFERS, 'backend_info': {}},
                     {'tunnus': '2', 'reason': K.PROPERTY_ADD_BACKEND_DIFFERS, 'backend_info': {}},
                     {'tunnus': '3', 'reason': K.ATTENTION_CAUSE_ARCHIVED_ONLY, 'backend_info': {}}]
        dialog = PropertyImportReviewDialog(decisions, lang_manager=LanguageManager('et'))
        try:
            self.assertFalse(dialog.confirm.isEnabled())

            # Overwriting is offered only for address conflicts; the archived match keeps its choice.
            dialog.bulk_choice.setCurrentIndex(dialog.bulk_choice.findData('apply'))
            dialog._set_all()
            self.assertEqual(dialog.selected_decisions(), {'1': 'apply', '2': 'apply'})
            self.assertTrue(dialog.confirm.isEnabled())
            self.assertIn('1', dialog.bulk_note.text())

            # Keeping the existing record is available for every row.
            dialog.bulk_choice.setCurrentIndex(dialog.bulk_choice.findData('keep'))
            dialog._set_all()
            self.assertEqual(dialog.selected_decisions(), {'1': 'keep', '2': 'keep', '3': 'keep'})
            self.assertEqual(dialog.bulk_note.text(), '')
        finally:
            dialog.deleteLater()

    def test_address_split_separates_only_a_trailing_house_number(self):
        cases = {
            # A plain name and a real street address keep working as before.
            'Kuusemäe': ('Kuusemäe', ''),
            'Viljandi tee 31a': ('Viljandi tee', '31a'),
            'Kivi tn 16': ('Kivi tn', '16'),
            'Pärna 5-2': ('Pärna', '5-2'),
            'Kivi  tn   16': ('Kivi tn', '16'),
            # The number ends a name; the words before it stay untouched.
            'Jäärja metskond 66': ('Jäärja metskond', '66'),
            # A road marker and a leading road number belong to the name.
            'Põhja tänav L2': ('Põhja tänav L2', ''),
            'Jaama tänav T1': ('Jaama tänav T1', ''),
            '24226 Kamara-Peraküla tee': ('24226 Kamara-Peraküla tee', ''),
            # `//` joins several addresses of one object, so nothing is separated.
            'Nurme tn 2 // Kangrumäe': ('Nurme tn 2 // Kangrumäe', ''),
            'Pärnu mnt 9 // 11': ('Pärnu mnt 9 // 11', ''),
            'Allika tn 7 // Tartu mnt 23 // 23a // 23b': ('Allika tn 7 // Tartu mnt 23 // 23a // 23b', ''),
            # A lone token is a name, and an empty address never becomes the text NULL.
            '12': ('12', ''),
            'NULL': ('', ''),
            '': ('', ''),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                result = PropertyDataLoader.get_address_details_from_street(value)
                self.assertEqual((result['street'], result.get('house', '')), expected)

    def test_check_and_import_share_the_same_missing_settlement_value(self):
        """The pre-write check (AddUpdatePropertyDialog._start_attention_checks) and the
        import (PropertyDataLoader.prepare_data_for_import_stage1) both build the address
        through the shared PropertyDataLoader.build_import_address now, so a row with a
        missing settlement must reach the backend check with the exact same unnormalized
        value (QGIS NULL) that the import itself would send -- never a normalized ''.
        This is the regression guard for the mismatch the two previous production fixes
        (v2.12.27, v2.12.30) were about. Mirrors each site's own feature retrieval
        (table UserRole vs the source feature) instead of driving the whole dialog."""
        from PyQt5.QtGui import QStandardItemModel

        # `self.layer` is what PropertyDataLoader() resolves to here (MapHelpers is patched
        # in setUp), so the extra fields it validates on construction must live on it too.
        self.add_import_fields()
        feature = QgsFeature(self.layer.fields())
        # ay_nimi (settlement) is left unset, so it reads back as QGIS NULL.
        feature.setAttributes(['A', 'Shared municipality', None, '9', 'Address 9', '100',
                                '10', '2024-01-01', '2024-01-01'])
        self.layer.dataProvider().addFeatures([feature])
        stored = list(self.layer.getFeatures())[-1]

        # The check's own retrieval: AddUpdatePropertyDialog._start_attention_checks reads
        # the feature from the table's UserRole cell, then calls build_import_address.
        table = QTableView()
        model = QStandardItemModel(1, 1)
        model.setData(model.index(0, 0), stored, Qt.UserRole)
        table.setModel(model)
        row_feature = PropertyTableManager.get_cell_data(table, 0, 0, role=Qt.UserRole)
        check_city = PropertyDataLoader.build_import_address(row_feature)['city']

        # The import's own retrieval: AddBatchRunner reads the complete source feature and
        # calls prepare_data_for_import_stage1, which delegates to the same helper.
        import_data, *_ = PropertyDataLoader().prepare_data_for_import_stage1(stored)

        self.assertTrue(QgsVariantUtils.isNull(check_city))
        self.assertEqual(check_city, import_data['address']['city'])
        self.assertNotEqual(check_city, '')

    def test_date_typed_main_muudet_still_gives_the_same_decision_in_both_paths(self):
        """AddBatchRunner now normalizes the main layer's `muudet` value with
        date_to_iso_string before it reaches classify_property_import, the same way the
        check already did (AddUpdatePropertyDialog._start_attention_checks). _is_import_newer
        also converts either representation internally, so both a raw QDate and its
        normalized ISO string must still steer classify_property_import to the same
        decision -- this is the safety net behind that internal conversion."""
        from PyQt5.QtCore import QDate
        from Kavitro_dev.widgets.DateHelpers import DateHelpers
        from Kavitro_dev.modules.Property.FlowControllers.property_import_decisions import classify_property_import

        main_layer = QgsVectorLayer(f'Point?crs=EPSG:3301&field={F.tunnus}:string', 'Main', 'memory')
        add_fields(main_layer, (F.muudet,), QVariant.Date)
        main_feature = QgsFeature(main_layer.fields())
        main_feature.setAttributes(['1', QDate(2026, 1, 1)])
        main_layer.dataProvider().addFeatures([main_feature])
        main_row = next(main_layer.getFeatures())

        raw_main_date = main_row.attribute(F.muudet)                                # AddBatchRunner's way
        normalized_main_date = DateHelpers().date_to_iso_string(main_row[F.muudet])  # the check's way
        self.assertIsInstance(raw_main_date, QDate)
        self.assertEqual(normalized_main_date, '2026-01-01')

        data = {'cadastralUnit': {'number': '1'}, 'address': {'street': 'Uus tn 5', 'houseNumber': ''}}
        info = {'exists': True, 'active_count': 1, 'LastUpdated': '2025-06-01',
                'property': {'id': '861', 'cadastralUnitNumber': '1', 'displayAddress': 'Vana tn 3'}}

        via_import = classify_property_import(data, '2025-12-01', raw_main_date, info)
        via_check = classify_property_import(data, '2025-12-01', normalized_main_date, info)
        self.assertEqual(via_import['import_newer'], via_check['import_newer'])
        self.assertFalse(via_import['import_newer'])
        self.assertEqual((via_import['action'], via_import['reason']), (via_check['action'], via_check['reason']))
        self.assertEqual(via_import['action'], 'needs_decision')

    def test_check_and_import_reach_the_same_decision_for_the_same_object(self):
        """End-to-end regression guard for this refactor: given one cadastral feature, the
        check's own construction (AddUpdatePropertyDialog._start_attention_checks) and the
        import's own construction (AddBatchRunner._tick / prepare_data_for_import_stage1)
        must steer classify_property_import to the same decision. Additional to, not a
        replacement for, the existing import-builder test
        (test_address_split_separates_only_a_trailing_house_number) or the missing-settlement
        and date-type regression guards above."""
        from Kavitro_dev.widgets.DateHelpers import DateHelpers
        from Kavitro_dev.modules.Property.FlowControllers.property_import_decisions import classify_property_import

        self.add_import_fields()
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(['A', 'Shared municipality', 'Uus küla', '11', 'Kase tn 7', '250',
                                '20', '2024-01-01', '2025-03-10'])
        self.layer.dataProvider().addFeatures([feature])
        stored = next(f for f in self.layer.getFeatures() if f[F.tunnus] == '11')

        main_layer = make_main_layer(extra_fields=(F.muudet,))
        main_feature = QgsFeature(main_layer.fields())
        main_feature.setAttributes(['11', '2025-01-01'])
        main_layer.dataProvider().addFeatures([main_feature])
        main_row = next(main_layer.getFeatures())

        info = {'exists': True, 'active_count': 1, 'LastUpdated': '2025-02-01',
                'property': {'id': '900', 'cadastralUnitNumber': '11',
                              'displayAddress': 'Kase tn 7, Uus küla, Shared municipality, A'}}

        # The check's own construction (AddUpdatePropertyDialog._start_attention_checks).
        check_data = {'cadastralUnit': {'number': '11'},
                      'address': PropertyDataLoader.build_import_address(stored)}
        check_import_date = DateHelpers().date_to_iso_string(stored[F.muudet])
        check_main_date = DateHelpers().date_to_iso_string(main_row[F.muudet])
        check_decision = classify_property_import(check_data, check_import_date, check_main_date, info)

        # The import's own construction (AddBatchRunner._tick / prepare_data_for_import_stage1).
        import_data, _tunnus, _uses, import_date = PropertyDataLoader().prepare_data_for_import_stage1(stored)
        import_main_date = DateHelpers().date_to_iso_string(main_row.attribute(F.muudet))
        import_decision = classify_property_import(import_data, import_date, import_main_date, info)

        self.assertEqual((check_decision['action'], check_decision['reason'], check_decision['import_newer']),
                          (import_decision['action'], import_decision['reason'], import_decision['import_newer']))
        self.assertEqual(check_decision['action'], 'update')

    def test_property_table_headers_come_from_translations_in_both_languages(self):
        from Kavitro_dev.languages import en as en_module
        from Kavitro_dev.languages import et as et_module
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget

        keys = (K.CADASTRAL_ID, K.ADDRESS, K.AREA, K.SETTLEMENT, K.PROPERTY_COLUMN_BACKEND,
                K.PROPERTY_COLUMN_MAIN_LAYER, K.PROPERTY_COLUMN_ARCHIVE_BACKEND, K.PROPERTY_COLUMN_ARCHIVE_MAP)
        lang = LanguageManager()
        self.assertEqual(PropertyTableWidget._headers(), [lang.translate(key) for key in keys])
        # Strict lookup raises on a missing key, so every language must carry all of them.
        for translations in (et_module.TRANSLATIONS, en_module.TRANSLATIONS):
            self.assertEqual([key for key in keys if key not in translations], [])


class PropertyDialogStateTest(unittest.TestCase):
    """The dialog's button rules, read straight off the state object without Qt."""

    def state(self, **overrides):
        base = dict(row_count=1, selected_count=1)
        base.update(overrides)
        return PropertyDialogState(**base)

    def test_each_phase_is_named_by_the_first_matching_flag(self):
        cases = {
            (): P.IDLE,
            ('checks_completed_for_scope',): P.CHECKED,
            ('checks_running',): P.CHECKING,
            ('checks_running', 'checks_completed_for_scope'): P.CHECKING,
            ('add_in_progress',): P.ADDING,
            ('add_in_progress', 'checks_completed_for_scope'): P.ADDING,
            ('add_in_progress', 'checks_running'): P.ADDING,
            ('add_in_progress', 'checks_running', 'checks_completed_for_scope'): P.ADDING,
        }
        for flags, expected in cases.items():
            self.assertEqual(self.state(**{flag: True for flag in flags}).phase, expected,
                             msg=str(flags))

    def test_buttons_follow_the_phase_and_the_scope_size(self):
        # phase -> (add, add_without_checks, run_checks, review, scope_controls)
        expected = {
            P.IDLE: (False, True, True, True, True),
            P.CHECKING: (False, True, False, True, True),
            P.CHECKED: (True, True, True, True, True),
            P.ADDING: (False, False, False, False, False),
        }
        flags = {P.IDLE: {}, P.CHECKING: {'checks_running': True},
                 P.CHECKED: {'checks_completed_for_scope': True},
                 P.ADDING: {'add_in_progress': True}}
        for phase, buttons in expected.items():
            state = self.state(deferred_count=1, **flags[phase])
            self.assertEqual(
                (state.can_add_with_checks, state.can_add_without_checks, state.can_run_checks,
                 state.can_review_additions, state.scope_controls_enabled), buttons, msg=phase)

            # An empty scope takes every add and check away, whatever the phase.
            empty = self.state(row_count=0, selected_count=0, deferred_count=1, **flags[phase])
            self.assertEqual(
                (empty.can_add_with_checks, empty.can_add_without_checks, empty.can_run_checks),
                (False, False, False), msg='empty ' + phase)

            # Nothing deferred means nothing to review, in every phase.
            self.assertFalse(self.state(**flags[phase]).can_review_additions, msg='none ' + phase)

    def test_import_decisions_pending_is_the_only_thing_that_redirects_an_add(self):
        pending = dict(decisions_from_import=True, deferred_count=1)
        for phase_flags in ({}, {'checks_running': True}, {'checks_completed_for_scope': True},
                            {'add_in_progress': True}):
            state = self.state(**pending, **phase_flags)
            self.assertEqual(state.add_action(with_checks=True), AddAction.REVIEW, msg=str(phase_flags))
            self.assertEqual(state.add_action(with_checks=False), AddAction.REVIEW, msg=str(phase_flags))
            self.assertEqual(state.batch_add_action(mode=AddMode.WITH_CHECKS), AddAction.REVIEW
                             if not phase_flags.get('add_in_progress') else AddAction.IGNORE,
                             msg=str(phase_flags))

        # A check's own decisions stay where they are.
        from_check = self.state(decisions_from_import=False, deferred_count=1,
                                checks_completed_for_scope=True)
        self.assertEqual(from_check.add_action(with_checks=True), AddAction.START)
        self.assertEqual(from_check.add_action(with_checks=False), AddAction.START)

    def test_add_routing_per_phase(self):
        # phase -> (add_action with_checks, add_action without_checks)
        expected = {
            P.IDLE: (AddAction.IGNORE, AddAction.START),
            P.CHECKING: (AddAction.IGNORE, AddAction.START),
            P.CHECKED: (AddAction.START, AddAction.START),
            P.ADDING: (AddAction.IGNORE, AddAction.IGNORE),
        }
        flags = {P.IDLE: {}, P.CHECKING: {'checks_running': True},
                 P.CHECKED: {'checks_completed_for_scope': True},
                 P.ADDING: {'add_in_progress': True}}
        for phase, actions in expected.items():
            state = self.state(**flags[phase])
            self.assertEqual((state.add_action(with_checks=True),
                              state.add_action(with_checks=False)), actions, msg=phase)

        # The unchecked add refuses an empty scope by itself; the checked one never gets there.
        empty = self.state(row_count=0, selected_count=0, checks_completed_for_scope=True)
        self.assertEqual(empty.add_action(with_checks=False), AddAction.IGNORE)

    def test_the_review_run_is_the_one_batch_mode_that_passes_a_pending_review(self):
        pending = self.state(decisions_from_import=True, deferred_count=1,
                             checks_completed_for_scope=True)
        self.assertEqual(pending.batch_add_action(mode=AddMode.REVIEW), AddAction.START)
        self.assertEqual(pending.batch_add_action(mode=AddMode.WITHOUT_CHECKS), AddAction.REVIEW)
        # A checked batch still needs a finished check behind it.
        unchecked = self.state()
        self.assertEqual(unchecked.batch_add_action(mode=AddMode.WITH_CHECKS), AddAction.IGNORE)
        self.assertEqual(unchecked.batch_add_action(mode=AddMode.WITHOUT_CHECKS), AddAction.START)
        # Nothing starts on top of a running add.
        adding = self.state(add_in_progress=True, checks_completed_for_scope=True)
        for mode in (AddMode.WITH_CHECKS, AddMode.WITHOUT_CHECKS, AddMode.REVIEW):
            self.assertEqual(adding.batch_add_action(mode=mode), AddAction.IGNORE, msg=mode)

    def test_cancel_stops_the_innermost_running_work(self):
        cases = [
            (dict(archive_lookup_active=True, checks_running=True, has_add_runner=True),
             CancelTarget.ARCHIVE_LOOKUP),
            (dict(checks_running=True, has_add_runner=True), CancelTarget.CHECKS),
            (dict(has_add_runner=True), CancelTarget.ADD_RUN),
            (dict(), CancelTarget.CLOSE),
        ]
        for flags, expected in cases:
            self.assertEqual(self.state(**flags).cancel_target, expected, msg=str(flags))

        # A finished run clears the flag before the runner, and cancel follows the runner.
        self.assertEqual(self.state(add_in_progress=True, has_add_runner=False).cancel_target,
                         CancelTarget.CLOSE)



if __name__ == '__main__':
    unittest.main()
