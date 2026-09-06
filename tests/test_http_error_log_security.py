from __future__ import annotations

import importlib.util
import os
import stat
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def _load_secure_log_io():
    module_path = ROOT / "Logs" / "secure_log_io.py"
    spec = importlib.util.spec_from_file_location("secure_log_io_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load secure_log_io for testing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


secure_log_io = _load_secure_log_io()


class HttpErrorSourceSecurityTest(unittest.TestCase):
    def test_http_response_body_never_enters_api_error_message(self) -> None:
        source = (ROOT / "python" / "api_client.py").read_text(encoding="utf-8")

        self.assertNotIn("response.text", source)
        self.assertEqual(
            source.count("raise Exception(self._http_status_error(response.status_code))"),
            2,
        )

    def test_both_disk_loggers_use_private_log_io(self) -> None:
        for relative_path in (
            Path("Logs/python_fail_logger.py"),
            Path("Logs/switch_logger.py"),
        ):
            with self.subTest(path=str(relative_path)):
                source = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("ensure_private_directory", source)
                self.assertIn("harden_private_file", source)
                self.assertIn("with open_private_log(path) as fh:", source)
                self.assertNotIn('with open(path, "a", encoding="utf-8")', source)


class SecureLogIoTest(unittest.TestCase):
    def test_private_log_can_be_appended_without_truncation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "nested" / "test.log"

            with secure_log_io.open_private_log(str(log_path)) as handle:
                handle.write("first\n")
            with secure_log_io.open_private_log(str(log_path)) as handle:
                handle.write("second\n")

            self.assertEqual(log_path.read_text(encoding="utf-8"), "first\nsecond\n")

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits are not Windows ACLs")
    def test_existing_directory_and_file_permissions_are_tightened(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            log_dir.mkdir(mode=0o755)
            log_path = log_dir / "existing.log"
            log_path.write_text("existing\n", encoding="utf-8")
            os.chmod(log_dir, 0o755)
            os.chmod(log_path, 0o644)

            secure_log_io.ensure_private_directory(str(log_dir))
            secure_log_io.harden_private_file(str(log_path))

            self.assertEqual(stat.S_IMODE(log_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
