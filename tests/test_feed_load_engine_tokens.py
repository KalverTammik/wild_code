"""FeedLoadEngine keeps its module across deactivate; the module's token decides which loads still count."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QWidget

from Kavitro_dev.feed.feed_load_engine import FeedLoadEngine
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.coordination.CoordinationModule import CoordinationModule
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin


def delete_now(widget: QWidget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class TokenOwner(TokenMixin):
    def load_next_batch(self):
        return []


class FeedLoadEngineTokenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.owner = TokenOwner()
        self.engine = FeedLoadEngine(self.owner.load_next_batch).attach(parent_ui=self.owner)
        self.token = self.owner.mark_activated()

    def test_attached_module_decides_activity_and_token(self) -> None:
        self.assertTrue(self.engine._is_active())
        self.assertEqual(self.engine._current_token(), self.token)
        self.assertTrue(self.engine._is_token_active(self.token))
        self.assertFalse(self.engine._is_token_active(self.token - 1))

    def test_a_new_session_rejects_the_old_token(self) -> None:
        self.owner.mark_deactivated()

        self.assertFalse(self.engine._is_active())
        self.assertFalse(self.engine._is_token_active(self.token))

        new_token = self.owner.mark_activated()

        self.assertTrue(self.engine._is_token_active(new_token))
        self.assertFalse(self.engine._is_token_active(self.token))

    def test_plain_function_loader_has_no_owner(self) -> None:
        engine = FeedLoadEngine(lambda: [])

        self.assertTrue(engine._is_active())
        self.assertIsNone(engine._current_token())
        self.assertTrue(engine._is_token_active(5))


class FeedSessionReactivationTest(unittest.TestCase):
    """A module the user switched away from and back to still pages on its own."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        patches = [
            patch.object(ModuleManager, "getModuleSupports", return_value=(False, False, False, False)),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")),
        ]
        for p in patches:
            p.start()
        for p in patches:
            self.addCleanup(p.stop)
        self.ui = CoordinationModule(language=LanguageManager("et"))
        self.addCleanup(delete_now, self.ui)
        self.ui.init_feed_engine(self.ui.load_next_batch)
        self.ui.feed_logic = Mock(has_more=True)

    def test_engine_keeps_its_module_after_deactivate(self) -> None:
        engine = self.ui.feed_load_engine
        old_token = self.ui.mark_activated()

        # ModuleManager marks the module deactivated, then calls deactivate().
        self.ui.mark_deactivated()
        self.ui.deactivate()
        new_token = self.ui.mark_activated()

        self.assertIs(engine.parent_ui, self.ui)
        self.assertTrue(engine._is_token_active(new_token))
        self.assertFalse(engine._is_token_active(old_token))
        self.assertTrue(engine._upstream_has_more(), "a drained buffer must ask for the next page again")


if __name__ == "__main__":
    unittest.main()
