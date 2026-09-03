import unittest
from functools import partial

from ui.modules_registry import _adapt_value_editor


class ModuleLabelCallbackTest(unittest.TestCase):
    def test_value_editor_receives_only_current_value(self) -> None:
        received = []

        def open_dialog(lang_manager, parent, dialog_class, accepted_value, current_value):
            received.append(
                (lang_manager, parent, dialog_class, accepted_value, current_value)
            )
            return "PROJECT_NUMBER + SYMBOL(_) + PROJECT_NAME"

        bound_editor = partial(
            open_dialog,
            "language-manager",
            "parent-dialog",
            "folder-rule-dialog",
            "accepted",
        )
        callback = _adapt_value_editor(bound_editor)

        result = callback("project", "name structure rule", "PROJECT_NAME")

        self.assertEqual(
            received,
            [
                (
                    "language-manager",
                    "parent-dialog",
                    "folder-rule-dialog",
                    "accepted",
                    "PROJECT_NAME",
                )
            ],
        )
        self.assertEqual(
            result,
            "PROJECT_NUMBER + SYMBOL(_) + PROJECT_NAME",
        )

    def test_empty_unset_value_is_forwarded(self) -> None:
        callback = _adapt_value_editor(lambda current_value: current_value)

        self.assertEqual(callback("project", "name structure rule", ""), "")


if __name__ == "__main__":
    unittest.main()
