from qgis.PyQt.QtCore import QSettings, QTimer
from ...Logs.python_fail_logger import PythonFailLogger

class DialogGeometryWatcher:
    """
    Utility class to monitor and persist the geometry (position and size) of a QDialog.
    Can be attached to any QDialog instance for live geometry tracking and QSettings persistence.
    """
    def __init__(self, dialog, on_update=None, settings_key="kavitro/plugin_dialog/geometry", poll_interval=200):
        self.dialog = dialog
        self.on_update = on_update  # Callback: on_update(x, y, w, h)
        self.settings_key = settings_key
        # Track last known geometry (x,y,w,h) to avoid duplicate callbacks
        self._last_geom = None
        self._timer = QTimer(dialog)
        self._timer.timeout.connect(self._poll_geometry)
        self._timer.start(poll_interval)
        self._wrap_events()
        # Restore geometry from settings (if present). After restore we record
        # the restored geometry into _last_geom so subsequent move/resize
        # events and the polling timer do not emit duplicate notifications.
        self.restore_geometry()

    def _wrap_events(self):
        # Save original handlers if not already saved
        
        if not hasattr(self.dialog, '_original_resizeEvent'):
            self.dialog._original_resizeEvent = self.dialog.resizeEvent
        if not hasattr(self.dialog, '_original_moveEvent'):
            self.dialog._original_moveEvent = self.dialog.moveEvent
        # Replace handlers
        self.dialog.resizeEvent = self._wrap_resize_event(self.dialog._original_resizeEvent)
        self.dialog.moveEvent = self._wrap_move_event(self.dialog._original_moveEvent)

    def _wrap_resize_event(self, original_resize_event):
        def new_resize_event(event):
            self._update_size()
            original_resize_event(event)
        return new_resize_event

    def _wrap_move_event(self, original_move_event):
        def new_move_event(event):
            self._update_size()
            original_move_event(event)
        return new_move_event

    def _poll_geometry(self):
        geo = self.dialog.geometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        new_geom = (x, y, w, h)
        if new_geom != self._last_geom:
            self._last_geom = new_geom
            if self.on_update:
                self.on_update(x, y, w, h)
            self.save_geometry(x, y, w, h)

    def _update_size(self):
        geo = self.dialog.geometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        new_geom = (x, y, w, h)
        # Only notify/save when geometry actually changed since last recorded
        if new_geom != self._last_geom:
            self._last_geom = new_geom
            if self.on_update:
                self.on_update(x, y, w, h)
            self.save_geometry(x, y, w, h)

    def save_geometry(self, x, y, w, h):
        try:
            settings = QSettings()
            settings.setValue(self.settings_key, [x, y, w, h])
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="dialog_geometry_save_failed",
            )

    def restore_geometry(self):
        try:
            settings = QSettings()
            value = settings.value(self.settings_key, None)
            if value and len(value) == 4:
                x, y, w, h = map(int, value)
                # Apply saved geometry and mark it as last known geometry so
                # the watcher does not emit duplicate callbacks for the same
                # size/position coming from events or the poll timer.
                self.dialog.setGeometry(x, y, w, h)
                try:
                    self._last_geom = (int(x), int(y), int(w), int(h))
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="ui",
                        event="dialog_geometry_last_geom_failed",
                    )
                    self._last_geom = None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="dialog_geometry_restore_failed",
            )

    def stop(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        # Restore original event handlers
        if hasattr(self.dialog, '_original_resizeEvent'):
            self.dialog.resizeEvent = self.dialog._original_resizeEvent
        if hasattr(self.dialog, '_original_moveEvent'):
            self.dialog.moveEvent = self.dialog._original_moveEvent
