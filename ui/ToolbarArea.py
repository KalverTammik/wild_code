"""Standalone toolbar widget with left/right slots and a centered title.

API:
- set_title(text: str)
- add_left(widget: QWidget) / clear_left()
- add_right(widget: QWidget) / clear_right()
- retheme() – reapplies toolbar QSS
"""

# --- ToolbarArea class ---
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QPushButton,
    QSpacerItem,
)
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtCore import pyqtSignal
class ModuleToolbarArea(QWidget):
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
    
    filtersChanged = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarArea")

        # Main horizontal layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(3)

        self._left = QWidget(self)
        self._left.setObjectName("ToolbarLeft")

        # Start with an empty left layout. We'll add a single stretch after the first
        # widget is inserted so subsequent widgets remain left-aligned.
        self._left_layout = QHBoxLayout(self._left)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(2)
        self._left_has_spacer = False

        # Right slot container
        self._right = QWidget(self)
        self._right.setObjectName("ToolbarRight")
        self._right_layout = QHBoxLayout(self._right)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(2)

        # Compose
        self._layout.addWidget(self._left, 0)
        self._layout.addWidget(self._right, 0)

        # Apply toolbar + centralized combo styling (includes ComboBox.qss)
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])


    # --- Public API ---
    def add_refresh_button(self):
        """
        Generate and return a QWidget containing the refresh button.
        This ensures compatibility with layouts that only accept widgets.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        refresh_button = QPushButton("✖")
        refresh_button.setObjectName("FeedRefreshButton")
        
        size_px = 28
        refresh_button.setFixedSize(size_px, size_px)
        
        refresh_button.clicked.connect(self._on_refresh_clicked)  # type: ignore[attr-defined]

        layout.addWidget(refresh_button)
        return container

    def add_left(self, widget: QWidget) -> None:
        if widget is None:
            return

        # If no spacer/stretch has been added yet, add the widget then append a stretch
        # so that remaining free space is absorbed to the right and widgets stay left-aligned.
        if not getattr(self, '_left_has_spacer', False):
            self._left_layout.addWidget(widget)
            self._left_layout.addStretch(1)
            self._left_has_spacer = True
            return

        # Insert the new widget before the trailing stretch so widgets keep left-to-right order
        try:
            count = self._left_layout.count()
            # trailing stretch is expected to be the last item
            insert_index = max(0, count - 1)
            self._left_layout.insertWidget(insert_index, widget)
        except Exception:
            # Fallback: append to end
            self._left_layout.addWidget(widget)

    def add_right(self, widget: QWidget) -> None:
        if widget is not None:
            self._right_layout.addWidget(widget)

    def clear_left(self) -> None:
        ModuleToolbarArea._clear_layout(self._left_layout)

    def clear_right(self) -> None:
        ModuleToolbarArea._clear_layout(self._right_layout)

    def retheme(self) -> None:
        """Re-apply toolbar QSS and propagate to registered filter widgets.

        Called by the dialog's theme toggle sweep. We explicitly retheme
        children that expose a retheme() method so they refresh immediately
        even if the generic sweep order changes.
        """
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])

        # Propagate to registered filter widgets
        for widget in getattr(self, 'filter_widgets', {}).values():
            if hasattr(widget, 'retheme') and callable(widget.retheme):
                try:
                    widget.retheme()
                except Exception:
                    pass

        # Propagate to any child widgets that have retheme methods
        for child in self.findChildren(QWidget):
            if hasattr(child, 'retheme') and callable(child.retheme) and child != self:
                try:
                    child.retheme()
                except Exception:
                    pass
    
    @staticmethod
    def _clear_layout(layout: QHBoxLayout) -> None:
        try:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        except Exception:
            pass
