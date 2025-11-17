from datetime import datetime
from typing import List, Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.gui import QgsCheckableComboBox

from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module
from ...widgets.BaseFilterWidget import BaseFilterWidget
from typing import Callable, Tuple
from functools import partial



combo_item_list = [
    ("id=1", "Option 1", True),
    ("id=2", "Option 2", False),
    ("id=3", "Option 3", False),
]

class SignalTestModule(QWidget):
    """Standalone module that exposes the filter widget signal harness inside the plugin."""

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
        # unified signal for Mode 1 (name, texts, ids)




    ) -> None:
        super().__init__(parent)

        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager
        self.display_name = "Signaltest"
        self._display_label = None
        # testing state
        self._test_teardown: Callable[[], None] | None = None
        if self.lang_manager:
            self._display_label = self.lang_manager.translate(self.display_name)

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN, QssPaths.COMBOBOX])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        intro = QLabel(
            self._display_label
            if self._display_label
            else "Interact with the comboboxes below to inspect signal emissions."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)


        self.combobox = QgsCheckableComboBox(self)
        for id_val, label, checked in combo_item_list:
            self.combobox.addItem(label, id_val)
            row = self.combobox.count() - 1
            state = Qt.Checked if checked else Qt.Unchecked
            self.combobox.setItemCheckState(row, state)

        

        self.base_filter = BaseFilterWidget._init_checkable_combo(self, object_name="TestCombo", with_shadow=True)
        for id_val, label, checked in combo_item_list:
            self.base_filter.addItem(label, id_val)
            row = self.base_filter.count() - 1
            state = Qt.Checked if checked else Qt.Unchecked
            self.base_filter.setItemCheckState(row, state)

        self.base_filter.blockSignals(False)

        outer.addWidget(self.combobox)

        outer.addWidget(self.base_filter)

        self._results_panel = self._build_results_panel()

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.clear_button = QPushButton("Clear Signal Log", self)
        self.clear_button.clicked.connect(self._clear_log)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        outer.addLayout(button_row)
        outer.addWidget(self._results_panel)

        self._wire_signals()

    def _log_event(self, event: str, *details: object) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        summary = " | ".join(str(d) for d in details if d is not None)
        line = f"{timestamp} :: {event}"
        if summary:
            line = f"{line} -> {summary}"
        self.signal_area.appendPlainText(line)


    def _build_results_panel(self) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.selection_area = QPlainTextEdit(container)
        self.selection_area.setReadOnly(True)
        self.selection_area.setPlaceholderText("Combobox checked items appear here")

        self.signal_area = QPlainTextEdit(container)
        self.signal_area.setReadOnly(True)
        self.signal_area.setPlaceholderText("Signal emissions are logged here")

        layout.addWidget(self.selection_area, 1)
        layout.addWidget(self.signal_area, 1)
        return container

    def _wire_signals(self) -> None:
        self._test_teardown = self.bind_selection_forwarders(self._forwarder_consumer)

    def _forwarder_consumer(self, name: str, texts: list[str], ids: list[object]) -> None:
        if hasattr(self, "signal_area"):
            self.signal_area.appendPlainText(f"fwd: {name} -> texts={texts}, ids={ids}")
        if hasattr(self, "selection_area"):
            self.selection_area.setPlainText(
                f"Mode 3 — {name}\n"
                f"Checked texts: {', '.join(texts)}\n"
                f"Selected IDs: {', '.join(map(str, ids))}"
            )

    def _clear_log(self) -> None:
        self.signal_area.clear()

    def activate(self) -> None:
        self._log_event("module", "Activated")

    def deactivate(self) -> None:
        self._log_event("module", "Deactivated")
        if self._test_teardown:
            self._test_teardown()

    def get_widget(self) -> QWidget:
        return self

    def _disconnect_test_wiring(self) -> None:
        if self._test_teardown:
            try:
                self._test_teardown()
            finally:
                self._test_teardown = None

    def bind_selection_forwarders(self, target_slot: Callable[[str, list[str], list[object]], None]) -> Callable[[], None]:
        # Mode 3: connect forwarders and return teardown
        connections: list[Tuple[object, object]] = []

        def forward(combo):
            name  = combo.objectName() or "QgsCheckableComboBox"
            texts = combo.checkedItems() or []
            ids   = combo.checkedItemsData() or []
            target_slot(name, texts, ids)

        for w in (self.combobox, self.base_filter):
            cb = partial(forward, w)
            w.checkedItemsChanged.connect(cb)
            connections.append((w, cb))

        def teardown():
            for w, cb in connections:
                try:
                    w.checkedItemsChanged.disconnect(cb)
                except Exception:
                    pass
            if hasattr(self, "signal_area"):
                self.signal_area.appendPlainText("teardown: disconnected forwarders")

        return teardown

