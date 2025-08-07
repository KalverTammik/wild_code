from qgis.PyQt.QtCore import QSettings, QTimer

class DialogGeometryWatcher:
    """
    Utility class to monitor and persist the geometry (position and size) of a QDialog.
    Can be attached to any QDialog instance for live geometry tracking and QSettings persistence.
    """
    def __init__(self, dialog, on_update=None, settings_key="wild_code/plugin_dialog/geometry", poll_interval=200):
        self.dialog = dialog
        self.on_update = on_update  # Callback: on_update(x, y, w, h)
        self.settings_key = settings_key
        self._last_geom = None
        print(f"[DialogGeometryWatcher] Initializing for dialog: {dialog}")
        self._timer = QTimer(dialog)
        self._timer.timeout.connect(self._poll_geometry)
        self._timer.start(poll_interval)
        self._wrap_events()
        self.restore_geometry()

    def _wrap_events(self):
        print(f"[DialogGeometryWatcher] Wrapping dialog events for: {self.dialog}")
        # Save original handlers if not already saved
        if not hasattr(self.dialog, '_original_resizeEvent'):
            print("[DialogGeometryWatcher] Saving original resizeEvent handler")
            self.dialog._original_resizeEvent = self.dialog.resizeEvent
        if not hasattr(self.dialog, '_original_moveEvent'):
            print("[DialogGeometryWatcher] Saving original moveEvent handler")
            self.dialog._original_moveEvent = self.dialog.moveEvent
        # Replace handlers
        self.dialog.resizeEvent = self._wrap_resize_event(self.dialog._original_resizeEvent)
        self.dialog.moveEvent = self._wrap_move_event(self.dialog._original_moveEvent)

    def _wrap_resize_event(self, original_resize_event):
        def new_resize_event(event):
            print("[DialogGeometryWatcher] resizeEvent triggered")
            self._update_size()
            original_resize_event(event)
        return new_resize_event

    def _wrap_move_event(self, original_move_event):
        def new_move_event(event):
            print("[DialogGeometryWatcher] moveEvent triggered")
            self._update_size()
            original_move_event(event)
        return new_move_event

    def _poll_geometry(self):
        geo = self.dialog.geometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        new_geom = (x, y, w, h)
        if new_geom != self._last_geom:
            print(f"[DialogGeometryWatcher] _poll_geometry: x={x}, y={y}, w={w}, h={h}")
            self._last_geom = new_geom
            if self.on_update:
                self.on_update(x, y, w, h)
            self.save_geometry(x, y, w, h)

    def _update_size(self):
        geo = self.dialog.geometry()
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        print(f"[DialogGeometryWatcher] _update_size: x={x}, y={y}, w={w}, h={h}")
        if self.on_update:
            self.on_update(x, y, w, h)
        self.save_geometry(x, y, w, h)

    def save_geometry(self, x, y, w, h):
        try:
            print(f"[DialogGeometryWatcher] Saving geometry to QSettings: {x}, {y}, {w}, {h}")
            settings = QSettings()
            settings.setValue(self.settings_key, [x, y, w, h])
        except Exception as e:
            print(f"[DialogGeometryWatcher] Failed to save geometry: {e}")

    def restore_geometry(self):
        try:
            settings = QSettings()
            value = settings.value(self.settings_key, None)
            print(f"[DialogGeometryWatcher] Restoring geometry from QSettings: {value}")
            if value and len(value) == 4:
                x, y, w, h = map(int, value)
                print(f"[DialogGeometryWatcher] Restoring geometry: {x}, {y}, {w}, {h}")
                self.dialog.setGeometry(x, y, w, h)
        except Exception as e:
            print(f"[DialogGeometryWatcher] Failed to restore geometry: {e}")

    def stop(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        # Restore original event handlers
        if hasattr(self.dialog, '_original_resizeEvent'):
            self.dialog.resizeEvent = self.dialog._original_resizeEvent
        if hasattr(self.dialog, '_original_moveEvent'):
            self.dialog.moveEvent = self.dialog._original_moveEvent
