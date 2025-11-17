from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout,QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QSizePolicy, QFrame, QToolButton
from PyQt5.QtGui import QPainter, QFontMetrics, QPalette
from .theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from .theme_manager import styleExtras, ThemeShadowColors

from qgis.core import QgsProject, QgsMapLayer
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer  # for typing/instance checks

from ..utils.logger import error as log_error

# Custom frame for QComboBox-style text display with eliding
class ComboBoxTextFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._placeholder = ""
        
    def setText(self, text):
        if self._text != text:
            self._text = text
            self.update()  # Trigger repaint
            
    def text(self):
        return self._text
        
    def setPlaceholderText(self, placeholder):
        self._placeholder = placeholder
        self.update()
        
    def placeholderText(self):
        return self._placeholder
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get the text to display
        display_text = self._text if self._text else self._placeholder
        
        # Get font metrics for eliding calculation
        font_metrics = QFontMetrics(self.font())
        
        # Calculate available width (accounting for margins)
        rect = self.contentsRect()
        available_width = rect.width()
        
        # Elide text if necessary (like QComboBox does)
        elided_text = font_metrics.elidedText(display_text, Qt.ElideRight, available_width)
        
        # Set text color based on whether it's placeholder or actual text
        palette = self.palette()
        if self._text:
            text_color = palette.color(QPalette.Text)
        else:
            # Use placeholder color (slightly dimmed)
            text_color = palette.color(QPalette.Text)
            text_color.setAlpha(128)  # 50% opacity for placeholder
            
        painter.setPen(text_color)
        painter.setFont(self.font())
        
        # Draw text left-aligned, vertically centered
        text_rect = rect.adjusted(0, 0, 0, 0)  # No additional margins
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)

# --- Shared snapshot helpers (module-level) -----------------------------------
@staticmethod
def generate_projects_layer_item_list():
    """Build tree group from layers."""
    project = QgsProject.instance() 

    root = project.layerTreeRoot()
    return _snapshot_from_group(root)

@staticmethod
def _snapshot_from_group(group_node):
    items = []
    children = group_node.children()
    for ch in children:
        if QgsLayerTreeGroup and isinstance(ch, QgsLayerTreeGroup):
            items.append({
                "type": "group",
                "name": ch.name(),
                "children": _snapshot_from_group(ch)
            })
        elif QgsLayerTreeLayer and isinstance(ch, QgsLayerTreeLayer):
            lyr = ch.layer()
            if lyr:
                items.append({
                    "type": "layer",
                    "id": lyr.id(),
                    "name": lyr.name()
                })
    return items

class LayerTreePicker(QWidget):
    """
    Scrollable tree-based layer selector with dropdown-like UX:
    - Shows a button first; clicking it opens a popup (Qt.Popup) containing a hierarchical QTreeWidget.
    - Full project hierarchy is visible in the popup; after selecting a layer the popup closes.
    - Preserves project order using a shared snapshot or reading the project directly.
    - Emits the same signals as LayerDropdown for consistency.

    Supports lazy loading via on_settings_activate(snapshot) and memory release via on_settings_deactivate().
    """

    layerChanged = pyqtSignal(object)  # QgsMapLayer or None
    layerIdChanged = pyqtSignal(str)

    def __init__(self, parent=None, project=None, placeholder: str = "Select layer"):
        super().__init__(parent)
        self._project = project or (QgsProject.instance() if QgsProject else None)
        self._snapshot = None
        self._selected_layer_id = ""
        self._item_by_id = {}
        self._placeholder = placeholder

        self._container = QFrame(self)
        self._container.setObjectName("LayerTreePickerContainer")
        self._container.setContentsMargins(10, 0, 0, 0)

        # Set up the horizontal layout inside the container
        layout = QHBoxLayout(self._container)
        layout.setContentsMargins(0, 0, 0, 0)  # QComboBox-like margins
        layout.setSpacing(0)  # Minimal spacing like QComboBox
        

        # Main button area (frame with custom text display)
        self._button_frame = QFrame(self._container)
        self._button_frame.setObjectName("ComboAreaTextFrame")
        
        button_layout = QVBoxLayout(self._button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)  # Internal margins for text like QComboBox
        button_layout.setSpacing(0)
        
        # Use custom text display frame instead of QLabel
        self._text_display = ComboBoxTextFrame(self._button_frame)
        self._text_display.setPlaceholderText(self._placeholder)
        button_layout.addWidget(self._text_display)
        
        self._button_frame.mousePressEvent = lambda event: self._toggle_popup()
        layout.addWidget(self._button_frame, 1)  # Stretch factor 1 - expands like QComboBox text area

        # Dropdown frame with arrow
        self._dropdown_frame = QFrame(self._container)
        self._dropdown_frame.setObjectName("DropdownFrame")
        self._dropdown_frame.setFixedWidth(22)  # Reduced from 24px for narrower arrow frame
        
        frame_layout = QVBoxLayout(self._dropdown_frame)
        frame_layout.setContentsMargins(2, 2, 2, 2)  # Add padding around arrow like QComboBox
        frame_layout.setSpacing(0)
        
        # Arrow button like QComboBox
        self._arrow_button = QToolButton(self._dropdown_frame)
        self._arrow_button.setArrowType(Qt.DownArrow)
        self._arrow_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._arrow_button.setAutoRaise(True)
        self._arrow_button.clicked.connect(self._toggle_popup)
        frame_layout.addWidget(self._arrow_button)
        
        layout.addWidget(self._dropdown_frame, 0)  # Stretch factor 0 - fixed size like QComboBox arrow
        
        # Connect dropdown frame click
        self._dropdown_frame.mousePressEvent = lambda event: self._toggle_popup()

        # Set up main widget layout
        widget_layout = QVBoxLayout(self)
        widget_layout.setContentsMargins(4, 2, 4, 2)  # Margins for shadow visibility
        widget_layout.setSpacing(0)
        widget_layout.addWidget(self._container)

        # Popup container with a tree
        self._popup = QFrame(None, Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # No parent for top-level popup
        self._popup.setObjectName("LayerTreePopup")
        pl = QVBoxLayout(self._popup)
        pl.setContentsMargins(4, 4, 4, 4)
        pl.setSpacing(2)

        self._tree = QTreeWidget(self._popup)
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self._tree.setFocusPolicy(Qt.StrongFocus)
        self._tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tree.setRootIsDecorated(False)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        pl.addWidget(self._tree)
        self._popup.hide()

    # Snapshot API -----------------------------------------------------
    def setSnapshot(self, snapshot):
        self._snapshot = snapshot or []

    def getSnapshot(self):
        return self._snapshot

    # Project association ---------------------------------------------
    def project(self):
        return self._project

    def setProject(self, project):
        self._project = project

    # Selection --------------------------------------------------------
    def selectedLayerId(self) -> str:
        return self._selected_layer_id

    def selectedLayer(self):
        if not self._project or not self._selected_layer_id:
            return None
        try:
            return self._project.mapLayer(self._selected_layer_id)
        except Exception:
            return None

    def setSelectedLayerId(self, layer_id: str):
        self._selected_layer_id = layer_id or ""
        if not layer_id:
            self._tree.clearSelection()
            self._update_button_label()
            return
        item = self._item_by_id.get(layer_id)
        if item is not None:
            self._tree.setCurrentItem(item)
            # ensure visibility when opened
            it = item.parent()
            while it is not None:
                it.setExpanded(True)
                it = it.parent()
        self._update_button_label()

    def clearSelection(self):
        self._selected_layer_id = ""
        self._tree.clearSelection()
        self._update_button_label()

    def _update_button_label(self):
        name = self._resolve_layer_name(self._selected_layer_id)
        display_text = name or self._placeholder
        self._text_display.setText(display_text)

    def retheme(self):
        """Apply theme styling to the dropdown button and arrow."""
        try:
            ThemeManager.apply_module_style(self, [QssPaths.LAYER_TREE_PICKER])
        except Exception:
            pass

    # Build / refresh --------------------------------------------------
    def refresh(self):
        self._tree.clear()
        self._item_by_id.clear()
        if self._snapshot:
            self._build_tree_from_snapshot(self._snapshot, self._tree.invisibleRootItem())
        else:
            root = None
            try:
                root = self._project.layerTreeRoot() if (self._project and hasattr(self._project, 'layerTreeRoot')) else None
            except Exception:
                root = None
            if root is not None:
                self._build_tree_from_group(root, self._tree.invisibleRootItem())
        self._tree.expandAll()
        self._update_button_label()

    # Lifecycle --------------------------------------------------------
    def on_settings_activate(self, snapshot=None):
        if snapshot is not None:
            self.setSnapshot(snapshot)
        self.refresh()
        self._popup.hide()

    def on_settings_deactivate(self):
        # release memory and collapse
        self._tree.clear()
        self._item_by_id.clear()
        self._popup.hide()

    # Popup control ----------------------------------------------------
    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
            return

        # Build on demand
        if self._tree.topLevelItemCount() == 0:
            try:
                self.refresh()
            except Exception as e:
                log_error(f"[LayerTreePicker] Refresh failed: {e}")
                return

        # Check if we have any items
        if self._tree.topLevelItemCount() == 0:
            # log_debug("[LayerTreePicker] No items to show in dropdown")
            return

        # Apply LayerTreePicker styling to the popup and button
        try:
            from .theme_manager import ThemeManager
            from ..constants.file_paths import QssPaths
            # Apply LayerTreePicker styling to the popup
            ThemeManager.apply_module_style(self._popup, [QssPaths.LAYER_TREE_PICKER])
            # Apply styling to the button container as well
            ThemeManager.apply_module_style(self, [QssPaths.LAYER_TREE_PICKER])
        except Exception as e:
            log_error(f"[LayerTreePicker] Theme application failed: {e}")

        # Position under the button like a combobox popup
        try:
            btn_rect = self._button_frame.rect()
            global_pos = self._button_frame.mapToGlobal(btn_rect.bottomLeft())
            width = max(self._button_frame.width(), 300)
            height = min(400, max(200, self._tree.topLevelItemCount() * 20 + 40))  # Dynamic height based on item count

            # Ensure popup is properly sized and positioned
            self._popup.resize(width, height)
            self._popup.move(global_pos)

            # log_debug(f"[LayerTreePicker] Showing popup at {global_pos}, size {width}x{height}")
            self._popup.setWindowModality(Qt.NonModal)
            self._popup.show()
            self._popup.raise_()
            self._popup.activateWindow()
            self._tree.setFocus()
        except Exception as e:
            log_error(f"[LayerTreePicker] Popup positioning failed: {e}")

    def _on_dropdown_frame_clicked(self, event):
        """Handle mouse press on dropdown frame."""
        self._toggle_popup()

    # Internal builders ------------------------------------------------
    def _build_tree_from_snapshot(self, items, parent_item: QTreeWidgetItem):
        for it in items:
            typ = it.get('type')
            if typ == 'group':
                group_item = QTreeWidgetItem([it.get('name', '')])
                parent_item.addChild(group_item)
                self._build_tree_from_snapshot(it.get('children', []), group_item)
            elif typ == 'layer':
                layer_item = QTreeWidgetItem([it.get('name', '')])
                parent_item.addChild(layer_item)
                lid = it.get('id', '')
                layer_item.setData(0, Qt.UserRole, lid)
                self._item_by_id[lid] = layer_item

    def _build_tree_from_group(self, group_node, parent_item: QTreeWidgetItem):
        try:
            children = group_node.children()
        except Exception:
            children = []
        for ch in children:
            if QgsLayerTreeGroup and isinstance(ch, QgsLayerTreeGroup):
                group_item = QTreeWidgetItem([ch.name()])
                parent_item.addChild(group_item)
                self._build_tree_from_group(ch, group_item)
            elif QgsLayerTreeLayer and isinstance(ch, QgsLayerTreeLayer):
                lyr = None
                try:
                    lyr = ch.layer()
                except Exception:
                    pass
                if lyr:
                    layer_item = QTreeWidgetItem([lyr.name()])
                    parent_item.addChild(layer_item)
                    lid = lyr.id()
                    layer_item.setData(0, Qt.UserRole, lid)
                    self._item_by_id[lid] = layer_item

    # Handlers ---------------------------------------------------------
    def _on_selection_changed(self):
        item = self._tree.currentItem()
        if not item:
            return
        lid = item.data(0, Qt.UserRole)
        if not lid:
            return  # group selected
        self._selected_layer_id = str(lid)
        self._update_button_label()
        lyr = self.selectedLayer()
        self.layerIdChanged.emit(self._selected_layer_id)
        self.layerChanged.emit(lyr)
        # Close popup after selection
        self._popup.hide()

    # Helpers ----------------------------------------------------------
    def _resolve_layer_name(self, layer_id: str) -> str:
        if not layer_id or not self._project:
            return ""
        try:
            lyr = self._project.mapLayer(layer_id)
            return lyr.name() if lyr else ""
        except Exception:
            return ""

# Deprecated: keep for compatibility, prefer LayerTreePicker
class LayerDropdown(LayerTreePicker):
    def __init__(self, parent=None, project=None, placeholder: str = "Select layer", load_on_init: bool = False):
        super().__init__(parent, project=project, placeholder=placeholder)
        # load_on_init is ignored; LayerTreePicker loads via on_settings_activate/refresh
