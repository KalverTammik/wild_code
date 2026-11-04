"""Logout and unload destroy the dialog; the global module state must not outlive it."""
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

from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QApplication, QDialog, QListWidget, QWidget

from Kavitro_dev import dialog as dialog_module
from Kavitro_dev import main as main_module
from Kavitro_dev import module_manager as manager_module
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin
from Kavitro_dev.utils.moduleSwitchHelper import ModuleSwitchHelper
from Kavitro_dev.utils.SessionManager import SessionManager, SessionUIController
from Kavitro_dev.widgets import theme_manager as theme_module

ModuleManager = manager_module.ModuleManager
PluginDialog = dialog_module.PluginDialog


def delete_now(widget: QWidget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class RecordingModule(TokenMixin, QWidget):
    """Its deactivate() touches a child widget, as WorksModule.deactivate() does."""

    fail_deactivate = False

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._active_token = 0
        self._activated = False
        self._list_view = QListWidget(self)
        self.deactivate_calls = 0

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        self.deactivate_calls += 1
        if self.fail_deactivate:
            raise ValueError("deactivate failed")
        self._list_view.clear()

    def get_widget(self) -> QWidget:
        return self


def register_recording_modules(module_manager, dialog) -> None:
    for name in ("HOME", "PROPERTY", "WORKS"):
        module_manager.registerModule(RecordingModule, name, parent=dialog)


class IsolatedModuleStateTest(unittest.TestCase):
    """Gives each test its own module manager singleton and retheme registry."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        for patcher in (
            patch.object(ModuleManager, "_instance", None),
            patch.object(theme_module.ThemeManager, "_retheme_engine", theme_module.RethemeEngine()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        # SettingsLogic imported this list by name, so it must stay the same object.
        names = manager_module.MODULES_LIST_BY_NAME
        saved_names = list(names)
        names.clear()
        self.addCleanup(lambda: names.__setitem__(slice(None), saved_names))
        self.manager = ModuleManager()


class ModuleManagerSessionTest(IsolatedModuleStateTest):
    def setUp(self) -> None:
        super().setUp()
        self.owner = QDialog()
        self.addCleanup(delete_now, self.owner)
        register_recording_modules(self.manager, self.owner)

    def test_shutdown_deactivates_the_active_module_once(self) -> None:
        self.manager.activateModule("WORKS")
        instance = self.manager.getActiveModuleInstance("WORKS")

        self.manager.shutdownModules()
        self.manager.shutdownModules()

        self.assertEqual(instance.deactivate_calls, 1)
        self.assertFalse(instance._activated)
        self.assertIsNone(self.manager.getActiveModuleName())
        self.assertEqual(self.manager.modules, {})

    def test_shutdown_without_an_active_module_only_forgets_registrations(self) -> None:
        self.manager.shutdownModules()

        self.assertEqual(self.manager.modules, {})

    def test_failed_deactivate_still_forgets_the_old_modules(self) -> None:
        self.manager.activateModule("WORKS")
        self.manager.getActiveModuleInstance("WORKS").fail_deactivate = True

        with self.assertRaises(ValueError):
            self.manager.shutdownModules()

        self.assertIsNone(self.manager.getActiveModuleName())
        self.assertEqual(self.manager.modules, {})

    def test_registering_again_does_not_repeat_module_names(self) -> None:
        register_recording_modules(self.manager, self.owner)

        self.assertEqual(manager_module.MODULES_LIST_BY_NAME, ["Property", "Works"])


class PluginDialogSessionTest(IsolatedModuleStateTest):
    """Runs the real dialog, logout and unload; only the module classes are replaced."""

    def setUp(self) -> None:
        super().setUp()
        helper_state = {
            "_dialog_resolver": ModuleSwitchHelper._dialog_resolver,
            "_confirm_unsaved_handler": ModuleSwitchHelper._confirm_unsaved_handler,
            "_settings_focus_handler": ModuleSwitchHelper._settings_focus_handler,
        }
        for patcher in (
            patch.object(PluginDialog, "_instance", None),
            patch.object(dialog_module.ModulesRegistry, "register_all", side_effect=register_recording_modules),
            patch.object(SessionManager, "clear"),
            patch.multiple(ModuleSwitchHelper, **helper_state),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _open_dialog(self) -> PluginDialog:
        dialog = PluginDialog()
        self.addCleanup(self._delete_if_alive, dialog)
        return dialog

    @staticmethod
    def _delete_if_alive(dialog: PluginDialog) -> None:
        try:
            delete_now(dialog)
        except RuntimeError:
            pass  # Logout already deleted this dialog.

    def _open_dialog_on_works(self):
        dialog = self._open_dialog()
        dialog.moduleManager.activateModule("WORKS")
        return dialog, dialog.moduleManager.getActiveModuleInstance("WORKS")

    def test_logout_deactivates_the_active_module_and_forgets_it(self) -> None:
        dialog, works = self._open_dialog_on_works()

        SessionUIController.logout(dialog)

        self.assertEqual(works.deactivate_calls, 1)
        self.assertIsNone(self.manager.getActiveModuleName())
        self.assertEqual(self.manager.modules, {})
        self.assertIsNone(PluginDialog.get_instance())

    def test_module_switch_works_in_the_dialog_opened_after_logout(self) -> None:
        old_dialog, _works = self._open_dialog_on_works()
        SessionUIController.logout(old_dialog)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        new_dialog = self._open_dialog()
        with patch.object(SessionManager, "is_session_valid", return_value=True):
            ModuleSwitchHelper.switch_module("HOME", dialog=new_dialog)

        home = self.manager.getActiveModuleInstance("HOME")
        self.assertIsNotNone(home)
        self.assertIs(new_dialog.moduleStack.currentWidget(), home)

    def test_plugin_unload_deactivates_the_active_module(self) -> None:
        dialog, works = self._open_dialog_on_works()
        plugin = main_module.WildCodePlugin(Mock())
        plugin.action = Mock()
        plugin.pluginDialog = dialog

        plugin.unload()

        self.assertEqual(works.deactivate_calls, 1)
        self.assertIsNone(self.manager.getActiveModuleName())

    def test_failed_deactivate_does_not_keep_the_dialog_open(self) -> None:
        dialog, works = self._open_dialog_on_works()
        works.fail_deactivate = True

        SessionUIController.logout(dialog)

        self.assertIsNone(PluginDialog.get_instance())
        self.assertIsNone(self.manager.getActiveModuleName())

    def test_ordinary_close_only_minimizes_and_keeps_the_module_active(self) -> None:
        dialog, works = self._open_dialog_on_works()

        with patch.object(dialog, "showMinimized") as show_minimized:
            dialog.close()

        show_minimized.assert_called_once()
        self.assertEqual(works.deactivate_calls, 0)
        self.assertEqual(self.manager.getActiveModuleName(), "works")


class RethemeEngineDeletedWidgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_retheme_forgets_deleted_widgets_and_keeps_the_living_ones(self) -> None:
        engine = theme_module.RethemeEngine()
        deleted, living = QWidget(), QWidget()
        self.addCleanup(delete_now, living)
        deleted_hook, living_hook = Mock(), Mock()
        engine.register(deleted, qss_files=["main.qss"], after_apply=deleted_hook)
        engine.register(living, qss_files=["main.qss"], after_apply=living_hook)
        delete_now(deleted)

        with patch.object(theme_module.PythonFailLogger, "log_exception") as log_exception:
            engine.retheme_all()
            engine.retheme_all()

        log_exception.assert_not_called()
        deleted_hook.assert_not_called()
        self.assertEqual(living_hook.call_count, 2)


if __name__ == "__main__":
    unittest.main()
