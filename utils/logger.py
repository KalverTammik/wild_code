from typing import Optional

# Simple centralized logger controlled by a global debug flag.
# Use set_debug(True/False) from the app (e.g., PluginDialog) to control verbosity.

_debug_enabled: bool = False


def set_debug(enabled: bool) -> None:
    global _debug_enabled
    _debug_enabled = bool(enabled)


def is_debug() -> bool:
    return _debug_enabled


def debug(msg: str) -> None:
    if _debug_enabled:
        try:
            print(msg)
        except Exception:
            pass


def info(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass


def warn(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass


def error(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass
