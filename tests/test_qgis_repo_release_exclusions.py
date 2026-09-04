import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.qgis_repo_release import (
    DEFAULT_EXCLUDE_DIRS,
    _copy_repo_icon,
    _read_plugin_meta,
    _should_exclude,
)


ROOT = Path(__file__).resolve().parents[1]


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

    def test_release_metadata_copies_approved_kavitro_icon(self) -> None:
        approved_icon = Path("resources/icons/Kavitro-favicon-96x96.png")
        expected_bytes = (ROOT / approved_icon).read_bytes()

        with TemporaryDirectory() as temp_dir:
            plugin_root = Path(temp_dir) / "kavitro_live"
            icon_path = plugin_root / approved_icon
            icon_path.parent.mkdir(parents=True)
            icon_path.write_bytes(expected_bytes)
            (plugin_root / "metadata.txt").write_text(
                (ROOT / "metadata.release.txt").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            meta = _read_plugin_meta(plugin_root)
            output_dir = Path(temp_dir) / "release_repo"
            output_icon = _copy_repo_icon(
                plugin_root,
                meta,
                output_dir,
                repo_icon_name="kavitro_live.png",
            )

            self.assertEqual(meta.icon_path, approved_icon.as_posix())
            self.assertIsNotNone(output_icon)
            self.assertEqual(output_icon.read_bytes(), expected_bytes)


if __name__ == "__main__":
    unittest.main()
