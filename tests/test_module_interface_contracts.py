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

from PyQt5.QtCore import QObject, pyqtSignal

from Kavitro_dev.modules.Property.PropertyUITools import PropertyUITools
from Kavitro_dev.modules.Settings import settings_ui_controller as controller_module
from Kavitro_dev.modules.Settings.cards.ModuleLabelsWidget import ModuleLabelsWidget
from Kavitro_dev.modules.Settings.cards.SettingsModuleCard import SettingsModuleCard
from Kavitro_dev.modules.Settings.cards.SettingsProjectBaseLayersCard import SettingsProjectBaseLayersCard
from Kavitro_dev.modules.Settings.cards.SettingsUserCard import UserSettingsCard
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin
from Kavitro_dev.widgets.Filters.NotStartedStatusFilterWidget import NotStartedStatusFilterWidget
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget
from Kavitro_dev.widgets.layer_tree_picker import LayerTreePicker


class DirectCallContractTest(unittest.TestCase):
    """Module UIs and Settings call these hooks directly, without a hasattr fallback."""

    def test_classes_define_the_hooks_their_callers_use(self) -> None:
        expected = {
            StatusFilterWidget: ("ensure_loaded", "clear_data"),
            NotStartedStatusFilterWidget: ("ensure_loaded", "clear_data"),
            TypeFilterWidget: ("ensure_loaded", "clear_data"),
            TagsFilterWidget: ("ensure_loaded", "clear_data"),
            UserSettingsCard: ("retheme",),
            SettingsProjectBaseLayersCard: ("retheme",),
            SettingsModuleCard: ("retheme", "set_geospatial_mode_active", "set_property_management_available"),
            ModuleLabelsWidget: ("clear_data",),
            LayerTreePicker: ("project",),
        }
        for cls, names in expected.items():
            for name in names:
                with self.subTest(cls=cls.__name__, method=name):
                    self.assertTrue(callable(getattr(cls, name, None)))


class SettingsCloseGuardTest(unittest.TestCase):
    def test_close_guard_passes_the_active_module_name(self) -> None:
        dialog = SimpleNamespace(moduleManager=Mock(getActiveModuleName=Mock(return_value="settings")))

        with patch.object(
            controller_module.DialogHelpers, "confirm_settings_navigation", return_value=True
        ) as confirm:
            self.assertTrue(controller_module.SettingsUIController.can_close(dialog))

        confirm.assert_called_once_with("settings", dialog)


class _PropertyUiStub(TokenMixin, QObject):
    property_selected_from_map = pyqtSignal()

    def __init__(self) -> None:
        QObject.__init__(self)
        TokenMixin.__init__(self)


class PropertyToolsTokenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = _PropertyUiStub()
        # Skip __init__: it builds data and map-selection services these checks do not use.
        self.tools = PropertyUITools.__new__(PropertyUITools)
        self.tools.property_ui = self.ui

    def test_token_follows_module_activation(self) -> None:
        token = self.tools._current_token()
        self.assertFalse(self.tools._is_token_active(token))

        self.ui.mark_activated(token)
        self.assertTrue(self.tools._is_token_active(token))

        self.ui.mark_deactivated()
        self.assertFalse(self.tools._is_token_active(token))

    def test_named_signal_is_emitted(self) -> None:
        received = []
        self.ui.property_selected_from_map.connect(lambda: received.append(True))

        self.tools._emit_ui_signal("property_selected_from_map")

        self.assertEqual(received, [True])


if __name__ == "__main__":
    unittest.main()
