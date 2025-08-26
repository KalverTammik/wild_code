"""Standalone toolbar widget with left/right slots and a centered title.

API:
- set_title(text: str)
- add_left(widget: QWidget) / clear_left()
- add_right(widget: QWidget) / clear_right()
- retheme() – reapplies toolbar QSS
"""

# --- ToolbarArea class ---
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
)
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from PyQt5.QtCore import Qt, QCoreApplication

class ToolbarArea(QWidget):
    # --- Filter widget management ---
    def register_filter_widget(self, name, widget):
        """
        Register a filter widget by name and connect its selectionChanged signal to centralized handler.
        """
        if not hasattr(self, 'filter_widgets'):
            self.filter_widgets = {}
        self.filter_widgets[name] = widget
        if hasattr(widget, 'selectionChanged'):
            widget.selectionChanged.connect(self._on_any_filter_changed)
        self.add_left(widget)

    def _on_any_filter_changed(self):
        """
        Centralized handler for all filter widgets. Emits filtersChanged signal with all selected values.
        """
        filters = {}
        for name, widget in getattr(self, 'filter_widgets', {}).items():
            if hasattr(widget, 'selected_ids'):
                filters[name] = widget.selected_ids()
        if hasattr(self, 'filtersChanged'):
            self.filtersChanged.emit(filters)
        QCoreApplication.processEvents()

    # Add a signal for filtersChanged (Qt signal)
    from PyQt5.QtCore import pyqtSignal
    filtersChanged = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarArea")

        # Main horizontal layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(6)

        self._left = QWidget(self)
        self._left.setObjectName("ToolbarLeft")
        self._left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._left_layout = QHBoxLayout(self._left)
        self._left_layout.setContentsMargins(0, 0, 0, 0)

        self._left_layout.setSpacing(6)

        # Center title label (expands; centered text)
        self._title = QLabel("Toolbar Area (add widgets here)", self)
        self._title.setObjectName("SpecialToolbarLabel")
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._title.setAlignment(Qt.AlignCenter)  # type: ignore[name-defined]

        # Right slot container
        self._right = QWidget(self)
        self._right.setObjectName("ToolbarRight")
        self._right_layout = QHBoxLayout(self._right)
        self._right_layout.setContentsMargins(2, 4, 2, 4)
        self._right_layout.setSpacing(2)

        # Compose
        self._layout.addWidget(self._left, 0)
        self._layout.addWidget(self._title, 1)
        self._layout.addWidget(self._right, 0)

        # Apply toolbar + centralized combo styling (includes ComboBox.qss)
        ThemeManager.apply_module_style(self, QssPaths.MAIN)

    # --- Public API ---
    def set_title(self, text: str) -> None:
        self._title.setText(text or "")

    def add_left(self, widget: QWidget) -> None:
        if widget is not None:
            self._left_layout.addWidget(widget)

    def add_right(self, widget: QWidget) -> None:
        if widget is not None:
            self._right_layout.addWidget(widget)

    def clear_left(self) -> None:
        self._clear_layout(self._left_layout)

    def clear_right(self) -> None:
        self._clear_layout(self._right_layout)

    def retheme(self) -> None:
        """Re-apply toolbar QSS and propagate to registered filter widgets.

        Called by the dialog's theme toggle sweep. We explicitly retheme
        children that expose a retheme() method so they refresh immediately
        even if the generic sweep order changes.
        """
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])
   
    # --- Helpers ---
    def _clear_layout(self, layout: QHBoxLayout) -> None:
        try:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        except Exception:
            pass
