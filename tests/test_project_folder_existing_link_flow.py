"""What the project folder flow asks and tells the user, in order, and what it does in between.

The flow gets its dialogs from the card, so these tests hand it a recorder. The recorder, the saving of the
folder path and the card callback write into one list, so each test pins the whole sequence: which dialog,
its title, text, button labels and default, and where the request and the callback come between them.
"""
from __future__ import annotations

import ast
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.projects import projects_card_actions
from Kavitro_dev.utils.api_error_handling import user_message
from Kavitro_dev.utils.Folders import foldersHelpers
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.utils.project_folder_rules import MissingProjectNumberError
from Kavitro_dev.constants.module_names import Module
from Kavitro_dev.utils.user_dialogs import UserDialogs

T = LanguageManager.translate_static
FOLDER = "Projekt"
PROJECT_ID = "project-42"


def warning(key, **values):
    return ("warning", T(TranslationKeys.WARNING), T(key).format(**values))


def existing_link_question(path):
    return ("ask", T(TranslationKeys.CONFIRM), T(TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_CONFIRM).format(path=path),
            T(TranslationKeys.PROJECT_FOLDER_LINK_ACTION), T(TranslationKeys.NO), T(TranslationKeys.NO))


def create_question(source, destination):
    text = T(TranslationKeys.PROJECT_FOLDER_CREATE_CONFIRM).format(source=source, destination=destination)
    return ("ask", T(TranslationKeys.CONFIRM), text, T(TranslationKeys.YES), T(TranslationKeys.NO), T(TranslationKeys.NO))


def new_link_question(path):
    return ("ask", T(TranslationKeys.CONFIRM), T(TranslationKeys.PROJECT_FOLDER_LINK_CONFIRM).format(path=path),
            T(TranslationKeys.YES), T(TranslationKeys.NO), T(TranslationKeys.YES))


def link_failed(path, error):
    return warning(TranslationKeys.PROJECT_FOLDER_LINK_UPDATE_FAILED, path=path, error=user_message(error))


class RecordingDialogs:
    """Writes down each dialog the user would see; a question takes the next scripted answer."""

    def __init__(self, events: list, answers) -> None:
        self.events = events
        self.answers = list(answers)

    def show_warning(self, title, message):
        self.events.append(("warning", title, message))
        return True

    def show_info(self, title, message):
        self.events.append(("info", title, message))

    def ask_yes_no(self, title, message, *, yes_label, no_label, default=None):
        self.events.append(("ask", title, message, yes_label, no_label, default))
        answer = self.answers.pop(0)
        return answer() if callable(answer) else answer


class FolderFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="kavitro_project_folder_")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.source = root / "source"
        self.target = root / "target"
        self.source.mkdir()
        self.target.mkdir()
        (self.source / "template-only.txt").write_text("template", encoding="utf-8")
        self.source_dir = os.path.realpath(str(self.source))
        self.target_dir = os.path.realpath(str(self.target))
        self.dest = os.path.realpath(os.path.join(self.target_dir, FOLDER))
        self.events: list = []

        # A real window would wait for a click that never comes; the flow may only use the dialogs it is given.
        self.real_dialogs = {}
        for name in ("show_warning", "show_info", "show_error", "ask_yes_no", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            self.real_dialogs[name] = patcher.start()
            self.addCleanup(patcher.stop)

        self.folder_name = self.replace(foldersHelpers.FolderNameGenerator, "folder_structure_name_order",
                                        return_value=FOLDER)
        updater_class = self.replace(foldersHelpers, "ModuleFilesPathUpdater")
        updater_class.return_value.update.side_effect = self.save_path
        self.link_reply = None

    def replace(self, owner, name, **options) -> Mock:
        patcher = patch.object(owner, name, **options)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def save_path(self, module, project_id, path):
        self.events.append(("update", module, project_id, path))
        if isinstance(self.link_reply, Exception):
            raise self.link_reply
        return self.link_reply or {"id": project_id, "filesPath": path}

    def card_callback(self, path) -> None:
        self.events.append(("callback", path))

    def run_flow(self, *answers, source=None, target=None, callback=True) -> None:
        dialogs = RecordingDialogs(self.events, answers)
        foldersHelpers.FolderEngines.generate_project_folder_from_template(
            PROJECT_ID, "Projekti nimi", "PR-42",
            source_folder=str(self.source) if source is None else source,
            target_folder=str(self.target) if target is None else target,
            on_files_path_updated=self.card_callback if callback else None,
            dialogs=dialogs,
        )
        for name, stub in self.real_dialogs.items():
            self.assertFalse(stub.called, f"ModernMessageDialog.{name} was called directly")

    def saved(self, path=None):
        return ("update", Module.PROJECT, PROJECT_ID, path or self.dest)

    def target_contents(self) -> list:
        return sorted(os.listdir(self.target_dir))

    def make_existing_folder(self) -> None:
        os.mkdir(self.dest)
        Path(self.dest, "existing-only.txt").write_text("existing", encoding="utf-8")

    def assert_existing_folder_untouched(self) -> None:
        self.assertEqual(sorted(os.listdir(self.dest)), ["existing-only.txt"])

    # Refused before any question.

    def test_missing_source_folder_is_refused(self) -> None:
        missing = str(self.target / "puudub")
        self.run_flow(source=missing)
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_SOURCE_INVALID, path=missing)])
        self.assertEqual(self.target_contents(), [])

    def test_empty_target_folder_is_refused_with_a_dash(self) -> None:
        self.run_flow(target="  ")
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_TARGET_INVALID, path="-")])
        self.assertEqual(self.target_contents(), [])

    def test_target_inside_the_template_is_refused(self) -> None:
        inside = self.source / "sees"
        inside.mkdir()
        self.run_flow(target=str(inside))
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_TARGET_INSIDE_SOURCE,
                                               source=self.source_dir, target=os.path.realpath(str(inside)))])
        self.assertEqual(sorted(os.listdir(inside)), [])

    def test_missing_project_number_is_refused(self) -> None:
        self.folder_name.side_effect = MissingProjectNumberError("number")
        self.run_flow()
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_NUMBER_MISSING)])
        self.assertEqual(self.target_contents(), [])

    def test_other_naming_error_shows_its_text_below_the_message(self) -> None:
        self.folder_name.side_effect = ValueError("vigane reegel")
        self.run_flow()
        text = T(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID) + "\nvigane reegel"
        self.assertEqual(self.events, [("warning", T(TranslationKeys.WARNING), text)])
        self.assertEqual(self.target_contents(), [])

    def test_name_without_a_safe_destination_is_refused(self) -> None:
        self.replace(foldersHelpers, "resolve_direct_child_path", return_value="")
        self.run_flow()
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_DESTINATION_INVALID)])
        self.assertEqual(self.target_contents(), [])

    def test_destination_taken_by_a_file_is_refused(self) -> None:
        Path(self.dest).write_text("fail", encoding="utf-8")
        self.run_flow()
        self.assertEqual(self.events, [warning(TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS, path=self.dest)])
        self.assertEqual(Path(self.dest).read_text(encoding="utf-8"), "fail")

    # The folder already exists: only its path can be saved to the project.

    def test_existing_folder_declined_changes_nothing(self) -> None:
        self.make_existing_folder()
        self.run_flow(False)
        self.assertEqual(self.events, [existing_link_question(self.dest)])
        self.assert_existing_folder_untouched()

    def test_existing_folder_linked_updates_the_card_before_the_success_notice(self) -> None:
        self.make_existing_folder()
        self.run_flow(True)
        self.assertEqual(self.events, [
            existing_link_question(self.dest),
            self.saved(),
            ("callback", self.dest),
            ("info", T(TranslationKeys.SUCCESS),
             T(TranslationKeys.PROJECT_FOLDER_EXISTING_LINK_SUCCESS).format(path=self.dest)),
        ])
        self.assert_existing_folder_untouched()

    def test_existing_folder_link_failure_warns_and_stops(self) -> None:
        self.make_existing_folder()
        self.link_reply = RuntimeError("API failure")
        self.run_flow(True)
        self.assertEqual(self.events, [existing_link_question(self.dest), self.saved(),
                                       link_failed(self.dest, self.link_reply)])
        self.assert_existing_folder_untouched()

    def test_empty_saved_path_counts_as_a_failed_link(self) -> None:
        self.make_existing_folder()
        self.link_reply = {"id": PROJECT_ID, "filesPath": "  "}
        self.run_flow(True)
        empty = RuntimeError("filesPath update returned an empty path")
        self.assertEqual(self.events, [existing_link_question(self.dest), self.saved(), link_failed(self.dest, empty)])

    def test_existing_folder_linked_without_a_card_callback(self) -> None:
        self.make_existing_folder()
        self.run_flow(True, callback=False)
        self.assertEqual([event[0] for event in self.events], ["ask", "update", "info"])

    # A new folder: copy the template, then offer to save its path.

    def test_declined_creation_copies_nothing(self) -> None:
        self.run_flow(False)
        self.assertEqual(self.events, [create_question(self.source_dir, self.dest)])
        self.assertEqual(self.target_contents(), [])

    def test_folder_appearing_before_the_copy_is_not_overwritten(self) -> None:
        def someone_else_creates_it():
            self.make_existing_folder()
            return True

        self.run_flow(someone_else_creates_it)
        self.assertEqual(self.events, [create_question(self.source_dir, self.dest),
                                       warning(TranslationKeys.PROJECT_FOLDER_ALREADY_EXISTS, path=self.dest)])
        self.assert_existing_folder_untouched()

    def test_failed_copy_warns_with_the_error_text(self) -> None:
        self.replace(foldersHelpers.shutil, "copytree", side_effect=OSError("ketas täis"))
        self.run_flow(True)
        self.assertEqual(self.events, [create_question(self.source_dir, self.dest),
                                       warning(TranslationKeys.PROJECT_FOLDER_COPY_FAILED, error="ketas täis")])

    def test_copied_folder_left_unlinked_still_reports_the_copy(self) -> None:
        self.run_flow(True, False)
        self.assertEqual(self.events, [
            create_question(self.source_dir, self.dest),
            new_link_question(self.dest),
            ("info", T(TranslationKeys.SUCCESS),
             T(TranslationKeys.FOLDER_COPY_SUCCESS).format(source=self.source_dir, folder=FOLDER)),
        ])
        self.assertTrue(Path(self.dest, "template-only.txt").is_file())

    def test_copied_and_linked_folder_updates_the_card_before_the_success_notice(self) -> None:
        self.run_flow(True, True)
        self.assertEqual(self.events, [
            create_question(self.source_dir, self.dest),
            new_link_question(self.dest),
            self.saved(),
            ("callback", self.dest),
            ("info", T(TranslationKeys.SUCCESS),
             T(TranslationKeys.FOLDER_COPY_SUCCESS).format(source=self.source_dir, folder=FOLDER)),
        ])
        self.assertTrue(Path(self.dest, "template-only.txt").is_file())

    def test_copied_folder_whose_link_fails_gets_no_success_notice(self) -> None:
        # Today's behaviour: the folder stays copied, but only the failure is reported.
        self.link_reply = RuntimeError("API failure")
        self.run_flow(True, True)
        self.assertEqual(self.events, [create_question(self.source_dir, self.dest), new_link_question(self.dest),
                                       self.saved(), link_failed(self.dest, self.link_reply)])
        self.assertTrue(Path(self.dest, "template-only.txt").is_file())

    def test_copied_and_linked_folder_without_a_card_callback(self) -> None:
        self.run_flow(True, True, callback=False)
        self.assertEqual([event[0] for event in self.events], ["ask", "ask", "update", "info"])


class FolderFlowContractTest(unittest.TestCase):
    def test_flow_requires_the_dialogs_by_keyword(self) -> None:
        parameter = inspect.signature(
            foldersHelpers.FolderEngines.generate_project_folder_from_template
        ).parameters["dialogs"]
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_folder_helpers_do_not_import_the_message_dialog(self) -> None:
        tree = ast.parse(Path(foldersHelpers.__file__).read_text(encoding="utf-8"))
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("messages_helper"):
                found.append(node.lineno)
            elif isinstance(node, ast.Import) and any(a.name.endswith("messages_helper") for a in node.names):
                found.append(node.lineno)
            elif isinstance(node, ast.Name) and node.id == "ModernMessageDialog":
                found.append(node.lineno)
        self.assertEqual(found, [])

    def test_real_dialogs_fit_the_protocol(self) -> None:
        for name in ("show_warning", "show_info", "ask_yes_no"):
            with self.subTest(name=name):
                wanted = list(inspect.signature(getattr(UserDialogs, name)).parameters.values())[1:]
                real = inspect.signature(getattr(ModernMessageDialog, name)).parameters
                for parameter in wanted:
                    self.assertIn(parameter.name, real)
                    self.assertEqual(real[parameter.name].kind, parameter.kind)
                extra = [p for p in real.values() if p.name not in {w.name for w in wanted}]
                self.assertTrue(all(p.default is not inspect.Parameter.empty for p in extra))


class ProjectCardFolderActionTest(unittest.TestCase):
    def setUp(self) -> None:
        mocks = {}
        stubs = [(ModernMessageDialog, name) for name in ("show_warning", "show_info", "show_error", "ask_yes_no")]
        stubs += [(projects_card_actions, name) for name in ("FolderEngines", "SettingsSetupGuard", "SettingsService")]
        for owner, name in stubs:
            patcher = patch.object(owner, name)
            mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)
        mocks["SettingsSetupGuard"].missing_project_folder_settings.return_value = []
        self.create = mocks["FolderEngines"].generate_project_folder_from_template

    def test_project_card_hands_the_real_dialogs_to_the_flow(self) -> None:
        host = SimpleNamespace(item_data={"id": "7", "name": "Nimi", "projectNumber": "P-1"},
                               update_files_path=Mock(), lang_manager=None, safe_parent_window=Mock())

        projects_card_actions.ProjectCardActions(host).generate_folder()

        self.create.assert_called_once()
        self.assertIs(self.create.call_args.kwargs["dialogs"], ModernMessageDialog)


if __name__ == "__main__":
    unittest.main()
