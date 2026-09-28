import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from Kavitro_dev.widgets.DelayHelpers.glow_progress_bar import GlowProgressBar

STYLES = Path(__file__).resolve().parents[1] / 'styles'


class GlowProgressBarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self):
        self.window = QWidget()
        self.bar = GlowProgressBar(self.window)
        QVBoxLayout(self.window).addWidget(self.bar)

    def tearDown(self):
        # A top-level widget left for deleteLater crashes a later module at shutdown.
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_theme_qss_sets_colours_for_both_themes(self):
        for theme, track in (('Light', '#e2eeec'), ('Dark', '#253038')):
            with self.subTest(theme=theme):
                self.window.setStyleSheet((STYLES / theme / 'main.qss').read_text(encoding='utf-8'))
                self.bar.ensurePolished()
                self.app.processEvents()
                self.assertEqual(self.bar.trackColor.name(), track)
                self.assertGreater(self.bar.borderColor.alpha(), 0)
                self.assertLess(self.bar.borderColor.alpha(), 255)

    def test_only_a_visible_running_bar_animates(self):
        self.bar.setState(GlowProgressBar.RUNNING)
        self.assertFalse(self.bar.isAnimating())
        self.window.show()
        self.assertTrue(self.bar.isAnimating())
        self.bar.hide()
        self.assertFalse(self.bar.isAnimating())
        self.bar.show()
        self.assertTrue(self.bar.isAnimating())
        for state in (GlowProgressBar.ERROR, GlowProgressBar.IDLE):
            self.bar.setState(state)
            self.assertFalse(self.bar.isAnimating())

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(ValueError):
            self.bar.setState('done')

    def test_paints_every_state_and_edge_value(self):
        self.window.resize(300, 40)
        self.window.show()
        for state in (GlowProgressBar.RUNNING, GlowProgressBar.ERROR, GlowProgressBar.IDLE):
            for minimum, maximum, value in ((0, 1, 0), (0, 710, 1), (0, 710, 710), (0, 0, 0)):
                with self.subTest(state=state, value=value, maximum=maximum):
                    self.bar.setState(state)
                    self.bar.setRange(minimum, maximum)
                    self.bar.setValue(value)
                    self.assertFalse(self.bar.grab().isNull())


if __name__ == '__main__':
    unittest.main()
