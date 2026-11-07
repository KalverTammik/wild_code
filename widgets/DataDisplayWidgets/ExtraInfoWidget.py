import weakref
from PyQt5 import sip

from PyQt5.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QToolButton, QSizePolicy
from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from .ModuleConfig import ModuleConfigFactory


class ExtraInfoFrame(QFrame):
    _expanded_inline_frame_ref = None

    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None, handle_host=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("ExtraInfoOuterFrame")
        self._lang = lang_manager or LanguageManager()
        self._handle_host = handle_host if handle_host is not None else self
        self._detail_container = None
        self._detail_layout = None
        self._detail_widget = None
        self._detail_animation = None
        self._detail_expanded = False
        self._expand_handle = None
        self._height_timer = QTimer(self)
        self._height_timer.setSingleShot(True)
        self._height_timer.timeout.connect(self._refresh_detail_height)
        self._position_timer = QTimer(self)
        self._position_timer.setSingleShot(True)
        self._position_timer.timeout.connect(self._position_handle)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Determine module type from item_id
        self._extra_info_widget = ExtraInfoWidget(item_data, module_name, lang_manager=lang_manager)
        self._layout.addWidget(self._extra_info_widget)

        # Modules without a detail view keep an empty, hidden frame.
        if not self._extra_info_widget.should_show_detail_handle():
            self.hide()
            return

        self._init_project_detail_container()
        self._expand_handle = QToolButton(self._handle_host)
        self._expand_handle.setObjectName("ExtraInfoHandleButton")
        self._expand_handle.setAutoRaise(True)
        self._expand_handle.setFixedSize(56, 16)
        self._expand_handle.setArrowType(Qt.DownArrow)
        self._expand_handle.setCheckable(True)
        self._expand_handle.setFocusPolicy(Qt.StrongFocus)
        self._expand_handle.setCursor(Qt.PointingHandCursor)
        self._update_handle_state()
        self._expand_handle.clicked.connect(self._on_handle_clicked)
        self._expand_handle.raise_()
        if self._handle_host is not self:
            self._handle_host.installEventFilter(self)

        self._schedule_position_handle()

    @classmethod
    def _expanded_project_frame(cls):
        frame = cls._expanded_inline_frame_ref() if cls._expanded_inline_frame_ref is not None else None
        return frame if frame is not None and not sip.isdeleted(frame) else None

    @classmethod
    def _set_expanded_project_frame(cls, frame):
        cls._expanded_inline_frame_ref = weakref.ref(frame) if frame is not None else None

    def _init_project_detail_container(self):
        self._detail_container = QFrame(self)
        self._detail_container.setObjectName("ExtraInfoInlineDetail")
        self._detail_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._detail_container.setMaximumHeight(0)
        self._detail_container.setMinimumHeight(0)
        self._detail_container.installEventFilter(self)
        self._detail_container.hide()

        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 8, 0, 8)
        self._detail_layout.setSpacing(0)
        self._layout.addWidget(self._detail_container)

        self._detail_animation = QPropertyAnimation(self._detail_container, b"maximumHeight", self)
        self._detail_animation.setDuration(260)
        self._detail_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._detail_animation.finished.connect(self._on_detail_animation_finished)

    def _on_handle_clicked(self):
        if not self._detail_expanded:
            self._extra_info_widget.on_before_inline_open()
        self._toggle_project_detail()

    def _toggle_project_detail(self):
        if self._detail_container is None:
            return
        if self._detail_expanded:
            self._collapse_project_detail()
            return

        other = self._expanded_project_frame()
        if other is not None and other is not self:
            other._collapse_project_detail()

        self._set_expanded_project_frame(self)
        self._detail_expanded = True
        self._update_handle_state()
        self._ensure_project_detail_loaded()
        self._detail_container.show()
        self._run_detail_animation(self._project_detail_target_height())

    def _ensure_project_detail_loaded(self):
        if self._detail_layout is None or self._detail_widget is not None:
            return

        detail_widget = self._extra_info_widget.load_detail_widget()
        detail_widget.setParent(self._detail_container)
        detail_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._detail_layout.addWidget(detail_widget)
        self._detail_widget = detail_widget
        detail_widget.installEventFilter(self)

    def _update_handle_state(self):
        if self._expand_handle is None:
            return
        key = TranslationKeys.CARD_DETAIL_CLOSE if self._detail_expanded else TranslationKeys.CARD_DETAIL_OPEN
        text = self._lang.translate(key)
        self._expand_handle.setChecked(self._detail_expanded)
        self._expand_handle.setArrowType(Qt.UpArrow if self._detail_expanded else Qt.DownArrow)
        self._expand_handle.setToolTip(text)
        self._expand_handle.setAccessibleName(text)

    def eventFilter(self, obj, event):
        if obj is self._handle_host and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Show, QEvent.LayoutRequest):
            self._schedule_position_handle()
        if event.type() == QEvent.LayoutRequest and self._detail_expanded:
            if not self._height_timer.isActive():
                self._height_timer.start(0)
        return super().eventFilter(obj, event)

    def _refresh_detail_height(self):
        if not self._detail_expanded or self._detail_container is None:
            return
        if self._detail_animation.state() == QPropertyAnimation.Running:
            return  # The animation's finished handler picks up the new content size.
        self._detail_container.setMaximumHeight(self._project_detail_target_height())
        self.updateGeometry()
        self._schedule_position_handle()

    def _project_detail_target_height(self) -> int:
        if self._detail_layout is None:
            return 0
        return max(0, self._detail_layout.sizeHint().height())

    def _collapse_project_detail(self):
        if self._detail_container is None:
            return
        if self._expanded_project_frame() is self:
            self._set_expanded_project_frame(None)
        self._detail_expanded = False
        self._update_handle_state()
        self._run_detail_animation(0)

    def _run_detail_animation(self, end_value: int):
        if self._detail_animation is None or self._detail_container is None:
            return
        self._detail_animation.stop()
        self._detail_container.show()
        self._detail_animation.setStartValue(self._detail_container.maximumHeight())
        self._detail_animation.setEndValue(max(0, end_value))
        self._detail_animation.start()

    def _on_detail_animation_finished(self):
        if self._detail_container is None:
            return
        if self._detail_container.maximumHeight() <= 0:
            self._detail_container.hide()
            return
        self._detail_container.setMaximumHeight(self._project_detail_target_height())

    def moveEvent(self, event):  # noqa: N802 - Qt override
        super().moveEvent(event)
        self._schedule_position_handle()

    def showEvent(self, event):  # noqa: N802 - Qt override
        super().showEvent(event)
        self._schedule_position_handle()

    def _schedule_position_handle(self):
        if not self._position_timer.isActive():
            self._position_timer.start(0)

    def _position_handle(self):
        host = self._handle_host
        if host is None or self._expand_handle is None or not host.isVisible():
            return

        handle_x = max(0, (self.width() - self._expand_handle.width()) // 2)
        if host is self:
            target_x = handle_x
            target_y = max(0, self.height() - self._expand_handle.height() - 1)
        else:
            host_pos = self.mapTo(host, QPoint(0, 0))
            target_x = max(0, host_pos.x() + handle_x)
            target_y = max(0, host.height() - self._expand_handle.height() - 1)

        self._expand_handle.move(QPoint(target_x, target_y))
        self._expand_handle.raise_()

    def resizeEvent(self, event):  # noqa: N802 - Qt override
        super().resizeEvent(event)
        if (
            self._detail_container is not None
            and self._detail_container.isVisible()
            and self._detail_animation is not None
            and self._detail_animation.state() != QPropertyAnimation.Running
        ):
            self._detail_container.setMaximumHeight(self._project_detail_target_height())
        self._schedule_position_handle()

    def retheme(self) -> None:
        if self._extra_info_widget is not None:
            self._extra_info_widget.retheme()
        if self._expand_handle is not None:
            ThemeManager.apply_module_style(self._expand_handle, [QssPaths.MODULE_INFO])
        if self._detail_container is not None:
            ThemeManager.apply_module_style(self._detail_container, [QssPaths.MODULE_INFO])
        if self._detail_widget is not None:
            self._detail_widget.retheme()

class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("ExtraInfoWidget")
        self.config = ModuleConfigFactory.create_config(
            module_type=module_name,
            item_id=item_data if isinstance(item_data, dict) else {},
            lang_manager=lang_manager or LanguageManager(),
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def should_show_detail_handle(self) -> bool:
        return self.config.show_detail_handle

    def on_before_inline_open(self) -> None:
        callback = self.config.detail_open_callback
        if callable(callback):
            callback()

    def load_detail_widget(self) -> QWidget:
        return self.config.detail_loader()
