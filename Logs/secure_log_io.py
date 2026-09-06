from __future__ import annotations

import os
from typing import TextIO


PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


def ensure_private_directory(path: str) -> str:
    """Create a log directory and enforce owner-only access on POSIX."""
    if os.path.islink(path):
        raise OSError(f"Refusing to use a symbolic link as a log directory: {path}")

    os.makedirs(path, mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
    if os.name == "posix":
        os.chmod(path, PRIVATE_DIRECTORY_MODE)
    return path


def harden_private_file(path: str) -> None:
    """Tighten an existing log file without following symbolic links."""
    if not os.path.lexists(path):
        return
    if os.path.islink(path):
        raise OSError(f"Refusing to use a symbolic link as a log file: {path}")
    if os.name == "posix":
        os.chmod(path, PRIVATE_FILE_MODE)


def open_private_log(path: str) -> TextIO:
    """Open a UTF-8 append-only log with restrictive creation permissions."""
    parent = os.path.dirname(os.path.abspath(path))
    ensure_private_directory(parent)

    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if no_follow:
        flags |= no_follow
    elif os.path.islink(path):
        raise OSError(f"Refusing to follow a symbolic link for a log file: {path}")

    descriptor = os.open(path, flags, PRIVATE_FILE_MODE)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, PRIVATE_FILE_MODE)
        return os.fdopen(descriptor, "a", encoding="utf-8")
    except Exception:
        os.close(descriptor)
        raise
