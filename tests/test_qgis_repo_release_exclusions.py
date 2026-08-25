import unittest

from tools.qgis_repo_release import DEFAULT_EXCLUDE_DIRS, _should_exclude


class QgisRepoReleaseExclusionsTest(unittest.TestCase):
    def test_internal_guides_are_excluded_from_live_package(self) -> None:
        self.assertTrue(
            _should_exclude(
                "docs/juhendid/01_seadistuste_mooduli_kasutamine.md",
                exclude_dirs=DEFAULT_EXCLUDE_DIRS,
            )
        )

    def test_runtime_module_is_not_excluded_from_live_package(self) -> None:
        self.assertFalse(
            _should_exclude(
                "modules/Settings/SettingsUI.py",
                exclude_dirs=DEFAULT_EXCLUDE_DIRS,
            )
        )

    def test_local_release_output_is_not_packaged_into_itself(self) -> None:
        self.assertTrue(
            _should_exclude(
                "release_repo/Kavitro_dev.2.00.05.zip",
                exclude_dirs=DEFAULT_EXCLUDE_DIRS,
            )
        )


if __name__ == "__main__":
    unittest.main()
