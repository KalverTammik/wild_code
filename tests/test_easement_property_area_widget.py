import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QWidget
from Kavitro_dev.constants.cadastral_fields import AreaUnit
from Kavitro_dev.widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget


class EasementPropertyAreaCalculationWidgetTest(unittest.TestCase):
    """The unit, currency, total and payment-date controls exist only in some modes."""

    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self):
        self.window = QWidget()
        self.lang = Mock()
        self.lang.translate.side_effect = str

    def tearDown(self):
        # A top-level widget left for deleteLater crashes a later module at shutdown.
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def _widget(self, *, payable: bool, read_only: bool) -> EasementPropertyAreaCalculationWidget:
        edge = {
            'area': {'size': 2.0, 'unit': AreaUnit.H},
            'pricePerAreaUnit': {'amount': 3.0, 'currencyCode': 'USD'},
            'isPayable': payable,
            'nextPaymentDate': ' 2026-01-01 ',
        }
        return EasementPropertyAreaCalculationWidget(
            lang_manager=self.lang,
            edge=edge,
            area_unit_labels={AreaUnit.M: 'm2', AreaUnit.H: 'ha'},
            default_currency='EUR',
            read_only=read_only,
            parent=self.window,
        )

    def test_read_only_unpaid_edge_reads_its_values_from_the_edge(self):
        widget = self._widget(payable=False, read_only=True)
        self.assertIsNone(widget.unit_combo)
        self.assertIsNone(widget.currency_combo)
        self.assertIsNone(widget.total_label)
        self.assertIsNone(widget.next_payment_edit)
        self.assertEqual(widget.current_unit(), AreaUnit.H)
        self.assertEqual(widget.currency_code(), 'USD')
        self.assertEqual(widget.next_payment_text(), '2026-01-01')
        widget.set_total_display('6.00 USD')
        self.assertFalse(widget.payable_checkbox.isEnabled())

    def test_read_only_payable_edge_locks_the_payment_date(self):
        widget = self._widget(payable=True, read_only=True)
        self.assertIsNone(widget.unit_combo)
        self.assertIsNone(widget.currency_combo)
        self.assertTrue(widget.next_payment_edit.isReadOnly())
        widget.set_total_display('6.00 USD')
        self.assertEqual(widget.total_label.text(), '6.00 USD')

    def test_editable_payable_edge_reads_its_values_from_the_controls(self):
        widget = self._widget(payable=True, read_only=False)
        unit_changes = []
        widget.unitChanged.connect(lambda: unit_changes.append(True))
        widget.unit_combo.setCurrentIndex(widget.unit_combo.findData(AreaUnit.M))
        widget.currency_combo.setCurrentIndex(widget.currency_combo.findData('EUR'))
        widget.next_payment_edit.setText(' 2027-02-02 ')
        self.assertEqual(widget.current_unit(), AreaUnit.M)
        self.assertEqual(unit_changes, [True])
        self.assertEqual(widget.currency_code(), 'EUR')
        self.assertEqual(widget.next_payment_text(), '2027-02-02')
        self.assertFalse(widget.next_payment_edit.isReadOnly())


if __name__ == '__main__':
    unittest.main()
