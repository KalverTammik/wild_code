import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from utils.security_boundaries import (
    ALLOWED_EXTERNAL_FILE_EXTENSIONS,
    DESCRIPTION_LINK_BLOCKED,
    DESCRIPTION_LINK_LOCAL_PATH,
    DESCRIPTION_LINK_NETWORK_PATH,
    DESCRIPTION_LINK_WEB,
    classify_description_link,
    file_name_extension,
    is_same_or_descendant_path,
    normalize_file_extension,
    resolve_allowed_external_extension,
    resolve_direct_child_path,
    sanitize_path_component,
)


class ExternalFilePolicyTest(unittest.TestCase):
    def test_expected_business_document_extensions_are_allowed(self) -> None:
        expected = {
            "asice", "bdoc", "cad", "csv", "ddoc", "dgn", "doc", "docx",
            "dwg", "dxf", "mov", "mp4", "ods", "odt", "pdf", "rtf", "txt",
            "xls", "xlsx", "zip",
        }
        self.assertTrue(expected.issubset(ALLOWED_EXTERNAL_FILE_EXTENSIONS))

    def test_executable_and_browser_active_extensions_are_blocked(self) -> None:
        blocked = {
            "bat", "cmd", "com", "exe", "hta", "html", "js", "lnk", "msi",
            "ps1", "py", "scr", "svg", "url", "vbs",
        }
        for extension in blocked:
            with self.subTest(extension=extension):
                self.assertEqual(
                    resolve_allowed_external_extension(
                        api_extension=extension,
                        file_name=f"attachment.{extension}",
                    ),
                    "",
                )

    def test_api_extension_and_file_name_must_agree(self) -> None:
        self.assertEqual(
            resolve_allowed_external_extension(
                api_extension="pdf",
                file_name="invoice.pdf.exe",
            ),
            "",
        )
        self.assertEqual(
            resolve_allowed_external_extension(
                api_extension="jpeg",
                file_name="photo.jpg",
            ),
            "jpeg",
        )

    def test_missing_api_extension_can_use_allowlisted_file_name(self) -> None:
        self.assertEqual(
            resolve_allowed_external_extension(file_name="folder\\report.docx"),
            "docx",
        )

    def test_malformed_api_extension_is_not_recovered_from_file_name(self) -> None:
        for extension in ("../pdf", "pdf.exe", "pdf/../../exe", "..pdf"):
            with self.subTest(extension=extension):
                self.assertEqual(
                    resolve_allowed_external_extension(
                        api_extension=extension,
                        file_name="report.pdf",
                    ),
                    "",
                )

    def test_local_file_uses_its_real_extension(self) -> None:
        self.assertEqual(
            resolve_allowed_external_extension(
                api_extension="exe",
                file_name="malware.exe",
                local_file_path="C:\\Temp\\drawing.pdf",
            ),
            "pdf",
        )
        self.assertEqual(
            resolve_allowed_external_extension(local_file_path="C:\\Temp\\script.cmd"),
            "",
        )

    def test_extension_helpers_reject_path_syntax(self) -> None:
        self.assertEqual(normalize_file_extension(".PDF"), "pdf")
        self.assertEqual(normalize_file_extension("../../pdf"), "")
        self.assertEqual(file_name_extension("folder/subfolder/report.PDF"), "pdf")


class DescriptionLinkPolicyTest(unittest.TestCase):
    def test_http_and_https_are_preserved_as_web_targets(self) -> None:
        for url in (
            "https://tenant.sharepoint.com/sites/project/report",
            "http://intranet.local/project/report",
        ):
            with self.subTest(url=url):
                target = classify_description_link(url)
                self.assertEqual(target.kind, DESCRIPTION_LINK_WEB)
                self.assertEqual(target.target, url)

    @patch("utils.security_boundaries.windows_drive_type", return_value=3)
    def test_windows_drive_and_file_url_are_local_targets(self, _drive_type) -> None:
        for raw in (
            r"C:\Projects\Drawing.pdf",
            "file:///C:/Projects/Drawing.pdf",
            "file://localhost/C:/Projects/Drawing.pdf",
        ):
            with self.subTest(raw=raw):
                target = classify_description_link(raw)
                self.assertEqual(target.kind, DESCRIPTION_LINK_LOCAL_PATH)
                self.assertEqual(target.target, r"C:\Projects\Drawing.pdf")

    def test_unc_and_hosted_file_url_are_network_targets(self) -> None:
        for raw in (
            r"\\server\projects\Drawing.pdf",
            "//server/projects/Drawing.pdf",
            "file://server/projects/Drawing.pdf",
        ):
            with self.subTest(raw=raw):
                target = classify_description_link(raw)
                self.assertEqual(target.kind, DESCRIPTION_LINK_NETWORK_PATH)
                self.assertEqual(target.host, "server")
                self.assertEqual(target.target, r"\\server\projects\Drawing.pdf")

    @patch(
        "utils.security_boundaries.windows_mapped_drive_remote_name",
        return_value=r"\\fileserver\projects",
    )
    @patch("utils.security_boundaries.windows_drive_type", return_value=4)
    def test_mapped_drive_is_network_target(self, _drive_type, _remote_name) -> None:
        target = classify_description_link(r"Z:\Project\Drawing.pdf")
        self.assertEqual(target.kind, DESCRIPTION_LINK_NETWORK_PATH)
        self.assertEqual(target.host, "fileserver")
        self.assertEqual(target.target, r"Z:\Project\Drawing.pdf")

    def test_relative_paths_custom_schemes_and_device_paths_are_blocked(self) -> None:
        for raw in (
            "relative/report.pdf",
            "mailto:user@example.com",
            "ftp://example.com/report.pdf",
            "javascript:alert(1)",
            r"\\?\C:\Windows\system.ini",
            r"\\.\pipe\example",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(
                    classify_description_link(raw).kind,
                    DESCRIPTION_LINK_BLOCKED,
                )

    def test_file_url_with_encoded_control_character_is_blocked(self) -> None:
        target = classify_description_link("file:///C:/Projects/report%0A.pdf")
        self.assertEqual(target.kind, DESCRIPTION_LINK_BLOCKED)
        self.assertEqual(target.reason, "control_characters")

    @patch("utils.security_boundaries.os.path.exists")
    @patch("utils.security_boundaries.os.path.realpath")
    def test_classification_does_not_probe_the_filesystem(self, realpath, exists) -> None:
        target = classify_description_link(r"\\untrusted-server\share\report.pdf")
        self.assertEqual(target.kind, DESCRIPTION_LINK_NETWORK_PATH)
        exists.assert_not_called()
        realpath.assert_not_called()


class ProjectFolderPathBoundaryTest(unittest.TestCase):
    def test_path_syntax_is_flattened_to_one_component(self) -> None:
        for raw_name in (
            "../../Outside/Project",
            "..\\..\\Outside\\Project",
            "C:\\Outside\\Project",
            "\\\\server\\share\\Project",
        ):
            with self.subTest(raw_name=raw_name):
                safe_name = sanitize_path_component(raw_name)
                self.assertTrue(safe_name)
                self.assertNotIn("/", safe_name)
                self.assertNotIn("\\", safe_name)
                self.assertNotIn(":", safe_name)

    def test_windows_reserved_names_are_made_safe(self) -> None:
        for raw_name in ("CON", "con.txt", "NUL", "COM1", "LPT9"):
            with self.subTest(raw_name=raw_name):
                self.assertTrue(sanitize_path_component(raw_name).startswith("_"))

    def test_unicode_and_spaces_are_preserved(self) -> None:
        self.assertEqual(
            sanitize_path_component("  Pärnu maantee projekt  "),
            "Pärnu maantee projekt",
        )

    def test_empty_or_dot_name_uses_safe_fallback(self) -> None:
        self.assertEqual(
            sanitize_path_component("..", fallback="project-123"),
            "project-123",
        )

    def test_component_length_is_bounded(self) -> None:
        self.assertEqual(len(sanitize_path_component("a" * 500)), 120)

    def test_direct_child_rejects_unsanitized_paths(self) -> None:
        with TemporaryDirectory() as target_root:
            for unsafe_name in (
                "../Outside",
                "..\\Outside",
                "C:\\Outside",
                "\\\\server\\share\\Project",
            ):
                with self.subTest(unsafe_name=unsafe_name):
                    self.assertEqual(
                        resolve_direct_child_path(target_root, unsafe_name),
                        "",
                    )

    def test_sanitized_destination_is_target_roots_direct_child(self) -> None:
        with TemporaryDirectory() as target_root:
            safe_name = sanitize_path_component("..\\..\\Outside")
            destination = resolve_direct_child_path(target_root, safe_name)
            self.assertEqual(
                Path(destination).parent.resolve(),
                Path(target_root).resolve(),
            )

    def test_source_target_topology_can_be_detected(self) -> None:
        with TemporaryDirectory() as source_root:
            nested_target = Path(source_root) / "generated"
            nested_target.mkdir()
            self.assertTrue(is_same_or_descendant_path(nested_target, source_root))
            self.assertFalse(is_same_or_descendant_path(source_root, nested_target))


if __name__ == "__main__":
    unittest.main()
