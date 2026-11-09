"""Parts the filter widgets share: loading state, the request token lookup and the picker's control and popup."""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget


class FilterLoadingMixin:
    """For a QWidget that fills itself in a worker thread. Goes before QWidget in the bases.

    The widget sets `_loaded`, `_worker` and `_worker_thread` and has `reload`.
    """

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def _cleanup_worker(self) -> None:
        if not self._is_widget_alive():
            return
        self._worker = None
        self._worker_thread = None

    def _current_token(self) -> int | None:
        if not self._is_widget_alive():
            return None
        try:
            parent = self.parent()
        except RuntimeError:
            return None
        while parent is not None:
            if hasattr(parent, "_active_token"):
                return parent._active_token
            parent = parent.parent()
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if not self._is_widget_alive():
            return False
        if token is None:
            return True
        try:
            parent = self.parent()
        except RuntimeError:
            return False
        while parent is not None:
            if hasattr(parent, "is_token_active"):
                try:
                    return bool(parent.is_token_active(token))
                except Exception:
                    return False
            parent = parent.parent()
        return True

    def _is_widget_alive(self) -> bool:
        try:
            import sip
        except Exception:
            sip = None
        try:
            return not bool(sip and sip.isdeleted(self))
        except RuntimeError:
            return False


class SelectAllFilterMixin(FilterLoadingMixin):
    """A filter that also has a select-all box in `all_cb`, guarded by `_suppress_all_cb`."""

    def _set_all_cb_state(self, state: Qt.CheckState, *, enabled: bool | None = None) -> None:
        self._suppress_all_cb = True
        try:
            self.all_cb.setCheckState(state)
            if enabled is not None:
                self.all_cb.setEnabled(enabled)
        finally:
            self._suppress_all_cb = False


class PickerControlBase(QFrame):
    """The closed picker: a summary in `_label` that opens the list when clicked."""

    clicked = pyqtSignal()

    def set_summary(self, text: str) -> None:
        self._label.setText(text)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class PickerPopupBase(QWidget):
    """The picker's open list."""

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
            if widget is not None:
                widget.deleteLater()
