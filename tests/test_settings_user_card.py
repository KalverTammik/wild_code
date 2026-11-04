from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from Kavitro_dev.modules.Settings.cards import SettingsUserCard as card_module


class ClickTargetRegistrationTest(unittest.TestCase):
    def test_event_filter_failure_is_logged_and_keeps_the_target(self) -> None:
        card = SimpleNamespace(_pill_click_targets={})
        widget = Mock()
        widget.installEventFilter.side_effect = RuntimeError("deleted")
        checkbox = object()

        with patch.object(card_module.PythonFailLogger, "log_exception") as log_exception:
            card_module.UserSettingsCard._register_click_target(card, widget, checkbox)

        log_exception.assert_called_once()
        self.assertEqual(log_exception.call_args.kwargs["event"], "settings_user_card_register_click_target_failed")
        self.assertIs(card._pill_click_targets[widget], checkbox)


if __name__ == "__main__":
    unittest.main()
