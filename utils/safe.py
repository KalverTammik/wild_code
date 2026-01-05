from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


def safe_call(
    func: Callable[..., T],
    *args: Any,
    default: Optional[T] = None,
    **kwargs: Any,
) -> Optional[T]:
    """Call `func(*args, **kwargs)` and swallow any exception.

    This is intentionally silent (SignalTest is a harness; callers often don't want noisy UI).
    """

    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    """Safe getattr that swallows attribute access errors."""

    try:
        return getattr(obj, name)
    except Exception:
        return default


def safe_setattr(obj: Any, name: str, value: Any) -> bool:
    """Safe setattr that swallows attribute set errors."""

    try:
        setattr(obj, name, value)
        return True
    except Exception:
        return False
