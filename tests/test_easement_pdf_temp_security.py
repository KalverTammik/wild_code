from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.modules.easements import easement_pdf_service
from Kavitro_dev.modules.easements.easement_pdf_service import EasementPdfService


class EasementPdfTempSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="kavitro_easement_pdf_test_")
        self.temp_root = Path(self.temp_dir.name).resolve()
        EasementPdfService._owned_output_paths.clear()

    def tearDown(self) -> None:
        EasementPdfService._owned_output_paths.clear()
        self.temp_dir.cleanup()

    def _output_path(self, item_number: str = "436-2") -> Path:
        with patch.object(
            easement_pdf_service.tempfile,
            "gettempdir",
            return_value=str(self.temp_root),
        ):
            return EasementPdfService._output_pdf_path(
                item_number=item_number,
                item_id="item-1",
            )

    def test_same_item_uses_unique_private_directories(self) -> None:
        first = self._output_path()
        second = self._output_path()

        self.assertNotEqual(first.parent, second.parent)
        self.assertEqual(first.name, "436-2.pdf")
        self.assertEqual(second.name, "436-2.pdf")
        self.assertEqual(first.parent.parent, self.temp_root)
        self.assertEqual(second.parent.parent, self.temp_root)
        self.assertTrue(first.parent.name.startswith(EasementPdfService.OUTPUT_TEMP_PREFIX))
        self.assertTrue(second.parent.name.startswith(EasementPdfService.OUTPUT_TEMP_PREFIX))

        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(first.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(second.parent.stat().st_mode), 0o700)

        self.assertTrue(EasementPdfService.cleanup_output_pdf(first))
        self.assertTrue(EasementPdfService.cleanup_output_pdf(second))
        self.assertFalse(first.parent.exists())
        self.assertFalse(second.parent.exists())

    def test_legacy_fixed_directory_is_not_reused_or_removed(self) -> None:
        legacy_dir = self.temp_root / "kavitro_easement_drawings"
        legacy_dir.mkdir()
        marker = legacy_dir / "keep.txt"
        marker.write_text("legacy", encoding="utf-8")

        output = self._output_path()
        output.write_bytes(b"pdf")

        self.assertNotEqual(output.parent, legacy_dir)
        self.assertTrue(EasementPdfService.cleanup_output_pdf(output))
        self.assertEqual(marker.read_text(encoding="utf-8"), "legacy")

    def test_item_number_cannot_escape_unique_output_directory(self) -> None:
        output = self._output_path("../../outside\\drawing")

        self.assertEqual(output.parent.parent, self.temp_root)
        self.assertEqual(output.name, "outside_drawing.pdf")
        self.assertTrue(EasementPdfService.cleanup_output_pdf(output))

    def test_cleanup_refuses_unowned_paths(self) -> None:
        unowned = self.temp_root / "unowned.pdf"
        unowned.write_bytes(b"do not remove")

        self.assertFalse(EasementPdfService.cleanup_output_pdf(unowned))
        self.assertEqual(unowned.read_bytes(), b"do not remove")

    def test_cleanup_removes_only_registered_pdf_and_keeps_unknown_sibling(self) -> None:
        output = self._output_path()
        output.write_bytes(b"pdf")
        sibling = output.parent / "unknown.txt"
        sibling.write_text("keep", encoding="utf-8")

        self.assertTrue(EasementPdfService.cleanup_output_pdf(output))
        self.assertFalse(output.exists())
        self.assertEqual(sibling.read_text(encoding="utf-8"), "keep")
        self.assertTrue(output.parent.exists())

    def test_cleanup_refuses_pdf_symlink(self) -> None:
        output = self._output_path()
        target = self.temp_root / "target.txt"
        target.write_text("keep", encoding="utf-8")
        try:
            output.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"File symlinks are unavailable: {exc}")

        self.assertFalse(EasementPdfService.cleanup_output_pdf(output))
        self.assertTrue(output.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_failed_export_removes_partial_pdf_and_directory(self) -> None:
        captured_path: list[Path] = []

        class FailedExporter:
            Success = 0

            class PdfExportSettings:
                pass

            def __init__(self, _layout) -> None:
                pass

            def exportToPdf(self, path, _settings) -> int:
                output = Path(path)
                captured_path.append(output)
                output.write_bytes(b"partial")
                return 1

        ok, error = self._run_export(FailedExporter)

        self.assertFalse(ok)
        self.assertIn("code 1", error)
        self.assertEqual(len(captured_path), 1)
        self.assertFalse(captured_path[0].exists())
        self.assertFalse(captured_path[0].parent.exists())

    def test_export_exception_removes_partial_pdf_and_directory(self) -> None:
        captured_path: list[Path] = []

        class RaisingExporter:
            Success = 0

            class PdfExportSettings:
                pass

            def __init__(self, _layout) -> None:
                pass

            def exportToPdf(self, path, _settings) -> int:
                output = Path(path)
                captured_path.append(output)
                output.write_bytes(b"partial")
                raise RuntimeError("export interrupted")

        with patch.object(easement_pdf_service.PythonFailLogger, "log_exception"):
            ok, error = self._run_export(RaisingExporter)

        self.assertFalse(ok)
        self.assertEqual(error, "export interrupted")
        self.assertEqual(len(captured_path), 1)
        self.assertFalse(captured_path[0].exists())
        self.assertFalse(captured_path[0].parent.exists())

    def _run_export(self, exporter_class) -> tuple[bool, str]:
        final_layer = Mock()
        final_layer.isValid.return_value = True
        layout = object()
        map_item = Mock()
        map_item.scale.return_value = 1000.0
        template_path = Mock()
        template_path.exists.return_value = True

        with (
            patch.object(easement_pdf_service, "QgsProject") as project_class,
            patch.object(easement_pdf_service, "QgsLayoutExporter", exporter_class),
            patch.object(EasementPdfService, "_layer_features", return_value=[object()]),
            patch.object(EasementPdfService, "_template_path", return_value=template_path),
            patch.object(EasementPdfService, "_load_template_layout", return_value=layout),
            patch.object(EasementPdfService, "_resolve_map_item", return_value=map_item),
            patch.object(EasementPdfService, "_configure_map_item"),
            patch.object(EasementPdfService, "_configure_legend"),
            patch.object(EasementPdfService, "_measure_total_area_sqm", return_value=1.0),
            patch.object(EasementPdfService, "_set_label_text"),
            patch.object(EasementPdfService, "_property_summary_text", return_value="Property"),
            patch.object(
                easement_pdf_service.tempfile,
                "gettempdir",
                return_value=str(self.temp_root),
            ),
        ):
            project_class.instance.return_value = object()
            return EasementPdfService.export_final_cut_pdf(
                item_data={},
                item_id="item-1",
                item_number="436-2",
                item_name="Test",
                final_layer=final_layer,
            )


if __name__ == "__main__":
    unittest.main()
