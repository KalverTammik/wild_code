"""Shared widgets get module pieces by registration, not by importing modules/.

ModuleConfigFactory used to build the project board detail itself and StatusChangeController
imported the works layer sync. Both now take what ui/modules_registry.py registers.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication

from Kavitro_dev.constants.module_names import Module
from Kavitro_dev.modules.projects import project_detail_config
from Kavitro_dev.modules.works import works_sync_service
from Kavitro_dev.ui.modules_registry import ModulesRegistry
from Kavitro_dev.widgets.DataDisplayWidgets import status_change_controller as status_widget_module
from Kavitro_dev.widgets.DataDisplayWidgets.ModuleConfig import ModuleConfig, ModuleConfigFactory
from Kavitro_dev.widgets.DataDisplayWidgets.status_change_controller import StatusChangeController

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()


class _Registrations(unittest.TestCase):
    """Each test starts from empty registrations and puts the real ones back afterwards."""

    def setUp(self):
        factories = patch.dict(ModuleConfigFactory._registered_factories, clear=True)
        hooks = patch.dict(StatusChangeController._status_change_hooks, clear=True)
        factories.start()
        hooks.start()
        self.addCleanup(factories.stop)
        self.addCleanup(hooks.stop)


class ModuleConfigRegistrationTest(_Registrations):
    def test_unregistered_project_gets_a_plain_config(self):
        config = ModuleConfigFactory.create_config(Module.PROJECT.value, {"id": "1"})

        self.assertIsInstance(config, ModuleConfig)
        self.assertIsNone(config.detail_loader)

    def test_registered_factory_builds_the_config(self):
        made = ModuleConfig()
        factory = Mock(return_value=made)
        ModuleConfigFactory.register(Module.PROJECT.value, factory)

        self.assertIs(ModuleConfigFactory.create_config(Module.PROJECT.value, {"id": "1"}), made)
        factory.assert_called_once_with({"id": "1"})

    def test_project_config_loads_the_board_in_the_background(self):
        config = project_detail_config.create_project_config({"id": "7"})

        self.assertTrue(config.show_detail_handle)
        with patch.object(project_detail_config, "AsyncContentWidget") as async_widget, \
                patch.object(project_detail_config.ProjectBoardOverviewService, "build_project_board_data") as build:
            config.detail_loader()
            loader = async_widget.call_args.args[0]
            loader()
        build.assert_called_once()
        self.assertEqual(build.call_args.args, ({"id": "7"},))


class _Host:
    """The StatusChangeController state the hook runner reads."""

    def __init__(self, module_name, item_id="T1"):
        self._module_name = module_name
        self._item_data = {"id": item_id}


class StatusChangeHookTest(_Registrations):
    def _run(self, host, payload=None):
        StatusChangeController._run_status_change_hooks(host, payload)

    def test_hook_runs_for_its_modules_only(self):
        hook = Mock()
        StatusChangeController.register_status_change_hook((Module.WORKS.value, Module.TASK.value), "sync", hook)
        works, project = _Host(Module.WORKS.value), _Host(Module.PROJECT.value)

        self._run(works, {"id": "T1"})
        self._run(project)

        hook.assert_called_once_with("T1", {"id": "T1"})

    def test_no_item_id_runs_nothing(self):
        hook = Mock()
        StatusChangeController.register_status_change_hook((Module.WORKS.value,), "sync", hook)

        self._run(_Host(Module.WORKS.value, item_id=" "))

        hook.assert_not_called()

    def test_registering_a_key_again_replaces_the_hook(self):
        first, second = Mock(), Mock()
        StatusChangeController.register_status_change_hook((Module.WORKS.value,), "sync", first)
        StatusChangeController.register_status_change_hook((Module.WORKS.value,), "sync", second)

        self._run(_Host(Module.WORKS.value))

        first.assert_not_called()
        second.assert_called_once()

    def test_a_failing_hook_is_logged_and_the_next_one_still_runs(self):
        failing, other = Mock(side_effect=RuntimeError("layer gone")), Mock()
        StatusChangeController.register_status_change_hook((Module.WORKS.value,), "a", failing)
        StatusChangeController.register_status_change_hook((Module.WORKS.value,), "b", other)

        with patch.object(status_widget_module.PythonFailLogger, "log_exception") as log:
            self._run(_Host(Module.WORKS.value))

        other.assert_called_once()
        self.assertEqual(log.call_args.kwargs["event"], "status_widget_status_change_hook_failed")


class RegistryWiringTest(_Registrations):
    def test_register_all_wires_the_project_detail_and_the_works_sync(self):
        ModulesRegistry.register_all(Mock(), Mock())

        self.assertIs(ModuleConfigFactory._registered_factories[Module.PROJECT.value],
                      project_detail_config.create_project_config)
        for module in (Module.WORKS.value, Module.TASK.value):
            self.assertIn("works_layer_sync", StatusChangeController._status_change_hooks[module])
        # An as-built's status goes to the as-built layer; the Works layer never holds as-builts.
        self.assertEqual(list(StatusChangeController._status_change_hooks[Module.ASBUILT.value]), ["asbuilt_layer_sync"])
        # A project and an easement mirror their status on the map; contracts and coordinations have no layer.
        self.assertEqual(list(StatusChangeController._status_change_hooks[Module.PROJECT.value]), ["project_layer_sync"])
        self.assertEqual(list(StatusChangeController._status_change_hooks[Module.EASEMENT.value]), ["easement_layer_sync"])
        for module in (Module.CONTRACT.value, Module.COORDINATION.value):
            self.assertNotIn(module, StatusChangeController._status_change_hooks)

        with patch.object(works_sync_service.WorksSyncService, "sync_task_from_backend") as sync:
            StatusChangeController._status_change_hooks[Module.WORKS.value]["works_layer_sync"]("T9", {"id": "T9"})
        sync.assert_called_once_with("T9", task={"id": "T9"})

    def test_project_and_easement_hooks_write_the_status_onto_their_layers(self):
        ModulesRegistry.register_all(Mock(), Mock())
        project, easement = {"id": "P1", "status": {"id": "3"}}, {"id": "E1", "status": {"id": "4"}}

        with patch("Kavitro_dev.modules.projects.projects_layer_service.ProjectsLayerService.sync_status_from_project") as sync_project:
            StatusChangeController._status_change_hooks[Module.PROJECT.value]["project_layer_sync"]("P1", project)
        sync_project.assert_called_once_with("P1", project)

        with patch("Kavitro_dev.modules.easements.easement_layer_service.EasementLayerService.sync_status_from_easement") as sync_easement:
            StatusChangeController._status_change_hooks[Module.EASEMENT.value]["easement_layer_sync"]("E1", easement)
        sync_easement.assert_called_once_with("E1", easement)

    def test_register_all_twice_keeps_one_hook(self):
        ModulesRegistry.register_all(Mock(), Mock())
        ModulesRegistry.register_all(Mock(), Mock())

        self.assertEqual(len(StatusChangeController._status_change_hooks[Module.WORKS.value]), 1)


if __name__ == "__main__":
    unittest.main()
