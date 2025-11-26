import json
from typing import Optional, Sequence

from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from ...constants.file_paths import QssPaths
from ...python.api_actions import APIModuleActions
from ...utils.url_manager import Module
from ...constants.settings_keys import SettingsService
from ...utils.MapTools.MapHelpers import MapHelpers
from ...widgets.theme_manager import ThemeManager
from ...utils.MapTools.item_selector_tools import PropertiesSelectors

class SignalTestModule(QWidget):
    """Interactive playground for testing property lookups via GraphQL."""

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
        self._settings = SettingsService()
        self._module_options = self._build_module_options()
        self._target_module = self._module_options[0] if self._module_options else Module.CONTRACT

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN, QssPaths.COMBOBOX])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        intro = QLabel(
            "Contract-connected properties tester (calls module_item_connected_properties)."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        module_block = QVBoxLayout()
        module_block.setSpacing(4)
        module_label = QLabel("Module")
        self.module_selector = QComboBox()
        for module in self._module_options:
            display = module.value.capitalize()
            self.module_selector.addItem(display, module)
        self.module_selector.currentIndexChanged.connect(self._on_module_changed)
        module_block.addWidget(module_label)
        module_block.addWidget(self.module_selector)

        id_block = QVBoxLayout()
        id_block.setSpacing(4)
        id_label = QLabel("Item ID")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter module item ID")
        self.id_input.setText("35")
        id_block.addWidget(id_label)
        id_block.addWidget(self.id_input)

        input_row.addLayout(module_block, 1)
        input_row.addLayout(id_block, 1)
        outer.addLayout(input_row)

        self.active_layer_label = QLabel()
        self.active_layer_label.setObjectName("ActiveLayerLabel")
        self.active_layer_label.setStyleSheet("color: #888;")
        outer.addWidget(self.active_layer_label)

        self.fetch_button = QPushButton("Fetch connected properties")
        self.fetch_button.setObjectName("SignalTestFetchButton")
        self.fetch_button.setStyleSheet(
            """
            #SignalTestFetchButton {
                background-color: #2962ff;
                color: #ffffff;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 600;
            }
            #SignalTestFetchButton:disabled {
                background-color: #9bb3ff;
                color: #f0f0f0;
            }
            """
        )
        self.fetch_button.clicked.connect(self._handle_fetch)
        actions_frame = QFrame()
        actions_frame.setObjectName("SignalTestActions")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)
        actions_layout.addWidget(self.fetch_button)
        actions_layout.addStretch(1)
        outer.addWidget(actions_frame)

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Response payload will appear here")
        outer.addWidget(self.output_area, 1)

        self._refresh_active_layer_label()

    def _build_module_options(self) -> Sequence[Module]:
        """Return a stable list of modules that can be targeted by the playground."""
        return [Module.CONTRACT, Module.PROJECT, Module.PROPERTY]

    def _on_module_changed(self, index: int) -> None:
        module = self.module_selector.itemData(index)
        if isinstance(module, Module):
            self._target_module = module
        self._refresh_active_layer_label()

    def _refresh_active_layer_label(self) -> None:
        if not hasattr(self, "active_layer_label"):
            return
        module_key = self._target_module.value
        stored_name = self._settings.module_main_layer_id(module_key) or ""
        if stored_name:
            layer_loaded = MapHelpers.resolve_layer(stored_name) is not None
            suffix = "" if layer_loaded else " (layer not loaded in project)"
            text = f"Active layer: {stored_name}{suffix}"
        else:
            text = "Active layer: — (no layer configured)"
        self.active_layer_label.setText(text)

    def _handle_fetch(self) -> None:
        item_id = (self.id_input.text() or "").strip()
        if not item_id:
            self._render_result({"error": "Contract ID is required"})
            return

        self.fetch_button.setEnabled(False)
        try:
            print(f"[SignalTestModule] Fetching connected properties for module {self._target_module.value}, item ID {item_id}")
            numbers = APIModuleActions.get_module_item_connected_properties(
                self._target_module.value,
                item_id,
            )
            result = {
                "module": self._target_module.value,
                "itemId": item_id,
                "cadastralCount": len(numbers),
                "cadastralNumbers": numbers,
            }
            self._render_result(result)
            PropertiesSelectors.show_connected_properties_on_map(numbers)
        except Exception as exc:
            self._render_result({"error": str(exc)})
        finally:
            self.fetch_button.setEnabled(True)

    def _render_result(self, data) -> None:
        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            text = str(data)
        self.output_area.setPlainText(text)

    def activate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def deactivate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def get_widget(self) -> QWidget:
        return self

