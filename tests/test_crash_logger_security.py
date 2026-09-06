from __future__ import annotations

import importlib.util
import io
import os
import stat
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TEST_PACKAGE = "_kavitro_crash_logs_under_test"


def _load_logs_module(module_name: str):
    package = sys.modules.get(TEST_PACKAGE)
    if package is None:
        package = types.ModuleType(TEST_PACKAGE)
        package.__path__ = [str(ROOT / "Logs")]
        sys.modules[TEST_PACKAGE] = package

    qualified_name = f"{TEST_PACKAGE}.{module_name}"
    existing = sys.modules.get(qualified_name)
    if existing is not None:
        return existing

    module_path = ROOT / "Logs" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_name} for testing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


_load_logs_module("secure_log_io")
crash_logger_module = _load_logs_module("crash_logger")
CrashLogger = crash_logger_module.CrashLogger


class FakeFaultHandler:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled
        self.fail_disable = False
        self.file = None
        self.enable_calls = 0
        self.disable_calls = 0

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self, file, *, all_threads: bool) -> None:
        self.enable_calls += 1
        self.enabled = True
        self.file = file
        self.all_threads = all_threads

    def disable(self) -> bool:
        if self.fail_disable:
            raise RuntimeError("disable failed")
        self.disable_calls += 1
        was_enabled = self.enabled
        self.enabled = False
        return was_enabled


class CrashLoggerSecurityTest(unittest.TestCase):
    def test_start_is_unique_idempotent_and_clean_stop_removes_empty_log(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fault_handler = FakeFaultHandler()
            logger = CrashLogger(log_dir=str(Path(temp_dir) / "CrashLogs"), fault_handler=fault_handler)

            first_path = logger.start()
            self.assertIsNotNone(first_path)
            self.assertTrue(Path(first_path).is_file())
            self.assertEqual(logger.start(), first_path)
            self.assertEqual(fault_handler.enable_calls, 1)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(Path(first_path).stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(Path(first_path).parent.stat().st_mode), 0o700)

            logger.stop()

            self.assertFalse(Path(first_path).exists())
            self.assertEqual(fault_handler.disable_calls, 1)
            self.assertTrue(fault_handler.file.closed)

            second_path = logger.start()
            self.assertIsNotNone(second_path)
            self.assertNotEqual(second_path, first_path)
            logger.stop()

    def test_non_empty_crash_log_is_retained_and_discoverable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fault_handler = FakeFaultHandler()
            logger = CrashLogger(log_dir=str(Path(temp_dir) / "CrashLogs"), fault_handler=fault_handler)
            path = logger.start()

            fault_handler.file.write("Fatal Python error: test\n")
            fault_handler.file.flush()
            logger.stop()

            self.assertTrue(Path(path).is_file())
            self.assertEqual(logger.latest_log_path(), path)

    def test_existing_host_faulthandler_is_not_overwritten_or_disabled(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fault_handler = FakeFaultHandler(enabled=True)
            log_dir = Path(temp_dir) / "CrashLogs"
            logger = CrashLogger(log_dir=str(log_dir), fault_handler=fault_handler)

            self.assertIsNone(logger.start())
            logger.stop()

            self.assertTrue(fault_handler.enabled)
            self.assertEqual(fault_handler.enable_calls, 0)
            self.assertEqual(fault_handler.disable_calls, 0)
            self.assertFalse(log_dir.exists())

    def test_disable_failure_keeps_owned_file_open_for_a_safe_retry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fault_handler = FakeFaultHandler()
            logger = CrashLogger(log_dir=str(Path(temp_dir) / "CrashLogs"), fault_handler=fault_handler)
            path = logger.start()
            handle = fault_handler.file
            fault_handler.fail_disable = True

            with patch.object(crash_logger_module.sys, "stderr", io.StringIO()):
                logger.stop()

            self.assertTrue(fault_handler.enabled)
            self.assertFalse(handle.closed)
            self.assertEqual(logger.current_path, path)

            fault_handler.fail_disable = False
            logger.stop()
            self.assertTrue(handle.closed)
            self.assertFalse(Path(path).exists())

    def test_predictable_legacy_temp_file_is_never_touched(self) -> None:
        with TemporaryDirectory() as temp_dir:
            legacy_path = Path(temp_dir) / "kavitro_crash.log"
            legacy_path.write_text("keep this evidence", encoding="utf-8")
            logger = CrashLogger(
                log_dir=str(Path(temp_dir) / "CrashLogs"),
                fault_handler=FakeFaultHandler(),
            )

            logger.start()
            logger.stop()

            self.assertEqual(legacy_path.read_text(encoding="utf-8"), "keep this evidence")

    def test_only_three_newest_non_empty_crash_logs_are_retained(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "CrashLogs"
            log_dir.mkdir()
            for index in range(5):
                path = log_dir / f"kavitro_crash_old_{index}.log"
                path.write_text(f"crash {index}", encoding="utf-8")
                os.utime(path, (100 + index, 100 + index))

            fault_handler = FakeFaultHandler()
            logger = CrashLogger(log_dir=str(log_dir), fault_handler=fault_handler)
            current_path = logger.start()
            fault_handler.file.write("current crash\n")
            fault_handler.file.flush()
            logger.stop()

            retained = sorted(log_dir.glob("kavitro_crash_*.log"))
            self.assertEqual(len(retained), 3)
            self.assertIn(Path(current_path), retained)
            self.assertTrue((log_dir / "kavitro_crash_old_4.log").exists())
            self.assertTrue((log_dir / "kavitro_crash_old_3.log").exists())

    def test_main_has_no_import_time_crash_log_side_effect(self) -> None:
        source = (ROOT / "main.py").read_text(encoding="utf-8")

        self.assertNotIn("tempfile.gettempdir()", source)
        self.assertNotIn("_CRASH_LOG_HANDLE", source)
        self.assertNotIn("CRASH_LOG_PATH", source)
        self.assertIn("self._crash_logger.start()", source)
        self.assertIn("self._crash_logger.stop()", source)


if __name__ == "__main__":
    unittest.main()
