"""Review of GIS features drawn into the works layer without a backend task: scan the
layer, list them and open one in the create form.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QProgressDialog

from ...languages.translation_keys import TranslationKeys
from ...ui.messages_helper import ModernMessageDialog
from .works_create_map_widgets import MapButtonProgressBubble
from .works_layer_service import WorksLayerService
from .works_pending_gis_dialog import WorksPendingGisDialog


class WorksPendingGisReviewMixin:
    """Mixed into WorksCreateController, whose _open_pending_gis_feature opens a listed feature."""

    def review_pending_gis_features(
        self,
        *,
        parent_window=None,
        allowed_type_ids: Optional[Iterable[str]] = None,
        on_created: Optional[Callable[[str], None]] = None,
        progress_anchor=None,
    ) -> bool:
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, dialogs=ModernMessageDialog)
        if works_layer is None:
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._allowed_type_ids = [str(item_id) for item_id in (allowed_type_ids or []) if item_id]
        self._on_created = on_created
        self._existing_task_id = ""
        self._existing_task_payload = {}
        self.preload_dialog_data()

        pending_rows = self._scan_pending_gis_features_with_feedback(
            works_layer,
            parent_window=parent_window,
            progress_anchor=progress_anchor,
        )
        if not pending_rows:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.INFO),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_NONE),
            )
            return False
        pending_rows = self._decorate_pending_gis_rows(pending_rows)

        dialog = WorksPendingGisDialog(
            rows=pending_rows,
            on_open=lambda feature_id, owner: self._open_pending_gis_feature(
                works_layer,
                feature_id,
                parent_window=owner,
            ),
            lang_manager=self._lang,
            parent=parent_window,
        )
        dialog.exec_()
        return True

    def _scan_pending_gis_features_with_feedback(
        self,
        works_layer,
        *,
        parent_window=None,
        progress_anchor=None,
    ) -> list[dict[str, object]]:
        progress = self._make_scan_progress_widget(
            parent_window=parent_window,
            progress_anchor=progress_anchor,
        )
        if isinstance(progress, MapButtonProgressBubble):
            progress.show_near_anchor()
        else:
            progress.show()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        try:
            return WorksLayerService.pending_gis_work_features(works_layer)
        finally:
            QApplication.restoreOverrideCursor()
            progress.close()
            progress.deleteLater()
            QApplication.processEvents()

    def _make_scan_progress_widget(self, *, parent_window=None, progress_anchor=None):
        text = self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_CHECKING)
        if progress_anchor is not None:
            return MapButtonProgressBubble(text=text, anchor=progress_anchor)

        progress = QProgressDialog(text, "", 0, 0, parent_window)
        progress.setWindowTitle(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        # The same look and width as the other short waits; without it the window takes QGIS's own.
        progress.setMinimumWidth(380)
        ModernMessageDialog.style_as_message(progress)
        return progress

    def _decorate_pending_gis_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        type_labels = {
            str(option.get("id") or "").strip(): str(option.get("label") or "").strip()
            for option in self._resolve_type_options()
            if isinstance(option, dict) and str(option.get("id") or "").strip()
        }
        status_labels = {
            str(option.get("id") or "").strip(): str(option.get("name") or option.get("label") or "").strip()
            for option in self._resolve_status_options()
            if isinstance(option, dict) and str(option.get("id") or "").strip()
        }

        decorated: list[dict[str, object]] = []
        for row in rows:
            payload = dict(row or {})
            type_id = str(payload.get("type_id") or "").strip()
            status_id = str(payload.get("status_id") or "").strip()
            payload["type_label"] = type_labels.get(type_id) or type_id
            payload["status_label"] = status_labels.get(status_id) or status_id
            decorated.append(payload)
        return decorated
