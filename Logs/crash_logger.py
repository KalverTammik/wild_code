from __future__ import annotations

import faulthandler
import os
import sys
import tempfile
from datetime import datetime
from typing import Any, TextIO

from .secure_log_io import ensure_private_directory, harden_private_file


class CrashLogger:
    """Own the optional Kavitro faulthandler file for one plugin lifetime."""

    FILE_PREFIX = "kavitro_crash_"
    FILE_SUFFIX = ".log"
    MAX_RETAINED_LOGS = 3

    def __init__(self, *, log_dir: str | None = None, fault_handler: Any = None) -> None:
        self._log_dir = log_dir or self.default_log_dir()
        self._fault_handler = fault_handler or faulthandler
        self._handle: TextIO | None = None
        self._path: str | None = None
        self._owns_handler = False

    @staticmethod
    def default_log_dir() -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "CrashLogs")

    @property
    def current_path(self) -> str | None:
        return self._path

    def _existing_log_paths(self) -> list[str]:
        if not os.path.isdir(self._log_dir) or os.path.islink(self._log_dir):
            return []

        paths: list[str] = []
        for name in os.listdir(self._log_dir):
            if not name.startswith(self.FILE_PREFIX) or not name.endswith(self.FILE_SUFFIX):
                continue
            path = os.path.join(self._log_dir, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            harden_private_file(path)
            paths.append(path)
        return paths

    @staticmethod
    def _modified_at(path: str) -> float:
        try:
            return os.path.getmtime(path)
        except OSError:
            return 0.0

    def latest_log_path(self) -> str | None:
        """Return the newest retained crash log without opening its contents."""
        try:
            paths = self._existing_log_paths()
        except Exception:
            return None
        return max(paths, key=self._modified_at) if paths else None

    def _prune_old_logs(self, *, keep: int) -> None:
        paths = self._existing_log_paths()
        non_empty: list[str] = []
        for path in paths:
            try:
                if os.path.getsize(path) == 0:
                    os.remove(path)
                else:
                    non_empty.append(path)
            except OSError:
                continue

        non_empty.sort(key=self._modified_at, reverse=True)
        for path in non_empty[max(0, int(keep)) :]:
            try:
                os.remove(path)
            except OSError:
                continue

    def start(self) -> str | None:
        """Securely start Kavitro crash logging unless the host already owns it."""
        if self._handle is not None and not self._handle.closed:
            return self._path

        descriptor: int | None = None
        path: str | None = None
        try:
            if self._fault_handler.is_enabled():
                return None

            ensure_private_directory(self._log_dir)
            # Leave room for this session so a crash retains at most three files.
            self._prune_old_logs(keep=self.MAX_RETAINED_LOGS - 1)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            descriptor, path = tempfile.mkstemp(
                prefix=f"{self.FILE_PREFIX}{stamp}_",
                suffix=self.FILE_SUFFIX,
                dir=self._log_dir,
                text=True,
            )
            harden_private_file(path)
            handle = os.fdopen(descriptor, "w", encoding="utf-8")
            descriptor = None
        except Exception:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass
            print("[CrashLogger] Failed to create crash log", file=sys.stderr)
            return None

        try:
            self._fault_handler.enable(handle, all_threads=True)
        except Exception:
            handle.close()
            try:
                os.remove(path)
            except OSError:
                pass
            print("[CrashLogger] Failed to enable faulthandler", file=sys.stderr)
            return None

        self._handle = handle
        self._path = path
        self._owns_handler = True
        return path

    def stop(self) -> None:
        """Disable the owned handler, close its file and discard an empty log."""
        handle = self._handle
        path = self._path

        if self._owns_handler:
            try:
                if self._fault_handler.is_enabled():
                    self._fault_handler.disable()
                if self._fault_handler.is_enabled():
                    print("[CrashLogger] faulthandler remained enabled", file=sys.stderr)
                    return
            except Exception:
                print("[CrashLogger] Failed to disable faulthandler", file=sys.stderr)
                return

        if handle is not None:
            try:
                handle.close()
            except Exception:
                print("[CrashLogger] Failed to close crash log", file=sys.stderr)
                if not handle.closed:
                    return

        self._handle = None
        self._path = None
        self._owns_handler = False

        if path:
            try:
                if os.path.isfile(path) and not os.path.islink(path) and os.path.getsize(path) == 0:
                    os.remove(path)
                else:
                    self._prune_old_logs(keep=self.MAX_RETAINED_LOGS)
            except OSError:
                pass
