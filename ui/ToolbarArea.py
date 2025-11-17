"""Simple toolbar widget hosting left/right slots with module theme support."""

from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QWidget,
)

from ..widgets.theme_manager import ThemeManager, styleExtras, ThemeShadowColors, AlphaLevel
from ..constants.file_paths import QssPaths


class ModuleToolbarArea(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarArea")

        # Main horizontal layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 4, 2, 4)
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
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])
        styleExtras.apply_chip_shadow(
            self,
            blur_radius=5,
            x_offset=1,
            y_offset=1,
            color=ThemeShadowColors.BLUE,
            alpha_level=AlphaLevel.MEDIUM,
        )

    def add_left(self, widget: QWidget) -> None:
        if widget is None:
            return

        # If no spacer/stretch has been added yet, add the widget then append a stretch
        # so that remaining free space is absorbed to the right and widgets stay left-aligned.
        if self._left_has_spacer is False:
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
        self._clear_layout(self._left_layout)

    def clear_right(self) -> None:
        self._clear_layout(self._right_layout)

    def retheme(self) -> None:
        """Re-apply toolbar QSS."""
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])

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
