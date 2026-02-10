import os
import sys
import traceback
from datetime import datetime
from typing import Any


class PythonFailLogger:
    """Per-module Python error logger (non-switch diagnostics)."""

    _log_paths: dict[str, str] = {}
    _fatal_handle = None

    @staticmethod
    def _base_dir() -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def _logs_dir() -> str:
        return os.path.join(PythonFailLogger._base_dir(), "Logs", "PythonLogs")

    @staticmethod
    def start_session() -> None:
        """Reset per-module session paths."""
        PythonFailLogger._log_paths = {}
        try:
            os.makedirs(PythonFailLogger._logs_dir(), exist_ok=True)
        except Exception:
            print("[PythonFailLogger] Failed to create logs dir", file=sys.stderr)
        PythonFailLogger._install_excepthook()

    @staticmethod
    def _setup_fatal_logger() -> None:
        # Fatal monitoring disabled by design to avoid file locks/spam.
        return None

    @staticmethod
    def _install_excepthook() -> None:
        def _hook(exc_type, exc, tb):
            try:
                msg = "".join(traceback.format_exception(exc_type, exc, tb))
                PythonFailLogger.log(
                    "unhandled_exception",
                    module="general",
                    message=msg,
                )
            except Exception:
                print("[PythonFailLogger] Failed to log unhandled exception", file=sys.stderr)
            try:
                sys.__excepthook__(exc_type, exc, tb)
            except Exception:
                print("[PythonFailLogger] sys.__excepthook__ failed", file=sys.stderr)

        try:
            sys.excepthook = _hook
        except Exception:
            print("[PythonFailLogger] Failed to install excepthook", file=sys.stderr)

    @staticmethod
    def _sanitize_module(module: str | None) -> str:
        value = (module or "general").strip().lower()
        return value.replace(" ", "_") or "general"

    @staticmethod
    def _get_log_path(module: str | None) -> str | None:
        mod = PythonFailLogger._sanitize_module(module)
        cached = PythonFailLogger._log_paths.get(mod)
        if cached:
            return cached
        logs_dir = PythonFailLogger._logs_dir()
        try:
            folder_name = "general"
            if mod == "property":
                folder_name = "property"
            elif mod == "general":
                folder_name = "general"
            folder_path = os.path.join(logs_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            prefix = f"python_{mod}_log_"
            existing = [name for name in os.listdir(folder_path) if name.startswith(prefix) and name.endswith(".log")]
            if len(existing) >= 5:
                existing.sort(key=lambda name: os.path.getmtime(os.path.join(folder_path, name)))
                while len(existing) >= 5:
                    oldest_name = existing.pop(0)
                    try:
                        os.remove(os.path.join(folder_path, oldest_name))
                    except Exception:
                        print(f"[PythonFailLogger] Failed to remove {oldest_name}", file=sys.stderr)
                        break

            stamp = datetime.now().strftime("%m_%d_%H%M%S")
            filename = f"{prefix}{stamp}.log"
            path = os.path.join(folder_path, filename)
            if os.path.exists(path):
                suffix = 1
                while True:
                    candidate = os.path.join(folder_path, f"{prefix}{stamp}_{suffix}.log")
                    if not os.path.exists(candidate):
                        path = candidate
                        break
                    suffix += 1
            PythonFailLogger._log_paths[mod] = path
            return path
        except Exception:
            print("[PythonFailLogger] Failed to resolve log path", file=sys.stderr)
            return None

    @staticmethod
    def _format_line(event: str, *, module: str | None = None, extra: dict | None = None, message: str | None = None) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parts = [f"[{ts}]", event]
        if module:
            parts.append(f"module={module}")
        if message:
            parts.append(f"message={message}")
        if extra:
            for k, v in extra.items():
                parts.append(f"{k}={v}")
        return " ".join(parts)

    @staticmethod
    def log(event: str, *, module: str | None = None, message: str | None = None, extra: dict | None = None) -> None:
        path = PythonFailLogger._get_log_path(module)
        if not path:
            return
        try:
            line = PythonFailLogger._format_line(event, module=module, extra=extra, message=message)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            print("[PythonFailLogger] Failed to write log", file=sys.stderr)

    @staticmethod
    def log_exception(exc: Exception, *, module: str | None = None, event: str = "python_error", extra: dict | None = None) -> None:
        message = str(exc)
        PythonFailLogger.log(event, module=module, message=message, extra=extra)
