from __future__ import annotations

from PyQt5.QtWidgets import QWidget

from ..Logs.python_fail_logger import PythonFailLogger
from ..utils.url_manager import Module


class ResponsiveWatchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._responsive_callback = None
        self._responsive_source = "watch"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._responsive_callback:
            self._responsive_callback(source=f"{self._responsive_source}-resize")

    def showEvent(self, event):
        super().showEvent(event)
        if self._responsive_callback:
            self._responsive_callback(source=f"{self._responsive_source}-show")


class _ResponsiveCornerContainer(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller

    def resizeEvent(self, event):
        self._controller._update_layout_mode(source="resize")
        super().resizeEvent(event)

    def showEvent(self, event):
        self._controller._update_layout_mode(source="show")
        super().showEvent(event)


class ResponsiveCornerWidget:
    HYSTERESIS_PX = 20
    _GLOBAL_WIDE_LEFT_HINT = 0
    _GLOBAL_WIDE_RIGHT_HINT = 0

    def __init__(
        self,
        dates_widget,
        actions_widget,
        members_view,
        *,
        content_widget,
        left_column,
        right_column,
        parent=None,
    ):
        from PyQt5.QtWidgets import QGridLayout

        self.widget = _ResponsiveCornerContainer(self, parent)
        self.widget.setObjectName("ResponsiveCornerWidget")

        self.dates_widget = dates_widget
        self.actions_widget = actions_widget
        self.members_view = members_view
        self.content_widget = content_widget
        self.left_column = left_column
        self.right_column = right_column
        self.column_spacing = 6
        self._compact = None
        self._wide_left_hint = 0
        self.layout = QGridLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._apply_layout(False)
        self._wide_right_hint = self.widget.sizeHint().width()
        ResponsiveCornerWidget._GLOBAL_WIDE_RIGHT_HINT = max(
            ResponsiveCornerWidget._GLOBAL_WIDE_RIGHT_HINT,
            self._wide_right_hint,
        )

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                self.layout.removeWidget(widget)

    def _apply_layout(self, compact):
        from PyQt5.QtCore import Qt

        self._clear_layout()
        self.layout.setHorizontalSpacing(2 if compact else 4)
        self.layout.setVerticalSpacing(2 if compact else 1)
        self.dates_widget.set_compact(compact)
        self.actions_widget.set_compact(compact)

        if compact:
            if self.members_view:
                self.layout.addWidget(self.members_view, 0, 0, 1, 2, Qt.AlignHCenter | Qt.AlignTop)
            self.layout.addWidget(self.dates_widget, 1, 0, 1, 2, Qt.AlignHCenter | Qt.AlignTop)
            self.layout.addWidget(self.actions_widget, 2, 0, 1, 2, Qt.AlignHCenter | Qt.AlignTop)
        else:
            self.layout.addWidget(self.dates_widget, 0, 0, Qt.AlignRight | Qt.AlignTop)
            self.layout.addWidget(self.actions_widget, 1, 0, Qt.AlignRight | Qt.AlignTop)
            if self.members_view:
                self.layout.addWidget(self.members_view, 0, 1, 2, 1, Qt.AlignRight | Qt.AlignTop)

        self.widget.updateGeometry()

    def _log_metrics(self, *, source, compact):
        left_width = self.left_column.width()
        left_hint = self.left_column.sizeHint().width()
        left_deficit = left_hint - left_width
        content_width = self.content_widget.width()
        content_hint = self.content_widget.sizeHint().width()
        wide_left_hint = ResponsiveCornerWidget._GLOBAL_WIDE_LEFT_HINT
        wide_right_hint = ResponsiveCornerWidget._GLOBAL_WIDE_RIGHT_HINT
        wide_threshold = wide_left_hint + wide_right_hint + self.column_spacing
        PythonFailLogger.log(
            "responsive_corner_metrics",
            module=PythonFailLogger.LOG_MODULE_UI,
            extra={
                "source": source,
                "compact": compact,
                "wide_threshold": wide_threshold,
                "wide_left_hint": wide_left_hint,
                "wide_right_hint": wide_right_hint,
                "hysteresis": self.HYSTERESIS_PX,
                "corner_width": self.widget.width(),
                "corner_hint": self.widget.sizeHint().width(),
                "right_width": self.right_column.width(),
                "right_hint": self.right_column.sizeHint().width(),
                "left_width": left_width,
                "left_hint": left_hint,
                "left_deficit": left_deficit,
                "content_width": content_width,
                "content_hint": content_hint,
                "dates_width": self.dates_widget.width(),
                "dates_hint": self.dates_widget.sizeHint().width(),
                "actions_width": self.actions_widget.width(),
                "actions_hint": self.actions_widget.sizeHint().width(),
                "members_width": self.members_view.width() if self.members_view else -1,
                "members_hint": self.members_view.sizeHint().width() if self.members_view else -1,
            },
        )

    def _update_layout_mode(self, *, source="unknown"):
        content_width = self.content_widget.width()
        self._wide_left_hint = max(self._wide_left_hint, self.left_column.sizeHint().width())
        ResponsiveCornerWidget._GLOBAL_WIDE_LEFT_HINT = max(
            ResponsiveCornerWidget._GLOBAL_WIDE_LEFT_HINT,
            self._wide_left_hint,
        )
        wide_threshold = (
            ResponsiveCornerWidget._GLOBAL_WIDE_LEFT_HINT
            + ResponsiveCornerWidget._GLOBAL_WIDE_RIGHT_HINT
            + self.column_spacing
        )

        if content_width <= 0:
            compact = False
        elif self._compact:
            compact = content_width < (wide_threshold + self.HYSTERESIS_PX)
        else:
            compact = content_width <= wide_threshold
        self._log_metrics(source=source, compact=compact)
        if compact == self._compact:
            return
        self._compact = compact
        self._apply_layout(compact)


class ModuleCardFactory:
    @staticmethod
    def create_item_card(item, module_name=None, lang_manager=None):
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QSizePolicy, QWidget

        from ..widgets.DataDisplayWidgets.ContactsWidget import ContactsWidget
        from ..widgets.DataDisplayWidgets.MainStatusWidget import MainStatusWidget
        from ..widgets.DataDisplayWidgets.MembersView import MembersView
        from ..widgets.DataDisplayWidgets.ExtraInfoWidget import ExtraInfoFrame
        from ..widgets.DataDisplayWidgets.EasementPropertiesWidget import EasementPropertiesWidget
        from ..widgets.DataDisplayWidgets.InfoCardHeader import InfocardHeaderFrame
        from ..widgets.DataDisplayWidgets.DatesWidget import DatesWidget
        from ..widgets.DataDisplayWidgets.ModuleConnectionActions import ModuleConnectionActions
        from ..widgets.theme_manager import IntensityLevels, styleExtras, ThemeShadowColors
        from ..widgets.theme_manager import ThemeManager
        from ..constants.file_paths import QssPaths

        item_data = dict(item or {})
        card = QFrame()
        card.setObjectName("ModuleInfoCard")
        shadow_color = ThemeShadowColors.GRAY
        styleExtras.apply_chip_shadow(
            element=card,
            color=shadow_color,
            blur_radius=15,
            x_offset=1,
            y_offset=2,
            alpha_level=IntensityLevels.EXTRA_HIGH,
        )

        main = QHBoxLayout(card)
        main.setContentsMargins(0, 10, 10, 10)
        main.setSpacing(8)

        content = QFrame()
        content.setObjectName("CardContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        content_columns = QHBoxLayout()
        content_columns.setContentsMargins(0, 0, 0, 0)
        content_columns.setSpacing(6)

        left_column = ResponsiveWatchWidget(content)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(6)

        right_column = QWidget(content)
        right_column.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 1, 0, 0)
        right_column_layout.setSpacing(2)

        item_id = item_data.get("id")
        if item_id is None:
            raise ValueError("Module feed items must include an 'id' field")

        header_frame = InfocardHeaderFrame(item_data, module_name=module_name, lang_manager=lang_manager)
        left_column_layout.addWidget(header_frame, 0, Qt.AlignTop)

        dates_widget = DatesWidget(
            item_data,
            parent=card,
            lang_manager=lang_manager,
        )

        actions_widget = ModuleConnectionActions(
            module_name,
            item_id,
            item_data,
            lang_manager=lang_manager,
        )

        members_view = MembersView(item_data)

        corner_widget_controller = ResponsiveCornerWidget(
            dates_widget,
            actions_widget,
            members_view,
            content_widget=content,
            left_column=left_column,
            right_column=right_column,
            parent=right_column,
        )
        corner_widget = corner_widget_controller.widget
        corner_widget._responsive_controller = corner_widget_controller
        left_column._responsive_source = "left-column"

        right_column_layout.addWidget(corner_widget, 0, Qt.AlignRight | Qt.AlignTop)
        right_column_layout.addStretch(1)

        content_columns.addWidget(left_column, 1)
        content_columns.addWidget(right_column, 0, Qt.AlignTop)
        cl.addLayout(content_columns)

        contacts_widget = ContactsWidget(item_data, parent=content)
        if not contacts_widget.isHidden():
            left_column_layout.addWidget(contacts_widget)

        def _handle_left_column_responsive_update(*, source="unknown"):
            corner_widget_controller._update_layout_mode(source=source)
            if not contacts_widget.isHidden():
                contacts_widget.handle_responsive_update(source=source)

        left_column._responsive_callback = _handle_left_column_responsive_update

        show_extra_info = module_name not in ()
        if show_extra_info:
            cl.addWidget(ExtraInfoFrame(item_data, module_name, lang_manager=lang_manager, handle_host=card))

        main.addWidget(
            MainStatusWidget(
                item_data,
                module_name=module_name,
                parent=card,
                lang_manager=lang_manager,
            ),
            0,
        )

        main.addWidget(content, 1)

        ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
        return card

    @staticmethod
    def create_card(item, lang_manager):
        from ..module_manager import ModuleManager

        module_manager = ModuleManager()
        module_name = module_manager.getActiveModuleName()
        return ModuleCardFactory.create_item_card(
            item,
            module_name=module_name,
            lang_manager=lang_manager,
        )
