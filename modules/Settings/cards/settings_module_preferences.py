"""Status, tag, type and not-started-status preferences of a settings module card:
loading, saving, reverting, clearing and the filter widgets that pick them.
"""
from __future__ import annotations

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QWidget

from ....constants.module_names import ModuleSupports
from ....constants.setting_placeholders import SettingDialogPlaceholders
from ....utils.FilterHelpers.FilterHelper import FilterHelper
from ....utils.project_board_status_rules import ProjectBoardStatusRules


class SettingsModulePreferencesMixin:
    """Mixed into SettingsModuleCard, whose __init__ creates the _orig_*/_pend_* sets and
    the filter widget slots used here."""

    def _preference_specs(self):
        return (
            (True, ModuleSupports.STATUSES.value, "_orig_status_preferences", "_pend_status_preferences", self._status_filter_widget),
            (self.supports_tags, ModuleSupports.TAGS.value, "_orig_tag_preferences", "_pend_tag_preferences", self._tags_filter_widget),
            (self.supports_types, ModuleSupports.TYPES.value, "_orig_type_preferences", "_pend_type_preferences", self._type_filter_widget),
        )

    def _load_preference_states(self) -> None:
        for enabled, support_key, orig_attr, pend_attr, _widget in self._preference_specs():
            if not enabled:
                setattr(self, orig_attr, set())
                setattr(self, pend_attr, set())
                continue
            loaded = set(
                self.logic.load_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                )
            )
            setattr(self, orig_attr, loaded)
            setattr(self, pend_attr, set(loaded))
        self._load_not_started_status_preferences()

    def _ensure_saved_preference_widgets_loaded(self) -> None:
        targets = [
            (self._status_filter_widget, self._pend_status_preferences),
            (self._tags_filter_widget, self._pend_tag_preferences),
            (self._type_filter_widget, self._pend_type_preferences),
            (self._not_started_status_filter_widget, self._pend_not_started_status_preferences),
        ]
        for widget, selected_ids in targets:
            if widget is None or not selected_ids:
                continue
            widget.ensure_loaded()

    def _save_preference_states(self) -> bool:
        changed = False
        for enabled, support_key, orig_attr, pend_attr, _widget in self._preference_specs():
            if not enabled:
                continue
            original = getattr(self, orig_attr)
            pending = getattr(self, pend_attr)
            if pending != original:
                self.logic.save_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                    ids=pending,
                )
                setattr(self, orig_attr, set(pending))
                changed = True
        return self._save_not_started_status_preferences() or changed

    def _revert_preference_states(self) -> None:
        for enabled, _support_key, orig_attr, pend_attr, widget in self._preference_specs():
            original = set(getattr(self, orig_attr))
            setattr(self, pend_attr, set(original))
            if enabled and widget is not None:
                widget.set_selected_ids(list(original), emit=False)
        self._revert_not_started_status_preferences()

    def _clear_preference_states_and_storage(self) -> None:
        for enabled, support_key, orig_attr, pend_attr, widget in self._preference_specs():
            if widget is not None:
                widget.set_selected_ids([], emit=False)
            setattr(self, orig_attr, set())
            setattr(self, pend_attr, set())
            if enabled:
                self.logic.clear_module_preference_ids(
                    self.module_key,
                    support_key=support_key,
                )
        self._clear_not_started_status_preferences()

    def _load_not_started_status_preferences(self) -> None:
        loaded = set(ProjectBoardStatusRules.load_not_started_status_ids(self.module_key)) if self.supports_statuses else set()
        self._orig_not_started_status_preferences = set(loaded)
        self._pend_not_started_status_preferences = set(loaded)

    def _save_not_started_status_preferences(self) -> bool:
        if not self.supports_statuses:
            return False
        if self._pend_not_started_status_preferences == self._orig_not_started_status_preferences:
            return False

        serialized = ""
        if self._pend_not_started_status_preferences:
            widget = self._not_started_status_filter_widget
            status_ids = list(widget.selected_ids()) if widget is not None else list(self._pend_not_started_status_preferences)
            status_names = list(widget.selected_texts()) if widget is not None else status_ids
            serialized = ProjectBoardStatusRules.serialize_not_started_status_rows(status_ids, status_names)

        if serialized:
            self.logic.save_module_label_value(
                self.module_key,
                SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES,
                serialized,
            )
        else:
            self.logic.clear_module_label_value(
                self.module_key,
                SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES,
            )

        self._orig_not_started_status_preferences = set(self._pend_not_started_status_preferences)
        return True

    def _revert_not_started_status_preferences(self) -> None:
        original = set(self._orig_not_started_status_preferences)
        self._pend_not_started_status_preferences = set(original)
        if self._not_started_status_filter_widget is not None:
            self._not_started_status_filter_widget.set_selected_ids(list(original), emit=False)

    def _clear_not_started_status_preferences(self) -> None:
        if self._not_started_status_filter_widget is not None:
            self._not_started_status_filter_widget.set_selected_ids([], emit=False)
        self._orig_not_started_status_preferences = set()
        self._pend_not_started_status_preferences = set()
        self.logic.clear_module_label_value(
            self.module_key,
            SettingDialogPlaceholders.PROJECT_BOARD_NOT_STARTED_STATUSES,
        )

    def _install_lazy_filter_loader(self, widget: QWidget | None) -> None:
        if widget is None:
            return
        targets = [widget]
        combo = getattr(widget, "combo", None)
        if combo is not None:
            targets.append(combo)
        group_combo = getattr(widget, "group_combo", None)
        if group_combo is not None:
            targets.append(group_combo)
        type_combo = getattr(widget, "type_combo", None)
        if type_combo is not None:
            targets.append(type_combo)

        for target in targets:
            if target is None:
                continue
            self._lazy_filter_widgets.add(target)
            target.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj in self._lazy_filter_widgets:
            if event.type() in (QEvent.MouseButtonPress, QEvent.FocusIn, QEvent.Show):
                ensure_loaded = getattr(obj, "ensure_loaded", None)
                if callable(ensure_loaded):
                    try:
                        ensure_loaded()
                    except Exception as exc:
                        self._log_error("settings_module_filter_lazy_load_failed", exc, extra={"widget": type(obj).__name__})
                to_remove = {obj}
                for target in list(self._lazy_filter_widgets):
                    if target is obj:
                        continue
                    owner = None
                    try:
                        owner = target.parent()
                    except RuntimeError:
                        owner = None
                    if owner is obj:
                        to_remove.add(target)
                for target in to_remove:
                    self._lazy_filter_widgets.discard(target)
                    try:
                        target.removeEventFilter(self)
                    except RuntimeError:
                        continue
        return super().eventFilter(obj, event)

    def _cancel_filter_workers(self):
        for widget in (
            self._status_filter_widget,
            self._not_started_status_filter_widget,
            self._type_filter_widget,
            self._tags_filter_widget,
                ):
            FilterHelper.cancel_pending_load(widget, invalidate_request=True)

    @staticmethod
    def _preference_error_event(support_key: str) -> str:
        return {
            ModuleSupports.STATUSES.value: "settings_module_status_selection_failed",
            ModuleSupports.TAGS.value: "settings_module_tags_selection_failed",
            ModuleSupports.TYPES.value: "settings_module_type_selection_failed",
        }.get(support_key, "settings_module_preference_selection_failed")

    def _apply_pending_preference_set(self, support_key: str, values: set) -> None:
        if support_key == ModuleSupports.STATUSES.value:
            self._pend_status_preferences = values
            return
        if support_key == ModuleSupports.TAGS.value:
            self._pend_tag_preferences = values
            return
        if support_key == ModuleSupports.TYPES.value:
            self._pend_type_preferences = values

    @staticmethod
    def _stringify_preference_ids(support_key: str) -> bool:
        return support_key in (ModuleSupports.STATUSES.value, ModuleSupports.TAGS.value)

    def _connect_preference_selection(self, widget, support_key: str) -> None:
        if widget is None:
            return
        widget.selectionChanged.connect(
            lambda texts=None, ids=None: self._on_preference_selection_changed(
                support_key=support_key,
                widget=widget,
                ids=ids,
            )
        )

    def _on_preference_selection_changed(self, *, support_key: str, widget, ids=None) -> None:
        try:
            selected_ids = ids if ids is not None else (widget.selected_ids() if widget is not None else [])
            stringify = self._stringify_preference_ids(support_key)
            normalized = {str(v) for v in (selected_ids or [])} if stringify else set(selected_ids or [])
            self._apply_pending_preference_set(support_key, normalized)
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            self._log_error(self._preference_error_event(support_key), exc)

    def _on_not_started_status_selection_changed(self, *, widget=None, ids=None) -> None:
        try:
            selected_ids = ids if ids is not None else (widget.selected_ids() if widget is not None else [])
            self._pend_not_started_status_preferences = {str(value).strip() for value in (selected_ids or []) if str(value).strip()}
            self._emit_pending_changed(self.has_pending_changes())
        except Exception as exc:
            self._log_error("settings_module_not_started_status_selection_failed", exc)
