import os
import shutil
import time
import sys
from datetime import datetime
from typing import Any


class SwitchLogger:
    """Lightweight session logger for module switching diagnostics."""

    _log_path: str | None = None
    _session_id: int | None = None
    _last_py_bytes: int | None = None

    @staticmethod
    def _base_dir() -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def _logs_dir() -> str:
        return os.path.join(SwitchLogger._base_dir(), "Logs", "SwitchLogs")

    @staticmethod
    def _crash_dir() -> str:
        return os.path.join(SwitchLogger._base_dir(), "Logs", "CrashLogs")

    @staticmethod
    def _migrate_legacy_logs() -> None:
        base_dir = SwitchLogger._base_dir()
        legacy_dir = os.path.join(base_dir, "CrashLogs")
        if not os.path.isdir(legacy_dir):
            return
        try:
            os.makedirs(SwitchLogger._crash_dir(), exist_ok=True)
        except Exception:
            print("[SwitchLogger] Failed to create crash logs dir", file=sys.stderr)
            return
        try:
            for name in os.listdir(legacy_dir):
                src = os.path.join(legacy_dir, name)
                if not os.path.isfile(src):
                    continue
                if name.startswith("switch_log_") and name.endswith(".log"):
                    dst_dir = SwitchLogger._logs_dir()
                else:
                    dst_dir = SwitchLogger._crash_dir()
                try:
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = os.path.join(dst_dir, name)
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                except Exception:
                    print(f"[SwitchLogger] Failed to migrate legacy log {name}", file=sys.stderr)
                    continue
            try:
                if not os.listdir(legacy_dir):
                    os.rmdir(legacy_dir)
            except Exception:
                print("[SwitchLogger] Failed to remove legacy dir", file=sys.stderr)
        except Exception:
            print("[SwitchLogger] Legacy migration failed", file=sys.stderr)

    @staticmethod
    def start_session() -> str | None:
        """Create a new log file for this plugin activation."""
        try:
            SwitchLogger._migrate_legacy_logs()
            logs_dir = SwitchLogger._logs_dir()
            os.makedirs(logs_dir, exist_ok=True)
            existing = [name for name in os.listdir(logs_dir) if name.startswith("switch_log_") and name.endswith(".log")]
            if len(existing) >= 5:
                existing.sort(key=lambda name: os.path.getmtime(os.path.join(logs_dir, name)))
                while len(existing) >= 5:
                    oldest_name = existing.pop(0)
                    try:
                        os.remove(os.path.join(logs_dir, oldest_name))
                    except Exception:
                        print(f"[SwitchLogger] Failed to remove old log {oldest_name}", file=sys.stderr)
                        break

            stamp = datetime.now().strftime("%m_%d_%H%M%S")
            filename = f"switch_log_{stamp}.log"
            path = os.path.join(logs_dir, filename)
            if os.path.exists(path):
                suffix = 1
                while True:
                    candidate = os.path.join(logs_dir, f"switch_log_{stamp}_{suffix}.log")
                    if not os.path.exists(candidate):
                        path = candidate
                        filename = os.path.basename(candidate)
                        break
                    suffix += 1
            SwitchLogger._log_path = path
            SwitchLogger._ensure_tracemalloc()
            SwitchLogger.log("session_start", extra={"file": filename})
            return path
        except Exception:
            print("[SwitchLogger] Failed to start session", file=sys.stderr)
            return None

    @staticmethod
    def _ensure_tracemalloc() -> None:
        try:
            import tracemalloc

            if not tracemalloc.is_tracing():
                tracemalloc.start(10)
        except Exception:
            print("[SwitchLogger] Failed to start tracemalloc", file=sys.stderr)

    @staticmethod
    def _bytes_to_mb(value: int | None) -> float | None:
        if value is None:
            return None
        return round(value / (1024 * 1024), 2)

    @staticmethod
    @staticmethod
    def _get_qgis_layer_stats() -> dict[str, Any]:
        try:
            from qgis.core import QgsProject

            layers = QgsProject.instance().mapLayers().values()
            total_layers = 0
            memory_layers = 0
            for layer in layers:
                total_layers += 1
                try:
                    if layer.providerType() == "memory":
                        memory_layers += 1
                except Exception:
                    print("[SwitchLogger] layer providerType failed", file=sys.stderr)
                    continue
            return {"layers": total_layers, "memory_layers": memory_layers}
        except Exception:
            print("[SwitchLogger] layer stats failed", file=sys.stderr)
            return {}

    @staticmethod
    def _collect_memory_stats() -> dict[str, Any]:
        stats: dict[str, Any] = {}

        try:
            import tracemalloc

            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                stats["py_mb"] = SwitchLogger._bytes_to_mb(current)
                stats["py_peak_mb"] = SwitchLogger._bytes_to_mb(peak)
                if SwitchLogger._last_py_bytes is not None:
                    stats["py_delta_mb"] = SwitchLogger._bytes_to_mb(current - SwitchLogger._last_py_bytes)
                SwitchLogger._last_py_bytes = current
        except Exception:
            print("[SwitchLogger] tracemalloc stats failed", file=sys.stderr)

        stats.update(SwitchLogger._get_qgis_layer_stats())
        return stats

    @staticmethod
    def _format_line(event: str, *, module: str | None = None, extra: dict | None = None) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parts = [f"[{ts}]", event]
        if module:
            parts.append(f"module={module}")
        if extra:
            for k, v in extra.items():
                parts.append(f"{k}={v}")
        return " ".join(parts)

    @staticmethod
    def log(event: str, *, module: str | None = None, extra: dict | None = None) -> None:
        path = SwitchLogger._log_path
        if not path:
            return
        try:
            line = SwitchLogger._format_line(event, module=module, extra=extra)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            print("[SwitchLogger] write failed", file=sys.stderr)

    @staticmethod
    def log_memory_snapshot(*, module: str | None = None, label: str = "after_switch") -> None:
        stats = SwitchLogger._collect_memory_stats()
        if not stats:
            return
        stats["label"] = label
        SwitchLogger.log("memory_snapshot", module=module, extra=stats)
