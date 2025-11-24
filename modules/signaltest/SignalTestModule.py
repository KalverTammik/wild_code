from typing import Callable, Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.core import QgsSettings

from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module


class SignalTestModule(QWidget):
    """Utility module that now focuses solely on viewing and pruning stored settings."""

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)

        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager
        self.display_name = "Signaltest"
        self._display_label = None
        if self.lang_manager:
            self._display_label = self.lang_manager.translate(self.display_name)

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN, QssPaths.COMBOBOX])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        intro = QLabel(
            self._display_label
            if self._display_label
            else "Inspect and manage stored QgsSettings entries for the plugin."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        self._settings_panel = self._build_settings_inspector()
        outer.addWidget(self._settings_panel)

        self._populate_settings_list()

    def _build_settings_inspector(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QLabel("QgsSettings entries under wild_code/", container)
        header.setObjectName("SettingsInspectorTitle")
        layout.addWidget(header)

        self.settings_list = QListWidget(container)
        self.settings_list.setObjectName("SettingsInspectorList")
        self.settings_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.settings_list.itemSelectionChanged.connect(self._update_settings_preview)
        layout.addWidget(self.settings_list, 2)

        self.settings_preview = QPlainTextEdit(container)
        self.settings_preview.setReadOnly(True)
        self.settings_preview.setPlaceholderText("Selected settings will appear here")
        layout.addWidget(self.settings_preview, 1)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        refresh_btn = QPushButton("Refresh Settings", container)
        refresh_btn.clicked.connect(self._refresh_settings_list)
        delete_btn = QPushButton("Delete Selected", container)
        delete_btn.clicked.connect(self._delete_selected_settings)
        controls.addWidget(refresh_btn)
        controls.addWidget(delete_btn)
        controls.addStretch(1)
        layout.addLayout(controls)
        return container

    def _populate_settings_list(self) -> None:
        settings = QgsSettings()
        keys = sorted(k for k in settings.allKeys() if k.startswith("wild_code/"))
        self.settings_list.clear()
        for key in keys:
            value = settings.value(key)
            display = f"{key} = {value}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, key)
            item.setData(Qt.UserRole + 1, value)
            self.settings_list.addItem(item)
        self._update_settings_preview()

    def _refresh_settings_list(self) -> None:
        self._populate_settings_list()

    def _delete_selected_settings(self) -> None:
        selected = self.settings_list.selectedItems()
        if not selected:
            return
        settings = QgsSettings()
        for item in selected:
            key = item.data(Qt.UserRole)
            if key:
                settings.remove(key)
        self._populate_settings_list()

    def _update_settings_preview(self) -> None:
        selected = self.settings_list.selectedItems()
        if not selected:
            self.settings_preview.setPlainText("Select settings to inspect")
            return
        lines = []
        for item in selected:
            key = item.data(Qt.UserRole)
            value = item.data(Qt.UserRole + 1)
            lines.append(f"{key} = {value}")
        self.settings_preview.setPlainText("\n".join(lines))

    def activate(self) -> None:
        """Module lifecycle hook (no-op for the inspector)."""

    def deactivate(self) -> None:
        """Module lifecycle hook (no-op for the inspector)."""

    def get_widget(self) -> QWidget:
        return self

    def bind_selection_forwarders(self, target_slot: Callable[[str, list[str], list[object]], None]) -> Callable[[], None]:
        def teardown() -> None:  # Maintains previous API contract.
            return None

        return teardown

