from __future__ import annotations

import io
import os
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.resolve_release_values import (
    ReleaseValueError,
    main,
    resolve_release_values,
    write_github_outputs,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "qgis_release.yml"
SETUP_GUIDE_PATH = ROOT / "MAIN_PLUGIN_RELEASE_SETUP.md"
RELEASE_METADATA_PATH = ROOT / "metadata.release.txt"
APPROVED_RELEASE_ICON = "resources/icons/Kavitro-favicon-96x96.png"


def _run_scripts(yaml_text: str) -> list[str]:
    """Extract inline and block run scripts without requiring a YAML package."""
    lines = yaml_text.splitlines()
    scripts = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue

        run_indent = len(match.group(1))
        value = match.group(2).strip()
        if value not in ("|", "|-", ">", ">-"):
            scripts.append(value)
            index += 1
            continue

        block = []
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= run_indent:
                break
            block.append(line)
            index += 1
        scripts.append("\n".join(block))
    return scripts


class ReleaseValueResolverTest(unittest.TestCase):
    def test_release_event_derives_version_from_valid_tag(self) -> None:
        version, tag = resolve_release_values(
            {
                "GITHUB_EVENT_NAME": "release",
                "PLUGIN_RELEASE_EVENT_TAG": "V2.02.15",
            }
        )

        self.assertEqual(version, "2.02.15")
        self.assertEqual(tag, "V2.02.15")

    def test_manual_short_versions_are_normalized(self) -> None:
        cases = {
            "2": ("2.0.0", "v2.0.0"),
            "2.4": ("2.4.0", "v2.4.0"),
            ".v2.4.6": ("2.4.6", "v2.4.6"),
            "2.4.6-beta.1": ("2.4.6-beta.1", "v2.4.6-beta.1"),
        }
        for raw_version, expected in cases.items():
            with self.subTest(raw_version=raw_version):
                self.assertEqual(
                    resolve_release_values(
                        {
                            "GITHUB_EVENT_NAME": "workflow_dispatch",
                            "PLUGIN_INPUT_RELEASE_VERSION": raw_version,
                            "PLUGIN_INPUT_RELEASE_TAG": "",
                        }
                    ),
                    expected,
                )

    def test_manual_tag_override_is_preserved_after_validation(self) -> None:
        version, tag = resolve_release_values(
            {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "PLUGIN_INPUT_RELEASE_VERSION": "3.1.4",
                "PLUGIN_INPUT_RELEASE_TAG": "V3.01.04",
            }
        )

        self.assertEqual(version, "3.1.4")
        self.assertEqual(tag, "V3.01.04")

    def test_shell_and_output_injection_versions_are_rejected(self) -> None:
        unsafe_versions = (
            "2.0.0;echo-pwned",
            "2.0.0-$(id)",
            "2.0.0-`id`",
            "2.0.0|id",
            "2.0.0&id",
            '2.0.0";id;"',
            "2.0.0\nrelease_tag=v9.9.9",
            "2.0.0-beta_1",
            "2.0.0-../../payload",
        )
        for raw_version in unsafe_versions:
            with self.subTest(raw_version=raw_version):
                with self.assertRaises(ReleaseValueError):
                    resolve_release_values(
                        {
                            "GITHUB_EVENT_NAME": "workflow_dispatch",
                            "PLUGIN_INPUT_RELEASE_VERSION": raw_version,
                        }
                    )

    def test_shell_and_output_injection_tags_are_rejected(self) -> None:
        unsafe_tags = (
            "v2.0.0;id",
            "v2.0.0-$(id)",
            "v2.0.0`id`",
            "v2.0.0\nrelease_version=9.9.9",
            "refs/tags/v2.0.0",
        )
        for raw_tag in unsafe_tags:
            with self.subTest(raw_tag=raw_tag):
                with self.assertRaises(ReleaseValueError):
                    resolve_release_values(
                        {
                            "GITHUB_EVENT_NAME": "release",
                            "PLUGIN_RELEASE_EVENT_TAG": raw_tag,
                        }
                    )

    def test_only_validated_single_line_outputs_are_written(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "github-output.txt"
            write_github_outputs(str(output_path), "2.4.6-beta.1", "v2.4.6-beta.1")

            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                [
                    "release_version=2.4.6-beta.1",
                    "release_tag=v2.4.6-beta.1",
                ],
            )

    def test_cli_error_does_not_echo_rejected_input(self) -> None:
        rejected = "2.0.0\n::warning::injected"
        stderr = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {
                    "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "PLUGIN_INPUT_RELEASE_VERSION": rejected,
                    "PLUGIN_INPUT_RELEASE_TAG": "",
                    "GITHUB_OUTPUT": "unused-on-validation-failure",
                },
                clear=True,
            ),
            patch("sys.stderr", stderr),
        ):
            exit_code = main()

        self.assertEqual(exit_code, 1)
        self.assertNotIn(rejected, stderr.getvalue())
        self.assertNotIn("::warning::", stderr.getvalue())

    def test_cli_writes_validated_outputs_from_environment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "github-output.txt"
            with patch.dict(
                os.environ,
                {
                    "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "PLUGIN_INPUT_RELEASE_VERSION": "2.5",
                    "PLUGIN_INPUT_RELEASE_TAG": "",
                    "GITHUB_OUTPUT": str(output_path),
                },
                clear=True,
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                ["release_version=2.5.0", "release_tag=v2.5.0"],
            )


class ReleaseWorkflowSourceTest(unittest.TestCase):
    def test_workflow_run_scripts_have_no_github_expressions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        scripts = _run_scripts(workflow)

        self.assertTrue(scripts)
        for script in scripts:
            with self.subTest(script=script[:80]):
                self.assertNotIn("${{", script)

    def test_workflow_uses_environment_boundary_and_resolver(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("PLUGIN_INPUT_RELEASE_VERSION: ${{ inputs.release_version }}", workflow)
        self.assertIn("PLUGIN_INPUT_RELEASE_TAG: ${{ inputs.release_tag }}", workflow)
        self.assertIn("run: python tools/resolve_release_values.py", workflow)
        self.assertIn('os.environ["PLUGIN_RELEASE_VERSION"]', workflow)
        self.assertNotIn('RELEASE_TAG="${{', workflow)
        self.assertNotIn('release_version = "${{', workflow)
        self.assertNotIn('qgis-plugin-ci release "${{', workflow)

    def test_workflow_publishes_only_a_verified_empty_draft(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertNotIn("types:\n      - published", workflow)
        self.assertIn("Release ${PLUGIN_RELEASE_TAG} is already published", workflow)
        self.assertIn(".assets | length", workflow)
        self.assertIn("Verify uploaded release asset digests", workflow)
        self.assertIn("sha256sum", workflow)
        self.assertIn(".digest // empty", workflow)
        self.assertIn("uploads.github.com/repos/${GITHUB_REPOSITORY}/releases/${PLUGIN_RELEASE_ID}/assets", workflow)
        self.assertIn("REMOTE_ASSET_COUNT", workflow)
        self.assertIn('"repos/${GITHUB_REPOSITORY}/git/refs"', workflow)
        self.assertIn('-f ref="${TAG_REF}"', workflow)
        self.assertGreaterEqual(workflow.count('-f tag_name="${PLUGIN_RELEASE_TAG}"'), 2)
        self.assertIn("Draft release did not retain the requested tag name", workflow)
        self.assertIn("Published release is not associated with the requested tag", workflow)
        self.assertIn("EXPECTED_DOWNLOAD_SEGMENT", workflow)
        self.assertNotIn("gh release upload", workflow)
        self.assertNotIn("--clobber", workflow)
        self.assertNotIn("qgis-plugin-ci release", workflow)

        upload_index = workflow.index("- name: Upload repository assets to release")
        verify_index = workflow.index("- name: Verify uploaded release asset digests")
        publish_index = workflow.index("- name: Publish and lock release")
        immutable_index = workflow.index("'.immutable'", publish_index)
        self.assertLess(upload_index, verify_index)
        self.assertLess(verify_index, publish_index)
        self.assertGreater(immutable_index, publish_index)

    def test_release_metadata_is_live_icon_source_of_truth(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        release_metadata = RELEASE_METADATA_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "cp metadata.release.txt kavitro_live/metadata.txt",
            workflow,
        )
        self.assertIn(f"icon={APPROVED_RELEASE_ICON}", release_metadata)
        self.assertIn(f"icon={APPROVED_RELEASE_ICON}", workflow)
        self.assertTrue((ROOT / APPROVED_RELEASE_ICON).is_file())

    def test_documented_workflow_has_no_expressions_in_run_scripts(self) -> None:
        guide = SETUP_GUIDE_PATH.read_text(encoding="utf-8")
        workflow_start = guide.index("```yaml", guide.index("## 4) Release Workflow"))
        workflow_end = guide.index("```", workflow_start + len("```yaml"))
        documented_workflow = guide[workflow_start + len("```yaml"):workflow_end]

        scripts = _run_scripts(documented_workflow)
        self.assertTrue(scripts)
        for script in scripts:
            with self.subTest(script=script[:80]):
                self.assertNotIn("${{", script)
        self.assertIn("run: python tools/resolve_release_values.py", documented_workflow)
        self.assertNotIn("--clobber", documented_workflow)
        self.assertIn("draft=false", documented_workflow)
        self.assertIn(".immutable", documented_workflow)


if __name__ == "__main__":
    unittest.main()
