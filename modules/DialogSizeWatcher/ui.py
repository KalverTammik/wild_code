
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtCore import Qt
from ...constants.file_paths import QssPaths

class DialogSizeWatcherUI(QWidget):
    def __init__(self, lang_manager, theme_manager):
        super().__init__()
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.x_label = QLabel(self.lang_manager.translate("x_label"))
        self.x_edit = QLineEdit()
        self.x_edit.setReadOnly(True)
        self.y_label = QLabel(self.lang_manager.translate("y_label"))
        self.y_edit = QLineEdit()
        self.y_edit.setReadOnly(True)
        self.width_label = QLabel(self.lang_manager.translate("width_label"))
        self.width_edit = QLineEdit()
        self.width_edit.setReadOnly(True)
        self.height_label = QLabel(self.lang_manager.translate("height_label"))
        self.height_edit = QLineEdit()
        self.height_edit.setReadOnly(True)
        layout.addWidget(self.x_label)
        layout.addWidget(self.x_edit)
        layout.addWidget(self.y_label)
        layout.addWidget(self.y_edit)
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_edit)
        layout.addWidget(self.height_label)
        layout.addWidget(self.height_edit)
        self.setLayout(layout)
        # Provide theme_dir from theme_manager or parent context
        if hasattr(self.theme_manager, 'theme_dir'):
            theme_dir = self.theme_manager.theme_dir
        else:
            # fallback: try to get from parent or use None
            theme_dir = None

        if theme_dir is not None:
            self.theme_manager.apply_theme(self, theme_dir, [QssPaths.MAIN])
        else:
            pass

    def refresh_theme(self, theme_dir=None):
        """
        Re-apply the theme for this widget. Call this after a theme toggle.
        """
        if theme_dir is None:
            if hasattr(self.theme_manager, 'theme_dir'):
                theme_dir = self.theme_manager.theme_dir
            else:
                theme_dir = None
        if theme_dir is not None:
            self.theme_manager.apply_theme(self, theme_dir, [QssPaths.MAIN])

    def update_size(self, x, y, width, height):
        self.x_edit.setText(str(x))
        self.y_edit.setText(str(y))
        self.width_edit.setText(str(width))
        self.height_edit.setText(str(height))
