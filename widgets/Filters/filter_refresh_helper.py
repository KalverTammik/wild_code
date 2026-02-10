from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from ...constants.button_props import ButtonVariant
from ...constants.module_icons import IconNames
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ..theme_manager import ThemeManager
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.FilterHelpers.FilterHelper import FilterRefreshService


class FilterRefreshHelper:
    """Utility widget that provides a toolbar-friendly reset button."""

    def __init__(self, owner: QWidget):
        self._owner = owner
        self._lang = LanguageManager()

    def make_filter_refresh_button(self, parent: Optional[QWidget] = None) -> QWidget:
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        size_px = 28

        refresh_btn = QPushButton("", container)
        refresh_btn.setObjectName("FeedRefreshButton")
        refresh_btn.setProperty("variant", ButtonVariant.ICON)
        refresh_btn.setAutoDefault(False)
        refresh_btn.setDefault(False)
        refresh_btn.setFixedSize(size_px, size_px)
        refresh_btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_REFRESH))
        refresh_btn.setIconSize(QSize(16, 16))
        refresh_btn.setToolTip(self._lang.translate(TranslationKeys.FILTERS_REFRESH))
        refresh_btn.clicked.connect(self._on_refresh_clicked)  # type: ignore[attr-defined]
        layout.addWidget(refresh_btn)

        clear_btn = QPushButton("", container)
        clear_btn.setObjectName("FeedClearButton")
        clear_btn.setProperty("variant", ButtonVariant.ICON)
        clear_btn.setAutoDefault(False)
        clear_btn.setDefault(False)
        clear_btn.setFixedSize(size_px, size_px)
        clear_btn.setIcon(ThemeManager.get_qicon(IconNames.ICON_CLOSE_X))
        clear_btn.setIconSize(QSize(20, 20))
        clear_btn.setToolTip(self._lang.translate(TranslationKeys.FILTERS_CLEAR))
        clear_btn.clicked.connect(self._on_clear_clicked)  # type: ignore[attr-defined]
        layout.addWidget(clear_btn)
        return container

    def _on_refresh_clicked(self):
        owner = self._owner
        status_ids: list[str] = []
        type_ids: list[str] = []
        tag_ids: list[str] = []
        try:
            ensure_loaded = getattr(owner, "_ensure_filters_loaded", None)
            if callable(ensure_loaded):
                ensure_loaded()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="filter_refresh_ensure_loaded_failed",
            )

        status_filter = getattr(owner, "status_filter", None)
        type_filter = getattr(owner, "type_filter", None)
        tags_filter = getattr(owner, "tags_filter", None)

        try:
            status_ids = FilterRefreshService.saved_status_ids(owner)
            type_ids = FilterRefreshService.saved_type_ids(owner)
            tag_ids = FilterRefreshService.saved_tag_ids(owner)

            if status_filter and hasattr(status_filter, "set_selected_ids"):
                status_filter.set_selected_ids(status_ids, emit=False)
            if type_filter and hasattr(type_filter, "set_selected_ids"):
                type_filter.set_selected_ids(type_ids, emit=False)
            if tags_filter and hasattr(tags_filter, "set_selected_ids"):
                tags_filter.set_selected_ids(tag_ids, emit=False)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="filter_refresh_apply_saved_failed",
            )

        try:
            refresh_fn = getattr(owner, "_refresh_filters", None)
            if callable(refresh_fn):
                refresh_fn()
            else:
                FilterRefreshService.refresh_filters(
                    owner,
                    status_ids=status_ids,
                    type_ids=type_ids,
                    tags_ids=tag_ids,
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="filter_refresh_execute_failed",
            )

    def _on_clear_clicked(self) -> None:
        owner = self._owner
        status_filter = getattr(owner, "status_filter", None)
        type_filter = getattr(owner, "type_filter", None)
        tags_filter = getattr(owner, "tags_filter", None)

        try:
            if status_filter and hasattr(status_filter, "set_selected_ids"):
                status_filter.set_selected_ids([], emit=False)
            if type_filter and hasattr(type_filter, "set_selected_ids"):
                type_filter.set_selected_ids([], emit=False)
            if tags_filter and hasattr(tags_filter, "set_selected_ids"):
                tags_filter.set_selected_ids([], emit=False)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="filter_clear_apply_failed",
            )

        try:
            refresh_fn = getattr(owner, "_refresh_filters", None)
            if callable(refresh_fn):
                refresh_fn()
            else:
                FilterRefreshService.refresh_filters(
                    owner,
                    status_ids=[],
                    type_ids=[],
                    tags_ids=[],
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="filter_clear_execute_failed",
            )
