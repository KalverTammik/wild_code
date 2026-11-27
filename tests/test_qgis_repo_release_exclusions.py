import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from pyplugin_installer.version_compare import isCompatible

from tools.qgis_repo_release import (
    DEFAULT_EXCLUDE_DIRS,
    _copy_repo_icon,
    _read_plugin_meta,
    _should_exclude,
    _write_plugins_xml,
)


ROOT = Path(__file__).resolve().parents[1]


class QgisRepoReleaseExclusionsTest(unittest.TestCase):
    def test_sensitive_local_artifacts_have_ignore_rules(self) -> None:
        rules = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertTrue({"*.gpkg", ".env", ".env.*", "!.env.example"} <= rules)

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

    def test_geopackages_are_excluded_from_live_package(self) -> None:
        self.assertTrue(
            _should_exclude(
                "samples/operational-data.gpkg",
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

    def test_the_repository_offers_the_plugin_to_qgis_3_40_and_qgis_4(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plugin_root = Path(temp_dir) / "kavitro_live"
            plugin_root.mkdir()
            (plugin_root / "metadata.txt").write_text(
                (ROOT / "metadata.release.txt").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            xml_path = Path(temp_dir) / "plugins.xml"
            _write_plugins_xml(
                _read_plugin_meta(plugin_root), xml_path, "https://example.invalid/a.zip", "a.zip", None
            )
            plugin = ElementTree.parse(xml_path).getroot().find("pyqgis_plugin")
            minimum = plugin.findtext("qgis_minimum_version")
            maximum = plugin.findtext("qgis_maximum_version")

        # QGIS' own rule, as its plugin installer applies it
        for version in ("3.40.0", "3.44.15", "4.0.0", "4.4.0"):
            self.assertTrue(isCompatible(version, minimum, maximum), version)
        for version in ("3.34.0", "5.0.0"):
            self.assertFalse(isCompatible(version, minimum, maximum), version)

    def test_dev_and_live_metadata_declare_the_same_qgis_support(self) -> None:
        def support(name: str) -> list:
            lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
            return [line for line in lines if line.startswith(("qgisM", "supportsQt6"))]

        self.assertEqual(support("metadata.txt"), support("metadata.release.txt"))
        self.assertIn("supportsQt6=True", support("metadata.txt"))


if __name__ == "__main__":
    unittest.main()
