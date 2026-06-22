"""Simple toolbar widget hosting left/right slots with module theme support."""

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLayout,
    QSizePolicy,
    QSpacerItem,
    QLabel,
)

from ..widgets.theme_manager import ThemeManager, styleExtras, ThemeShadowColors, AlphaLevel
from ..constants.file_paths import QssPaths
from ..Logs.python_fail_logger import PythonFailLogger


class ModuleToolbarArea(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarArea")

        # Main grid layout for deterministic positioning of sections
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setHorizontalSpacing(0)
        self._layout.setVerticalSpacing(0)

        
        self._left = QWidget(self)
        self._left.setObjectName("ToolbarLeft")
        self._left.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        # Left side now uses a grid so widgets can wrap across multiple rows.
        self._left_layout = QGridLayout(self._left)
        self._left_layout.setContentsMargins(2, 2, 2, 2)
        self._left_layout.setHorizontalSpacing(0)
        self._left_layout.setVerticalSpacing(0)
        self._left_widgets: List[QWidget] = []
        self._left_preferred_width = 240  # px per widget before wrapping
        self._left_max_columns = 2
        self._refresh_widget: QWidget | None = None

        # Right slot container
        self._right = QWidget(self)
        self._right.setObjectName("ToolbarRight")
        self._right_layout = QHBoxLayout(self._right)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(2)

        # Compose
        self._layout.addWidget(self._left, 0, 0, Qt.AlignTop)
        self._layout.addWidget(self._right, 0, 2, Qt.AlignTop)

        # Ensure right area absorbs remaining width
        self._layout.setColumnStretch(0, 0)
        self._layout.setColumnStretch(1, 1)
        self._layout.setColumnStretch(2, 0)


        # Apply toolbar + centralized combo styling (includes ComboBox.qss)

        self.retheme()
        styleExtras.apply_chip_shadow(
            self._left,
            blur_radius=10,
            x_offset=1,
            y_offset=2,
            color=ThemeShadowColors.BLUE,
            alpha_level=AlphaLevel.MEDIUM,
        )

    def add_left(self, widget: QWidget) -> None:
        if widget is None:
            return
        wrapped = self._wrap_filter_widget(widget)
        self._left_widgets.append(wrapped)
        self._reflow_left_widgets()

    def add_right(self, widget: QWidget) -> None:
        if widget is not None:
            self._right_layout.addWidget(widget)

    def set_refresh_widget(self, widget: QWidget) -> None:
        """Place filter actions inside the left filter grid."""
        self.clear_refresh()
        if widget is not None:
            widget.setParent(self._left)
            widget.setObjectName(widget.objectName() or "FilterActionsContainer")
            self._refresh_widget = widget
            self._reflow_left_widgets()

    def clear_left(self) -> None:
        for widget in self._left_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self._left_widgets.clear()
        if self._refresh_widget is not None:
            self._refresh_widget.setParent(None)
            self._refresh_widget.deleteLater()
        self._refresh_widget = None
        self._purge_left_grid()

    def clear_refresh(self) -> None:
        widget = self._refresh_widget
        if widget is None:
            return
        self._refresh_widget = None
        widget.setParent(None)
        widget.deleteLater()
        self._reflow_left_widgets()

    def clear_right(self) -> None:
        self._clear_layout(self._right_layout)

    def retheme(self) -> None:
        """Re-apply toolbar QSS."""
        ThemeManager.apply_module_style(
            self,
            [QssPaths.MAIN, QssPaths.BUTTONS, QssPaths.COMBOBOX, QssPaths.MODULE_TOOLBAR],
        )

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        try:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="toolbar_clear_layout_failed",
            )

    def resizeEvent(self, event):  # noqa: D401
        super().resizeEvent(event)
        self._reflow_left_widgets()

    def set_left_max_columns(self, count: int) -> None:
        """Optionally allow plugins to override how many widgets fit per row."""
        if count and count > 0:
            self._left_max_columns = count
            self._reflow_left_widgets()

    def set_left_preferred_width(self, width: int) -> None:
        """Override the approximate width used to estimate wrap columns."""
        if width and width > 0:
            self._left_preferred_width = width
            self._reflow_left_widgets()

    def _reflow_left_widgets(self) -> None:
        """Place left widgets inside the grid, wrapping rows as needed."""
        self._purge_left_grid()

        if not self._left_widgets and self._refresh_widget is None:
            return

        columns = self._calculate_left_columns()
        row = col = 0
        for widget in self._left_widgets:
            self._left_layout.addWidget(widget, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        if self._refresh_widget is not None:
            action_col = columns if self._left_widgets else 0
            self._left_layout.addWidget(self._refresh_widget, 0, action_col, 1, 1, Qt.AlignTop)

        # Extra stretch column absorbs leftover horizontal room so widgets stay left-aligned.
        extra_col = columns + (1 if self._refresh_widget is not None else 0)
        for index in range(extra_col + 1):
            self._left_layout.setColumnStretch(index, 0)
        self._left_layout.setColumnStretch(extra_col, 1)

    def _purge_left_grid(self) -> None:
        while self._left_layout.count():
            item = self._left_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self._left)

    def _calculate_left_columns(self) -> int:
        available = max(1, self._left.width())
        target_width = max(120, self._left_preferred_width)
        estimated = max(1, available // target_width)
        return max(1, min(self._left_max_columns, estimated))

    def _wrap_filter_widget(self, widget: QWidget) -> QWidget:
        """Wrap filters with a title label when they expose filter_title."""
        title = getattr(widget, "filter_title", None)
        if not title:
            widget.setParent(self._left)
            return widget

        container = QWidget(self._left)
        container.setObjectName("FilterWidgetContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)

        label = QLabel(str(title), container)
        label.setObjectName("FilterTitleLabel")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setProperty("role", "filter-title")
        layout.addWidget(label)

        widget.setParent(container)
        layout.addWidget(widget)
        return container
