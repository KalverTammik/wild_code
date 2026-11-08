"""The description of a new work is written the way Kavitro's TipTap editor stores it."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.modules.works.works_layer_service import WorksDescriptionService


class WorksDescriptionTest(unittest.TestCase):
    def build(self, text: str) -> str:
        return WorksDescriptionService.build_task_description(text)

    def test_text_is_one_plain_paragraph_with_line_breaks(self) -> None:
        self.assertEqual(self.build(' Kaev 47\nkaas <katki> & "vajub" '), '<p>Kaev 47<br>kaas &lt;katki&gt; &amp; "vajub"</p>')

    def test_empty_text_writes_no_description(self) -> None:
        self.assertEqual(self.build("  "), "")


if __name__ == "__main__":
    unittest.main()
