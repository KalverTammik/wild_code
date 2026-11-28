"""The layer popup is as tall as its layers need, with compact rows."""
import unittest

from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QTreeWidget

from Kavitro_dev.widgets.layer_tree_picker import LayerTreePicker

_APP = QgsApplication.instance() or QgsApplication([], False)


class LayerTreePopupTest(unittest.TestCase):
    def _popup_tree(self, layer_count: int) -> QTreeWidget:
        project = QgsProject()
        for index in range(layer_count):
            project.addMapLayer(QgsVectorLayer("Point?crs=EPSG:3301", f"Kiht {index}", "memory"))
        picker = LayerTreePicker()
        picker.setProject(project)

        def delete() -> None:
            picker._close_popup()
            picker.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            project.clear()

        self.addCleanup(delete)
        picker._open_popup()
        QCoreApplication.processEvents()
        return picker._popup.findChild(QTreeWidget)

    def test_a_few_layers_fit_without_scrolling(self) -> None:
        tree = self._popup_tree(3)

        self.assertEqual(tree.verticalScrollBar().maximum(), 0)
        self.assertLess(tree.height(), 3 * 32)

    def test_many_layers_stop_at_the_limit_and_scroll(self) -> None:
        tree = self._popup_tree(60)

        self.assertEqual(tree.height(), LayerTreePicker.POPUP_TREE_MAX_HEIGHT)
        self.assertGreater(tree.verticalScrollBar().maximum(), 0)


if __name__ == "__main__":
    unittest.main()
