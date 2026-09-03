import unittest

from utils.project_folder_rules import (
    MissingProjectNumberError,
    build_project_folder_name,
    resolve_project_number,
)


class ProjectNumberResolutionTest(unittest.TestCase):
    def test_graphql_number_field_is_supported(self) -> None:
        self.assertEqual(resolve_project_number({"number": "PR-2026-42"}), "PR-2026-42")

    def test_project_number_alias_remains_supported_and_takes_precedence(self) -> None:
        self.assertEqual(
            resolve_project_number(
                {
                    "projectNumber": "LEGACY-42",
                    "number": "CURRENT-42",
                }
            ),
            "LEGACY-42",
        )

    def test_empty_alias_falls_back_to_number(self) -> None:
        self.assertEqual(
            resolve_project_number(
                {
                    "projectNumber": "   ",
                    "number": "CURRENT-42",
                }
            ),
            "CURRENT-42",
        )

    def test_missing_number_returns_none(self) -> None:
        self.assertIsNone(resolve_project_number({"name": "Projekt"}))
        self.assertIsNone(resolve_project_number(None))


class ProjectFolderRuleRenderingTest(unittest.TestCase):
    def test_name_symbol_number_order_is_honored(self) -> None:
        self.assertEqual(
            build_project_folder_name(
                "PROJECT_NAME + SYMBOL(_) + PROJECT_NUMBER",
                project_name="Tamme tn 7, Sirmusti Liitumispunktide rajamine",
                project_number="PR-42",
            ),
            "Tamme tn 7, Sirmusti Liitumispunktide rajamine_PR-42",
        )

    def test_number_symbol_name_order_is_honored(self) -> None:
        self.assertEqual(
            build_project_folder_name(
                "PROJECT_NUMBER + SYMBOL(-) + PROJECT_NAME",
                project_name="Pärnu projekt",
                project_number="PR-42",
            ),
            "PR-42-Pärnu projekt",
        )

    def test_missing_rule_uses_default_number_name_order(self) -> None:
        self.assertEqual(
            build_project_folder_name(
                "",
                project_name="Projekt",
                project_number="PR-42",
            ),
            "PR-42Projekt",
        )

    def test_name_only_rule_does_not_require_number(self) -> None:
        self.assertEqual(
            build_project_folder_name(
                "PROJECT_NAME",
                project_name="Projekt",
                project_number=None,
            ),
            "Projekt",
        )

    def test_rule_requiring_missing_number_is_rejected(self) -> None:
        with self.assertRaises(MissingProjectNumberError):
            build_project_folder_name(
                "PROJECT_NAME + SYMBOL(_) + PROJECT_NUMBER",
                project_name="Projekt",
                project_number=None,
            )


if __name__ == "__main__":
    unittest.main()
