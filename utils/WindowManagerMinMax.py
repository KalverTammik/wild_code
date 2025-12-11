from PyQt5.QtWidgets import QWidget


class WindowManagerMinMax:
    def __init__(self, window: QWidget):
        self.window = window
        self.is_maximized = False
        self.is_minimized = False
        self.original_geometry = window.geometry()
        try:
            geo = self.original_geometry
            print(f"[window_mgr] init id={id(self.window)} geo=({geo.x()},{geo.y()},{geo.width()},{geo.height()})")
        except Exception:
            print(f"[window_mgr] init id={id(self.window)} geo=<unavailable>")

    def _minimize_window(self):
        if not self.is_minimized:
            try:
                geo = self.window.geometry()
                print(f"[window_mgr] minimize id={id(self.window)} geo_before=({geo.x()},{geo.y()},{geo.width()},{geo.height()})")
            except Exception:
                print(f"[window_mgr] minimize id={id(self.window)} geo_before=<unavailable>")
            try:
                # Update original geometry so restore brings us back to the latest normal position
                self.original_geometry = self.window.geometry()
            except Exception:
                pass
            self.window.showMinimized()
            self.is_minimized = True
            self.is_maximized = False

    def _maximize_window(self):
        if not self.is_maximized:
            try:
                geo = self.window.geometry()
                print(f"[window_mgr] maximize id={id(self.window)} geo_before=({geo.x()},{geo.y()},{geo.width()},{geo.height()})")
            except Exception:
                print(f"[window_mgr] maximize id={id(self.window)} geo_before=<unavailable>")
            self.window.showMaximized()
            self.is_maximized = True
            self.is_minimized = False

    def _restore_window(self):
        try:
            geo_before = self.window.geometry()
            print(
                f"[window_mgr] restore id={id(self.window)} geo_before=({geo_before.x()},{geo_before.y()},{geo_before.width()},{geo_before.height()})"
                f" orig=({self.original_geometry.x()},{self.original_geometry.y()},{self.original_geometry.width()},{self.original_geometry.height()})"
            )
        except Exception:
            print(f"[window_mgr] restore id={id(self.window)} geo_before=<unavailable>")

        self.window.setGeometry(self.original_geometry)
        self.window.showNormal()
        self.window.raise_()  # Bring the window to the front
        self.window.activateWindow()  # Focus the window
        self.is_maximized = False
        self.is_minimized = False

    def _toggle_maximize(self):
        if self.is_maximized:
            self._restore_window()
        else:
            self._maximize_window()