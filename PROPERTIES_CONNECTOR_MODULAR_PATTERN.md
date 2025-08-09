# Properties Connector UI Controller - Modular Pattern Example

This document outlines a modular approach for implementing a controller that attaches properties to a module item, inspired by the `PropertiesConnectorUIController` pattern.

## Core Concepts

- **Single Button Action:** The controller is designed to work with a single button as the entry point for attaching properties.
- **Widget State Management:** Ensures only one instance of the properties widget is open at a time.
- **Selection Check:** Only allows the action if a selection is made in the table.
- **Button State Management:** Disables/enables the button to prevent conflicting actions.
- **Widget Initialization:** Handles widget creation, UI loading, and cleanup on close.

## Example Structure

### helpers.py
```python
def disable_button(button):
    button.setEnabled(False)

def enable_button(button):
    button.setEnabled(True)

def has_selection(table):
    selection_model = table.selectionModel()
    return selection_model.hasSelection()
```

### property_attach_controller.py
```python
from .property_attach_widget import PropertyAttachWidget
from .helpers import disable_button, enable_button, has_selection

class PropertyAttachController:
    _is_open = False

    def open_property_attach(self, module, table, button):
        if PropertyAttachController._is_open:
            return

        PropertyAttachController._is_open = True
        disable_button(button)

        if has_selection(table):
            self._init_property_attach(module, table, button)
        else:
            enable_button(button)
            PropertyAttachController._is_open = False

    def _init_property_attach(self, module, table, button):
        self.property_widget = PropertyAttachWidget(table)
        self.property_widget.closed.connect(
            lambda: self._on_widget_closed(button)
        )
        self.property_widget.load_ui(module)

    def _on_widget_closed(self, button):
        enable_button(button)
        PropertyAttachController._is_open = False
```

### property_attach_widget.py
```python
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class PropertyAttachWidget(QWidget):
    closed = pyqtSignal()

    def __init__(self, table):
        super().__init__()
        self.table = table
        # ... setup UI ...

    def load_ui(self, module):
        # ... load UI for the given module ...
        pass

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
```

## Key Points

- The controller manages widget state and button state in a modular way.
- The widget is responsible for its own UI and emits a signal when closed.
- Helpers keep UI logic clean and reusable.

This pattern is clean, modular, and easily extensible for any scenario where you need to attach properties to an item via a single button action.
