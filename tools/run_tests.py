"""Run the offline test suite with QGIS' Python, without a QGIS window.

    $env:QT_QPA_PLATFORM = "offscreen"
    & "C:\\Program Files\\QGIS 3.40.13\\bin\\python-qgis-ltr.bat" tools/run_tests.py [pattern]

The plugin root and QGIS' own plugins folder (for ``processing``) go on ``sys.path``,
because some tests import ``tests.…``, ``utils.…`` or ``python.…`` from the root.
The run happens in a temporary folder: tests that build memory layers with geometry make
QGIS write ``symbology-style.db`` into the current folder, which must not land in the plugin.
The exit code is the suite's; a crash at shutdown after "OK" still shows as non-zero.
"""
import os
import shutil
import sys
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "test*.py"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, PLUGIN_ROOT)
    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        sys.path.insert(0, os.path.join(prefix, "python", "plugins"))
    work_dir = tempfile.mkdtemp(prefix="kavitro_tests_")
    os.chdir(work_dir)
    try:
        program = unittest.main(
            module=None,
            argv=["unittest", "discover", "-s", os.path.join(PLUGIN_ROOT, "tests"), "-p", pattern],
            exit=False,
        )
        return 0 if program.result.wasSuccessful() else 1
    finally:
        os.chdir(PLUGIN_ROOT)
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
