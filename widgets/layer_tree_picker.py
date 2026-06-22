# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from qgis.core import Qgis, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMapLayer, QgsProject, QgsVectorLayer

from ..constants.file_paths import QssPaths
from .theme_manager import ThemeManager


class ComboBoxTextFrame(QLabel):
    """Named label class used by LayerTreePicker.qss."""


class LayerTreePicker(QWidget):
    """Combo-like layer picker that preserves QGIS group/subgroup structure."""

    layerChanged = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._project: Optional[QgsProject] = QgsProject.instance() if QgsProject else None
        self._current_layer_id = ""
        self._allow_empty = False
        self._empty_text = ""
        self._show_crs = False
        self._filters = None
        self._popup: Optional[QFrame] = None

        self.setObjectName("LayerTreePicker")
        self.setFocusPolicy(Qt.StrongFocus)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._container = QFrame(self)
        self._container.setObjectName("LayerTreePickerContainer")
        self._container.setFocusPolicy(Qt.StrongFocus)
        container_layout = QHBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self._text_frame = QFrame(self._container)
        self._text_frame.setObjectName("ComboAreaTextFrame")
        text_layout = QHBoxLayout(self._text_frame)
        text_layout.setContentsMargins(8, 0, 6, 0)
        text_layout.setSpacing(0)
        self._label = ComboBoxTextFrame(self._text_frame)
        self._label.setObjectName("ComboBoxTextFrame")
        self._label.setText("")
        self._label.setTextInteractionFlags(Qt.NoTextInteraction)
        text_layout.addWidget(self._label)
        container_layout.addWidget(self._text_frame, 1)

        self._dropdown_frame = QFrame(self._container)
        self._dropdown_frame.setObjectName("DropdownFrame")
        dropdown_layout = QHBoxLayout(self._dropdown_frame)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)
        self._arrow = QLabel("v", self._dropdown_frame)
        self._arrow.setObjectName("LayerTreePickerArrow")
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        dropdown_layout.addWidget(self._arrow, 0, Qt.AlignCenter)
        container_layout.addWidget(self._dropdown_frame, 0)

        root.addWidget(self._container)
        self._apply_style()
        self._sync_label()

    def setProject(self, project) -> None:  # noqa: N802 - QGIS-compatible API
        self._project = project
        self._sync_label()

    def project(self):
        return self._project

    def setAllowEmptyLayer(self, allow: bool, text: str = "") -> None:  # noqa: N802
        self._allow_empty = bool(allow)
        self._empty_text = str(text or "")
        self._sync_label()

    def setShowCrs(self, show: bool) -> None:  # noqa: N802
        self._show_crs = bool(show)
        self._sync_label()

    def setFilters(self, filters) -> None:  # noqa: N802
        self._filters = filters

    def setLayer(self, layer: QgsMapLayer | None) -> None:  # noqa: N802
        layer_id = layer.id() if layer is not None else ""
        if layer_id == self._current_layer_id:
            self._sync_label()
            return
        self._current_layer_id = layer_id
        self._sync_label()
        self.layerChanged.emit(layer)

    def currentLayer(self) -> QgsMapLayer | None:  # noqa: N802
        project = self._project or (QgsProject.instance() if QgsProject else None)
        if project is None or not self._current_layer_id:
            return None
        return project.mapLayer(self._current_layer_id)

    def retheme(self) -> None:
        self._apply_style()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._toggle_popup()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._toggle_popup()
            event.accept()
            return
        super().keyPressEvent(event)

    def _toggle_popup(self) -> None:
        if not self.isEnabled():
            return
        if self._popup is not None:
            self._close_popup()
            return
        self._open_popup()

    def _open_popup(self) -> None:
        popup = QFrame(self, flags=Qt.Popup | Qt.FramelessWindowHint)
        popup.setObjectName("LayerTreePopup")
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tree = QTreeWidget(popup)
        tree.setHeaderHidden(True)
        tree.setRootIsDecorated(True)
        tree.setUniformRowHeights(True)
        tree.setMinimumWidth(max(320, self.width()))
        tree.setMaximumHeight(360)
        tree.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(tree)
        self._populate_tree(tree)

        self._popup = popup
        self._apply_style(popup)
        popup.move(self.mapToGlobal(self.rect().bottomLeft()))
        popup.show()

    def _close_popup(self) -> None:
        popup = self._popup
        self._popup = None
        if popup is not None:
            try:
                popup.close()
            except RuntimeError:
                pass

    def _populate_tree(self, tree: QTreeWidget) -> None:
        tree.clear()
        if self._allow_empty:
            item = QTreeWidgetItem([self._empty_text or "-"])
            item.setData(0, Qt.UserRole, "")
            tree.addTopLevelItem(item)

        project = self._project or (QgsProject.instance() if QgsProject else None)
        root = project.layerTreeRoot() if project is not None else None
        if root is None:
            return

        for child in root.children():
            self._add_tree_node(tree, None, child)
        tree.expandAll()
        self._select_current_item(tree)

    def _add_tree_node(self, tree: QTreeWidget, parent_item: QTreeWidgetItem | None, node) -> bool:
        if isinstance(node, QgsLayerTreeLayer):
            layer = node.layer()
            if layer is None or not self._layer_allowed(layer):
                return False
            item = QTreeWidgetItem([self._layer_label(layer)])
            item.setData(0, Qt.UserRole, layer.id())
            if parent_item is None:
                tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            return True

        if isinstance(node, QgsLayerTreeGroup):
            group_item = QTreeWidgetItem([node.name()])
            group_item.setData(0, Qt.UserRole, None)
            added = False
            for child in node.children():
                added = self._add_tree_node(tree, group_item, child) or added
            if not added:
                return False
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            if parent_item is None:
                tree.addTopLevelItem(group_item)
            else:
                parent_item.addChild(group_item)
            return True

        return False

    def _select_current_item(self, tree: QTreeWidget) -> None:
        target = self._current_layer_id
        if not target and self._allow_empty and tree.topLevelItemCount() > 0:
            tree.setCurrentItem(tree.topLevelItem(0))
            return
        matches = tree.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive)
        for item in matches:
            if item.data(0, Qt.UserRole) == target:
                tree.setCurrentItem(item)
                tree.scrollToItem(item)
                return

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        layer_id = item.data(0, Qt.UserRole)
        if layer_id is None:
            return
        project = self._project or (QgsProject.instance() if QgsProject else None)
        layer = project.mapLayer(layer_id) if (project is not None and layer_id) else None
        self._close_popup()
        self.setLayer(layer)

    def _layer_allowed(self, layer: QgsMapLayer) -> bool:
        filters = self._filters
        if filters is None:
            return True
        try:
            if filters & Qgis.LayerFilter.HasGeometry:
                if layer.type() != QgsMapLayer.VectorLayer:
                    return False
                if isinstance(layer, QgsVectorLayer) and layer.geometryType() < 0:
                    return False
        except Exception:
            return True
        return True

    def _layer_label(self, layer: QgsMapLayer) -> str:
        label = layer.name()
        if self._show_crs:
            try:
                authid = layer.crs().authid()
                if authid:
                    label = f"{label} ({authid})"
            except Exception:
                pass
        return label

    def _sync_label(self) -> None:
        layer = self.currentLayer()
        if layer is not None:
            self._label.setText(self._layer_label(layer))
            self.setToolTip(self._layer_label(layer))
            return
        self._label.setText(self._empty_text or "-")
        self.setToolTip(self._empty_text or "")

    def _apply_style(self, target: QWidget | None = None) -> None:
        ThemeManager.apply_module_style(target or self, [QssPaths.LAYER_TREE_PICKER])
