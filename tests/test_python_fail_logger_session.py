import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger


class PythonFailLoggerSessionTest(unittest.TestCase):
    """Log files belong to a plugin session; code run without one must not touch the user's logs."""

    def setUp(self) -> None:
        self._saved = (PythonFailLogger._session_started, dict(PythonFailLogger._log_paths))
        self.addCleanup(self._restore)
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = patch.object(PythonFailLogger, "_base_dir", staticmethod(lambda: self.tmp.name))
        base.start()
        self.addCleanup(base.stop)

    def _restore(self) -> None:
        PythonFailLogger._session_started, PythonFailLogger._log_paths = self._saved

    def written(self):
        return sorted(
            os.path.relpath(os.path.join(folder, name), self.tmp.name)
            for folder, _dirs, names in os.walk(self.tmp.name) for name in names
        )

    def test_without_a_session_nothing_is_written_or_rotated(self) -> None:
        # No earlier test may leave a session open, or the rest of the suite writes real logs.
        self.assertFalse(self._saved[0])
        folder = os.path.join(self.tmp.name, "Logs", "PythonLogs", "general")
        os.makedirs(folder)
        old = [os.path.join(folder, f"python_api_log_0{i}.log") for i in (1, 2)]
        for path in old:
            open(path, "w").close()

        PythonFailLogger.log("api_network_error", module="api", message="offline")
        PythonFailLogger.log_exception(RuntimeError("boom"), module="property")

        self.assertEqual(self.written(), sorted(os.path.relpath(p, self.tmp.name) for p in old))

    def test_a_started_session_writes_into_the_plugin_log_folder(self) -> None:
        PythonFailLogger._session_started = False
        with patch.object(PythonFailLogger, "_install_excepthook"):
            PythonFailLogger.start_session()

        PythonFailLogger.log("api_network_error", module="api", message="offline")

        files = self.written()
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith(os.path.join("Logs", "PythonLogs", "general", "python_api_log_")))
        with open(os.path.join(self.tmp.name, files[0]), encoding="utf-8") as fh:
            self.assertIn("api_network_error module=api message=offline", fh.read())


if __name__ == "__main__":
    unittest.main()
