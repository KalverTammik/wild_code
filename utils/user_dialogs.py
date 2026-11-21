"""The dialogs a headless flow may show, handed in by its UI caller (usually ``ModernMessageDialog``)."""
from __future__ import annotations

from typing import Protocol


class UserDialogs(Protocol):
    """The subset of ``ModernMessageDialog`` that services use; the labels are required so they come translated."""

    def show_warning(self, title: str, message: str) -> bool: ...

    def show_info(self, title: str, message: str) -> None: ...

    def ask_yes_no(
        self,
        title: str,
        message: str,
        *,
        yes_label: str,
        no_label: str,
        default: str | None = None,
    ) -> bool: ...
