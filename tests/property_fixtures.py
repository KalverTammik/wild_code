"""Shared scaffolding for the offline tests.

Test scaffolding only: waiting on background work, building the offline import
layer, shaping a backend verify answer and opening/closing a dialog without
leaving a stray top level widget behind. No business logic lives here -- every
rule the tests assert still belongs to the production modules.

The test modules import this one as a plain top level module, so they put the
``tests`` directory on ``sys.path`` themselves before importing it. That keeps it
working under ``unittest discover``, under a direct run of a single file and
under the mutation runner in ``negative_checks.py``, which loads a test module
straight from its path.
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtCore import QCoreApplication, QEvent, Qt, QVariant
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QTableView, QVBoxLayout, QWidget
from qgis.core import QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableManager
from Kavitro_dev.widgets.LocationFilterWidget import LocationFilterHelper, LocationFilterWidget

# The three fields the add dialog reads on top of the plain location fields.
IMPORT_EXTRA_FIELDS = (F.hkood, F.registr, F.muudet)

# The location fields the offline import layer is built from.
LOCATION_FIELDS = (F.mk_nimi, F.ov_nimi, F.ay_nimi, F.tunnus, F.l_aadress, F.pindala)


# --------------------------------------------------------------------------- #
# Waiting for background work
# --------------------------------------------------------------------------- #

def wait_until(case, condition, *, attempts=200, message='background work did not complete'):
    """Pump the Qt event loop until ``condition`` holds, then return.

    The call sites disagreed on how long to wait and on what to say when the wait
    runs out, so both stay parameters: ``attempts`` times ``QTest.qWait(10)``, and
    ``message`` handed to ``TestCase.fail``. Nothing else differs between them.
    """
    for _ in range(attempts):
        if condition():
            return
        QTest.qWait(10)
    case.fail(message)


def wait_for(case, predicate, timeout=3, message='Timed out waiting for UI state'):
    """Wall clock variant of :func:`wait_until`.

    Kept separate on purpose: this one bounds the wait by ``time.monotonic`` rather
    than by a number of ``qWait`` rounds, and it asserts the predicate one last time
    instead of failing outright, which is what the widget tests rely on.
    """
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    case.assertTrue(predicate(), message)


# --------------------------------------------------------------------------- #
# Layer fields
# --------------------------------------------------------------------------- #

def add_fields(layer, names, field_type=QVariant.String):
    """Add a block of fields to ``layer`` and publish them in one go.

    Adding the attributes without ``updateFields`` leaves the layer reporting the
    old field list, which is the mistake this helper exists to stop repeating.
    """
    layer.dataProvider().addAttributes([QgsField(name, field_type) for name in names])
    layer.updateFields()
    return layer


def add_import_fields(layer, field_type=QVariant.String):
    """Add the add dialog's three extra fields to an offline import layer."""
    return add_fields(layer, IMPORT_EXTRA_FIELDS, field_type)


def make_import_layer(name='Offline location test', entries=None):
    """Build the offline import layer the location tests read from."""
    uri = 'Polygon?crs=EPSG:3301' + ''.join('&field=' + field + ':string' for field in LOCATION_FIELDS)
    layer = QgsVectorLayer(uri, name, 'memory')
    entries = entries if entries is not None else [('A', 'Shared municipality', 'First village', '1'),
                                                   ('A', 'Shared municipality', 'Second village', '2'),
                                                   ('B', 'Shared municipality', 'First village', '3')]
    features = []
    for county, municipality, village, cadastral in entries:
        feature = QgsFeature(layer.fields())
        feature.setAttributes([county, municipality, village, cadastral, 'Address ' + cadastral, '100'])
        offset = int(cadastral) * 100
        feature.setGeometry(QgsGeometry.fromWkt(
            f'POLYGON(({offset} 0,{offset + 10} 0,{offset + 10} 10,{offset} 10,{offset} 0))'))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def make_main_layer(name='Main', extra_fields=(), field_type=QVariant.String):
    """Build the main property layer the archive and check flows resolve to."""
    layer = QgsVectorLayer(f'Polygon?crs=EPSG:3301&field={F.tunnus}:string', name, 'memory')
    if extra_fields:
        add_fields(layer, extra_fields, field_type)
    return layer


# --------------------------------------------------------------------------- #
# Backend verify answers
# --------------------------------------------------------------------------- #

def backend_info(number='1', *, address='Example', item_id='known', active_count=1,
                 last_updated='2026-01-01', **extra):
    """A ``verify_properties_by_cadastral_number`` answer for a known property.

    ``active_count`` and ``last_updated`` are dropped from the answer when set to
    ``None``, because several call sites assert on an answer that carries neither.
    """
    info = {'exists': True}
    if active_count is not None:
        info['active_count'] = active_count
    if last_updated is not None:
        info['LastUpdated'] = last_updated
    info['property'] = {'id': item_id, 'cadastralUnitNumber': number, 'displayAddress': address}
    info.update(extra)
    return info


def missing_info(**extra):
    """The answer for a cadastral number the backend does not know."""
    return dict({'exists': False}, **extra)


def unknown_info(error='offline', **extra):
    """The answer for a lookup that could not be decided at all."""
    return dict({'exists': None, 'error': error}, **extra)


# --------------------------------------------------------------------------- #
# Dialogs
# --------------------------------------------------------------------------- #

def open_dialog(dialog_class, *args, **kwargs):
    """Construct a dialog without letting it enter its own modal loop.

    ``exec_`` is patched away for the construction only: offscreen, a real modal
    loop never returns.
    """
    with patch.object(dialog_class, 'exec_', return_value=0):
        return dialog_class(*args, **kwargs)


def close_dialog(case, dialog, *, attempts=200):
    """Reject a dialog and let its background read finish before it is deleted.

    Deleting a dialog whose location read is still running destroys a live worker,
    which aborts Qt, so the wait is not optional.
    """
    dialog.reject()
    helper = getattr(dialog, '_location_filter_helper', None)
    if helper is not None:
        wait_until(case, lambda: not helper._loader._request.busy, attempts=attempts,
                   message='dialog location read did not finish')
    dialog.deleteLater()


@contextlib.contextmanager
def dialog_open(case, dialog_class, *args, **kwargs):
    """Open a dialog and guarantee it is closed and deleted again.

    Trap this guards: a dialog left alive past the test can crash the process at
    interpreter shutdown, and it does so after the last test has already reported,
    so the run looks truncated rather than failed.
    """
    dialog = open_dialog(dialog_class, *args, **kwargs)
    try:
        yield dialog
    finally:
        close_dialog(case, dialog)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


# --------------------------------------------------------------------------- #
# The location filter test case
# --------------------------------------------------------------------------- #

class LocationFilterTestCase(unittest.TestCase):
    """The offline location fixture the three property location test files share.

    Builds the import layer, a parent window holding a real ``LocationFilterWidget``
    and table, and patches the map helpers so nothing reaches QGIS' project or the
    backend. Every widget the tests make is parented to ``self.window`` so that
    nothing is left standing at shutdown.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()
        if not QFontDatabase().families():
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        self.layer = make_import_layer()
        self.assertTrue(self.layer.isValid())
        self.window = QWidget()
        layout = QVBoxLayout(self.window)
        self.widget = LocationFilterWidget(LanguageManager('et'))
        layout.addWidget(self.widget)
        self.table = QTableView()
        layout.addWidget(self.table)
        self.completed, self.invalidated, self.stopped = Mock(), Mock(), Mock()
        self.helper = LocationFilterHelper(
            county_combo=self.widget.county_combo, municipality_combo=self.widget.municipality_combo,
            city_combo=self.widget.city_combo, properties_table=self.table,
            after_table_update=self.completed, stop_checks=self.stopped,
            invalidate_archive_scope=self.invalidated, update_add_button_state=Mock(),
            stop_map_update=Mock(), status_widget=self.widget, parent=self.window)
        self.helper.connect_signals()
        self.resolve = patch.object(MapHelpers, 'get_layer_by_tag', return_value=self.layer)
        self.resolve_mock = self.resolve.start()
        self.preview = patch.object(MapHelpers, 'apply_scope_preview')
        self.preview_mock = self.preview.start()
        self.window.resize(700, 450)
        self.window.show()

    def tearDown(self):
        self.helper.close()
        self.wait_until(lambda: not self.helper._loader._request.busy)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.preview.stop()
        self.resolve.stop()

    def wait_until(self, condition):
        wait_until(self, condition, attempts=200, message='Location read did not complete')

    def load_index(self):
        self.helper.load_counties(self.layer)
        self.wait_until(lambda: self.widget.county_combo.isEnabled())

    def pick(self, owner, county='A', municipality='Shared municipality'):
        owner.county_combo.setCurrentIndex(owner.county_combo.findData(county))
        # A county's municipalities arrive with its background read.
        self.wait_until(lambda: owner.municipality_combo.findData(municipality) >= 0)
        owner.municipality_combo.setCurrentIndex(owner.municipality_combo.findData(municipality))

    def choose_municipality(self, county='A'):
        self.pick(self.widget, county)

    def ids(self):
        return {PropertyTableManager.get_cell_text(self.table, row, 0)
                for row in range(PropertyTableManager.row_count(self.table))}

    def click_village(self, row):
        combo = self.widget.city_combo
        combo.showPopup()
        QTest.qWait(10)
        view = combo.view()
        QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view.visualRect(view.model().index(row, 0)).center())
        combo.hidePopup()

    def add_import_fields(self):
        add_import_fields(self.layer)

    def open_dialog_with_village_scope(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog)
        self.wait_until(lambda: dialog.county_combo.isEnabled())
        self.pick(dialog)
        dialog.city_combo.setCheckedItems(['First village'])
        self.wait_until(lambda: dialog._archive_scope_snapshot is not None)
        return dialog

    def close_dialog(self, dialog):
        close_dialog(self, dialog, attempts=200)
