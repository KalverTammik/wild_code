"""FeedLoadEngine reads the module's token state, also after deactivate clears parent_ui."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.feed.feed_load_engine import FeedLoadEngine
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin


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

    def test_loader_owner_decides_after_parent_ui_is_cleared(self) -> None:
        self.engine.parent_ui = None  # FeedSessionController.deactivate_session does this.

        self.assertEqual(self.engine._current_token(), self.token)
        self.assertTrue(self.engine._is_token_active(self.token))

        new_token = self.owner.mark_deactivated()

        self.assertFalse(self.engine._is_active())
        self.assertFalse(self.engine._is_token_active(self.token))
        self.assertFalse(self.engine._is_token_active(new_token))

    def test_plain_function_loader_has_no_owner(self) -> None:
        engine = FeedLoadEngine(lambda: [])

        self.assertTrue(engine._is_active())
        self.assertIsNone(engine._current_token())
        self.assertTrue(engine._is_token_active(5))


if __name__ == "__main__":
    unittest.main()
