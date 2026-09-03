from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication

from Kavitro_dev.languages.translation_keys import TranslationKeys


html_description_module = importlib.import_module(
    "Kavitro_dev.widgets.DataDisplayWidgets.HtmlDescriptionWidget"
)
HtmlDescriptionWidget = html_description_module.HtmlDescriptionWidget


class StubLanguageManager:
    _TRANSLATIONS = {
        TranslationKeys.YES: "Yes",
        TranslationKeys.NO: "No",
        TranslationKeys.CONFIRM: "Confirm",
        TranslationKeys.WARNING: "Warning",
        TranslationKeys.ERROR: "Error",
        TranslationKeys.DESCRIPTION_LINK_WEB_CONFIRM: "Web: {url}{http_warning}",
        TranslationKeys.DESCRIPTION_LINK_HTTP_WARNING: " HTTP warning",
        TranslationKeys.DESCRIPTION_LINK_FOLDER_CONFIRM: "Folder: {path}",
        TranslationKeys.DESCRIPTION_LINK_NETWORK_CONFIRM: "Network: {host} {path}",
        TranslationKeys.DESCRIPTION_LINK_FILE_CONFIRM: "File: {path} .{extension}",
        TranslationKeys.DESCRIPTION_LINK_BLOCKED: "Blocked: {target}",
        TranslationKeys.DESCRIPTION_LINK_NOT_FOUND: "Not found: {target}",
        TranslationKeys.DESCRIPTION_LINK_OPEN_FAILED: "Open failed: {target}",
    }

    def translate(self, key) -> str:
        return self._TRANSLATIONS.get(key, str(key))


class HtmlDescriptionLinkPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _widget(self) -> HtmlDescriptionWidget:
        return HtmlDescriptionWidget(
            '<a href="https://example.com">Example</a>',
            lang_manager=StubLanguageManager(),
        )

    def test_qtextbrowser_automatic_link_opening_is_disabled(self) -> None:
        widget = self._widget()
        self.assertFalse(widget.openLinks())
        self.assertFalse(widget.openExternalLinks())

    def test_confirmed_https_link_opens_in_default_browser(self) -> None:
        widget = self._widget()
        with (
            patch.object(
                html_description_module.ModernMessageDialog,
                "ask_choice_modern",
                return_value="Yes",
            ) as ask_choice,
            patch.object(
                html_description_module.QDesktopServices,
                "openUrl",
                return_value=True,
            ) as open_url,
        ):
            widget._handle_anchor_clicked(QUrl("https://tenant.sharepoint.com/sites/project"))

        ask_choice.assert_called_once()
        self.assertEqual(ask_choice.call_args.kwargs["default"], "No")
        open_url.assert_called_once()

    def test_declined_network_link_does_not_probe_the_filesystem(self) -> None:
        widget = self._widget()
        with (
            patch.object(
                html_description_module.ModernMessageDialog,
                "ask_choice_modern",
                return_value="No",
            ),
            patch.object(html_description_module.os.path, "exists") as exists,
        ):
            widget._handle_anchor_clicked(QUrl("file://untrusted-server/share/report.pdf"))

        exists.assert_not_called()

    def test_network_link_is_probed_only_after_confirmation(self) -> None:
        widget = self._widget()
        state = {"confirmed": False}

        def confirm(*_args, **_kwargs):
            state["confirmed"] = True
            return "Yes"

        def exists_after_confirmation(_path):
            self.assertTrue(state["confirmed"])
            return False

        with (
            patch.object(
                html_description_module.ModernMessageDialog,
                "ask_choice_modern",
                side_effect=confirm,
            ),
            patch.object(
                html_description_module.ModernMessageDialog,
                "show_warning",
            ) as show_warning,
            patch.object(
                html_description_module.os.path,
                "exists",
                side_effect=exists_after_confirmation,
            ) as exists,
        ):
            widget._handle_anchor_clicked(QUrl("file://fileserver/share/report.pdf"))

        exists.assert_called_once_with(r"\\fileserver\share\report.pdf")
        show_warning.assert_called_once()

    def test_allowlisted_local_text_file_opens_internal_preview(self) -> None:
        widget = self._widget()
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "readme.txt"
            path.write_text("preview", encoding="utf-8")
            preview_dialog = Mock()

            with patch.object(
                html_description_module.TaskFilePreviewDialog,
                "open_preview",
                return_value=preview_dialog,
            ) as open_preview:
                widget._handle_anchor_clicked(QUrl.fromLocalFile(str(path)))

        open_preview.assert_called_once()
        preview_dialog.exec_.assert_called_once_with()

    def test_allowlisted_non_preview_file_requires_confirmation(self) -> None:
        widget = self._widget()
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "contract.docx"
            path.write_bytes(b"test")

            with (
                patch.object(
                    html_description_module.ModernMessageDialog,
                    "ask_choice_modern",
                    return_value="Yes",
                ) as ask_choice,
                patch.object(
                    html_description_module.TaskFilePreviewDialog,
                    "open_in_default_application",
                    return_value=True,
                ) as open_external,
            ):
                widget._handle_anchor_clicked(QUrl.fromLocalFile(str(path)))

        ask_choice.assert_called_once()
        open_external.assert_called_once_with(
            local_file_path=str(path),
            user_confirmed=True,
        )

    def test_blocked_local_executable_is_not_handed_to_the_os(self) -> None:
        widget = self._widget()
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.exe"
            path.write_bytes(b"test")

            with (
                patch.object(
                    html_description_module.ModernMessageDialog,
                    "show_warning",
                ) as show_warning,
                patch.object(
                    html_description_module.TaskFilePreviewDialog,
                    "open_in_default_application",
                ) as open_external,
            ):
                widget._handle_anchor_clicked(QUrl.fromLocalFile(str(path)))

        show_warning.assert_called_once()
        open_external.assert_not_called()

    def test_local_folder_requires_confirmation_before_file_manager(self) -> None:
        widget = self._widget()
        with TemporaryDirectory() as temp_dir:
            with (
                patch.object(
                    html_description_module.ModernMessageDialog,
                    "ask_choice_modern",
                    return_value="No",
                ),
                patch.object(
                    html_description_module.QDesktopServices,
                    "openUrl",
                ) as open_url,
            ):
                widget._handle_anchor_clicked(QUrl.fromLocalFile(temp_dir))

        open_url.assert_not_called()

    def test_qurl_encoded_raw_windows_paths_reach_the_path_classifier(self) -> None:
        widget = self._widget()
        with (
            patch.object(
                html_description_module,
                "classify_description_link",
                wraps=html_description_module.classify_description_link,
            ) as classify,
            patch.object(
                html_description_module.ModernMessageDialog,
                "show_warning",
            ),
        ):
            widget._handle_anchor_clicked(QUrl(r"C:\Projects\missing.pdf"))

        classified_values = [call.args[0] for call in classify.call_args_list]
        self.assertIn(
            r"c:\projects\missing.pdf",
            [value.casefold() for value in classified_values],
        )

    def test_qurl_encoded_raw_unc_path_is_still_confirmed_as_network(self) -> None:
        widget = self._widget()
        with (
            patch.object(
                html_description_module.ModernMessageDialog,
                "ask_choice_modern",
                return_value="No",
            ) as ask_choice,
            patch.object(html_description_module.os.path, "exists") as exists,
        ):
            widget._handle_anchor_clicked(QUrl(r"\\server\share\report.pdf"))

        ask_choice.assert_called_once()
        exists.assert_not_called()


if __name__ == "__main__":
    unittest.main()
