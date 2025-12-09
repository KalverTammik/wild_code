from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from ..constants.module_icons import IconNames
from .theme_manager import ThemeManager


class FilterRefreshHelper:
    """Utility widget that provides a toolbar-friendly reset button."""

    def __init__(self, owner: QWidget):
        self._owner = owner

    def make_filter_refresh_button(self, parent: Optional[QWidget] = None) -> QWidget:
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        btn = QPushButton("", container)
        btn.setObjectName("FeedRefreshButton")
        btn.setAutoDefault(False)
        btn.setDefault(False)
        size_px = 28
        btn.setFixedSize(size_px, size_px)
        btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_REFRESH))
        btn.setIconSize(QSize(18, 18))
        btn.clicked.connect(self._on_refresh_clicked)  # type: ignore[attr-defined]

        layout.addWidget(btn)
        return container

    def _on_refresh_clicked(self):
        owner = self._owner
        # Clear filters first
        try:
            filters = getattr(owner, "_filter_widgets", None)
            if filters:
                iterable = list(filters)
            else:
                toolbar = getattr(owner, "toolbar_area", None)
                iterable = list(getattr(toolbar, "filter_widgets", {}).values()) if toolbar else []

            for widget in iterable:
                try:
                    if hasattr(widget, "set_selected_ids"):
                        widget.set_selected_ids([])  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

        for flag in ("_status_preferences_loaded", "_type_preferences_loaded", "_tags_preferences_loaded"):
            if hasattr(owner, flag):
                try:
                    setattr(owner, flag, False)
                except Exception:
                    pass

        try:
            if hasattr(owner, "reset_feed_session") and callable(owner.reset_feed_session):
                owner.reset_feed_session()
        except Exception:
            pass

        try:
            eng = getattr(owner, "feed_load_engine", None)
            if eng and hasattr(eng, "schedule_load"):
                eng.schedule_load()
            elif hasattr(owner, "process_next_batch") and callable(owner.process_next_batch):
                owner.process_next_batch()
        except Exception:
            pass
