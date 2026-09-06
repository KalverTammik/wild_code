from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QApplication, QLabel

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog
from Kavitro_dev.widgets.DataDisplayWidgets import TaskFilePreviewDialog as preview_module


class FileMetadataHtmlSecurityTest(unittest.TestCase):
    MALICIOUS_NAME = '</b><br><font color="red">FAKE WARNING</font><b>.pdf'

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _dialog(self, **file_info) -> TaskFilePreviewDialog:
        payload = {
            "uuid": "file-1",
            "fileName": "report.pdf",
            "mimeType": "application/pdf",
            "ext": "pdf",
            "humanReadableSize": "10 KB",
            "uploader": {"displayName": "Jane User"},
        }
        payload.update(file_info)
        with (
            patch.object(TaskFilePreviewDialog, "_load_preview"),
            patch.object(preview_module.ThemeManager, "apply_module_style"),
        ):
            return TaskFilePreviewDialog(
                file_info=payload,
                lang_manager=LanguageManager(),
            )

    @staticmethod
    def _rendered_plain_text(rich_text: str) -> str:
        document = QTextDocument()
        document.setHtml(rich_text)
        return document.toPlainText()

    def test_all_remote_metadata_values_are_html_escaped(self) -> None:
        dialog = self._dialog(
            fileName=self.MALICIOUS_NAME,
            mimeType='<img src="file:///private.png">',
            humanReadableSize="</b><br>FAKE SIZE<b>",
            uploader={"displayName": '<a href="https://evil.example">FAKE USER</a>'},
        )
        self.addCleanup(dialog.close)

        rich_text = dialog._meta_label.text()
        rendered = self._rendered_plain_text(rich_text)

        self.assertEqual(dialog._meta_label.textFormat(), Qt.RichText)
        self.assertNotIn('<font color="red">', rich_text)
        self.assertNotIn('<img src="file:///private.png">', rich_text)
        self.assertNotIn('<a href="https://evil.example">', rich_text)
        self.assertIn(self.MALICIOUS_NAME, rendered)
        self.assertIn('<img src="file:///private.png">', rendered)
        self.assertIn("</b><br>FAKE SIZE<b>", rendered)
        self.assertIn('<a href="https://evil.example">FAKE USER</a>', rendered)

    def test_normal_metadata_keeps_existing_visual_text(self) -> None:
        dialog = self._dialog(
            fileName="Report & drawing.pdf",
            uploader={"displayName": "Jane & John"},
        )
        self.addCleanup(dialog.close)

        self.assertEqual(
            self._rendered_plain_text(dialog._meta_label.text()),
            "Report & drawing.pdf\napplication/pdf • 10 KB • Jane & John",
        )

    def test_preview_placeholder_and_notice_are_plain_text(self) -> None:
        dialog = self._dialog()
        self.addCleanup(dialog.close)
        malicious = '<font color="red">FAKE WARNING</font>'

        dialog._set_notice(malicious)
        self.assertEqual(dialog._notice_label.textFormat(), Qt.PlainText)
        self.assertEqual(dialog._notice_label.text(), malicious)

        dialog._show_placeholder(malicious)
        placeholder = dialog._content_layout.itemAt(0).widget()
        self.assertIsInstance(placeholder, QLabel)
        self.assertEqual(placeholder.textFormat(), Qt.PlainText)
        self.assertEqual(placeholder.text(), malicious)

    def test_external_open_confirmation_treats_file_name_as_plain_text(self) -> None:
        dialog = self._dialog(fileName=self.MALICIOUS_NAME)
        self.addCleanup(dialog.close)

        with patch.object(
            preview_module.ModernMessageDialog,
            "ask_choice_modern",
            return_value=None,
        ) as ask_choice:
            dialog._open_externally()

        safe_message = ask_choice.call_args.args[1]
        rendered = self._rendered_plain_text(safe_message)
        self.assertIn(self.MALICIOUS_NAME, rendered)
        self.assertIn("Ava ainult siis", rendered)
        self.assertNotIn('<font color="red">', safe_message)
        self.assertNotIn("\N{NO-BREAK SPACE}", safe_message)


if __name__ == "__main__":
    unittest.main()
