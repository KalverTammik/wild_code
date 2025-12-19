import json
from typing import Optional, Sequence

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QWidget,
    QPushButton,
)

from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager

from qgis.gui import QgsMapLayerComboBox
from qgis.core import Qgis, QgsMapLayer


class SignalTestModule(QWidget):
    """Simple viewer for inspecting signals and payloads sent around the plugin.

    Currently focused on showing what SearchResultsWidget emits when the user
    clicks on a search result, but can be reused for other signal payloads.
    """

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)

        self._qss_files = qss_files


        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager
        self.display_name = "Signaltest"

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        intro = QLabel(
            "Signal tester – shows payloads sent from other parts of the plugin.\n"
            "For now it focuses on unified search result clicks."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Signal payloads will appear here")
        outer.addWidget(self.output_area, 1)


        # Live layer picker example powered by QgsMapLayerComboBox
        layer_intro = QLabel(
            "Layer picker below is backed by QgsMapLayerComboBox "
            "(see https://qgis.org/pyqgis/master/gui/QgsMapLayerComboBox.html)."
        )
        layer_intro.setWordWrap(True)
        outer.addWidget(layer_intro)

        self.layer_combo = QgsMapLayerComboBox(self)
        self.layer_combo.setAllowEmptyLayer(True, "No layer selected")
        self.layer_combo.setShowCrs(True)
        self.layer_combo.setFilters(Qgis.LayerFilter.HasGeometry)
        self.layer_combo.layerChanged.connect(self._on_layer_combo_layer_changed)
        outer.addWidget(self.layer_combo)

    def _render_result(self, data) -> None:
        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            text = str(data)
        self.output_area.setPlainText(text)

    def _on_layer_combo_layer_changed(self, layer: Optional[QgsMapLayer]) -> None:
        payload = {
            "kind": "map-layer-selection",
            "source": "QgsMapLayerComboBox.layerChanged",
            "layer": None,
        }
        if layer is not None:
            payload["layer"] = {
                "id": layer.id(),
                "name": layer.name(),
                "provider": layer.providerType(),
                "crs": layer.crs().authid() if layer.crs() else None,
            }
        self._render_result(payload)

    def show_external_signal_payload(self, source: str, module: str, item_id: str, title: str) -> None:
        """Display payload received from external signals (e.g. search widget).

        This is meant to be called when some other part of the plugin wants
        to inspect what it sent, such as SearchResultsWidget.resultClicked.

        Args:
            source: Short label describing where the signal came from.
            module: Module identifier string from the search result.
            item_id: Item id from the search result.
            title: Human readable title from the search result.
        """
        payload = {
            "kind": "external-signal",
            "source": source,
            "searchResult": {
                "module": module,
                "id": item_id,
                "title": title,
            },
        }

        self._render_result(payload)


    def activate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def deactivate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def get_widget(self) -> QWidget:
        return self

