# --- ToolbarArea class ---
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths, StylePaths


class ToolbarArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarArea")
        layout = QVBoxLayout(self)
        self.label = QLabel("Toolbar Area (add widgets here)")
        self.label.setObjectName("SpecialToolbarLabel")
        layout.addWidget(self.label)

        # Determine current theme and theme directory
        from ..widgets.theme_manager import ThemeManager
        theme = ThemeManager.load_theme_setting()
        theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT

        # Apply only the module-specific QSS
        ThemeManager.apply_theme(self, theme_dir, [QssPaths.MODULE_TOOLBAR])
