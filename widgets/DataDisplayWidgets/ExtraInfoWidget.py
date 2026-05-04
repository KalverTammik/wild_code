import weakref

from PyQt5.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QDialog, QScrollArea, QToolButton, QPushButton, QSizePolicy
from ...constants.file_paths import QssPaths
from ...constants.button_props import ButtonVariant, ButtonSize
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...widgets.theme_manager import ThemeManager
from ...utils.url_manager import Module
from .HtmlDescriptionWidget import HtmlDescriptionWidget
from .ModuleConfig import ModuleConfigFactory


class ExtraInfoFrame(QFrame):
    _expanded_inline_frame_ref = None

    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None, handle_host=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("ExtraInfoOuterFrame")
        self._lang = lang_manager or LanguageManager()
        self._handle_host = handle_host if handle_host is not None else self
        module_key = str(module_name or "").strip().lower()
        self._uses_inline_detail = module_key in (
            Module.PROJECT.value,
            Module.CONTRACT.value,
            Module.COORDINATION.value,
            Module.EASEMENT.value,
            Module.TASK.value,
            Module.WORKS.value,
            Module.ASBUILT.value,
        )
        self._detail_container = None
        self._detail_layout = None
        self._detail_widget = None
        self._detail_animation = None
        self._position_timer = QTimer(self)
        self._position_timer.setSingleShot(True)
        self._position_timer.timeout.connect(self._position_handle)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Determine module type from item_id
        self._extra_info_widget = ExtraInfoWidget(item_data, module_name, lang_manager=lang_manager)
        self._layout.addWidget(self._extra_info_widget)

        if self._uses_inline_detail:
            self._init_project_detail_container()

        if not self._extra_info_widget.should_show_detail_handle():
            self.hide()
            return

        self._expand_handle = QToolButton(self._handle_host)
        self._expand_handle.setObjectName("ExtraInfoHandleButton")
        self._expand_handle.setAutoRaise(True)
        self._expand_handle.setFixedSize(42, 12)
        self._expand_handle.setText("")
        self._expand_handle.setCursor(Qt.PointingHandCursor)
        self._expand_handle.setToolTip(self._extra_info_widget._detail_button_tooltip())
        self._expand_handle.clicked.connect(self._on_handle_clicked)
        self._expand_handle.raise_()

        self._schedule_position_handle()

    @classmethod
    def _expanded_project_frame(cls):
        return cls._expanded_inline_frame_ref() if cls._expanded_inline_frame_ref is not None else None

    @classmethod
    def _set_expanded_project_frame(cls, frame):
        cls._expanded_inline_frame_ref = weakref.ref(frame) if frame is not None else None

    def _init_project_detail_container(self):
        self._detail_container = QFrame(self)
        self._detail_container.setObjectName("ExtraInfoInlineDetail")
        self._detail_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._detail_container.setMaximumHeight(0)
        self._detail_container.setMinimumHeight(0)
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
        if self._uses_inline_detail:
            self._extra_info_widget.on_before_inline_open()
            self._toggle_project_detail()
            return
        self._extra_info_widget._show_detailed_overview()

    def _toggle_project_detail(self):
        if self._detail_container is None:
            return
        if self._detail_container.isVisible() and self._detail_container.maximumHeight() > 0:
            self._collapse_project_detail()
            return

        other = self._expanded_project_frame()
        if other is not None and other is not self:
            other._collapse_project_detail()

        self._set_expanded_project_frame(self)
        self._ensure_project_detail_loaded()
        self._detail_container.show()
        self._run_detail_animation(self._project_detail_target_height())

    def _ensure_project_detail_loaded(self):
        if self._detail_layout is None or self._detail_widget is not None:
            return

        loaded = self._extra_info_widget._load_detailed_content()
        if isinstance(loaded, QWidget):
            detail_widget = loaded
        else:
            detail_widget = HtmlDescriptionWidget(str(loaded or ""), self._detail_container, inline=True)

        detail_widget.setParent(self._detail_container)
        detail_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._detail_layout.addWidget(detail_widget)
        self._detail_widget = detail_widget

    def _project_detail_target_height(self) -> int:
        if self._detail_layout is None:
            return 0
        return max(0, self._detail_layout.sizeHint().height())

    def _collapse_project_detail(self):
        if self._detail_container is None:
            return
        if self._expanded_project_frame() is self:
            self._set_expanded_project_frame(None)
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
            detail_retheme = getattr(self._detail_widget, "retheme", None)
            if callable(detail_retheme):
                detail_retheme()

class ExtraInfoWidget(QWidget):
    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("ExtraInfoWidget")
        self.item_data = item_data if isinstance(item_data, dict) else {}
        self.module_name = module_name
        self._lang = lang_manager or LanguageManager()
        self.config = ModuleConfigFactory.create_config(
            module_type=self.module_name,
            item_id=self.item_data,
            lang_manager=self._lang,
        )
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        module_key = str(self.module_name or "").strip().lower()
        uses_inline_detail = module_key in (
            Module.PROJECT.value,
            Module.CONTRACT.value,
            Module.COORDINATION.value,
            Module.EASEMENT.value,
            Module.TASK.value,
            Module.WORKS.value,
            Module.ASBUILT.value,
        )

        if not uses_inline_detail and self.config.title:
            title = QLabel(self.config.title)
            title.setObjectName("ExtraInfoTitle")
            main_layout.addWidget(title)

        if self.config.summary_text and not uses_inline_detail:
            summary_label = QLabel(self.config.summary_text)
            summary_label.setObjectName("SetupCardDescription")
            summary_label.setWordWrap(True)
            main_layout.addWidget(summary_label)

        if uses_inline_detail:
            ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])
            return

        # Dynamic column layout based on configuration
        if self.config.columns:
            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(12)

            for column_config in self.config.columns:
                column = self._create_status_columns(
                    column_config['title'],
                    column_config['color'],
                    column_config['activities']
                )
                columns_layout.addWidget(column)

            main_layout.addLayout(columns_layout)
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO])

    def _detail_button_tooltip(self) -> str:
        base = self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_EXTRAINFO_TOOLTIP)
        module_key = str(self.module_name or "").strip().lower()
        uses_inline_detail = module_key in (
            Module.PROJECT.value,
            Module.CONTRACT.value,
            Module.COORDINATION.value,
            Module.EASEMENT.value,
            Module.TASK.value,
            Module.WORKS.value,
            Module.ASBUILT.value,
        )
        if not uses_inline_detail:
            return base

        parts = [str(self.config.title or "").strip(), str(self.config.summary_text or "").strip()]
        parts = [part for part in parts if part]
        return "\n".join(parts) if parts else base

    def has_detail_content(self) -> bool:
        if self.config.detailed_widget is not None:
            return True
        if isinstance(self.config.detailed_content, str) and self.config.detailed_content.strip():
            return True
        if callable(self.config.detail_loader):
            loaded = self.config.load_detailed_content()
            return bool(loaded and str(loaded).strip())
        return False

    def should_show_detail_handle(self) -> bool:
        if self.config.show_detail_handle:
            return True
        return self.has_detail_content()

    def on_before_inline_open(self) -> None:
        callback = getattr(self.config, "detail_open_callback", None)
        if callable(callback):
            callback()

    def _create_status_columns(self, title, color, activities):
        """Create a status column with title and activity list."""
        column_widget = QWidget()
        column_widget.setObjectName("ExtraInfoColumn")
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(2)  # Reduced spacing between header and list

        # Column title - removed background color, kept text color
        title_label = QLabel(title)
        title_label.setObjectName("ExtraInfoColumnTitle")
        title_label.setStyleSheet(f"color: {color};")
        title_label.setAlignment(Qt.AlignCenter)
        column_layout.addWidget(title_label)

        # Activity list
        list_widget = QListWidget()
        list_widget.setObjectName("ExtraInfoList")
        list_widget.setFixedHeight(120)  # Set fixed height to ensure at least 3 items are visible

        # Add activities
        for activity_name, icon in activities:
            item = QListWidgetItem(f"{icon} {activity_name}")
            list_widget.addItem(item)

        column_layout.addWidget(list_widget)
        return column_widget

    def _load_detailed_content(self):
        return self.config.load_detailed_content() or (
            f"<h3>{self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_OVERVIEW_TITLE)}</h3>"
        )

    def _show_detailed_overview(self):
        """Show detailed activity overview in a dialog window."""
        dialog = QDialog(self)
        dialog.setObjectName("ExtraInfoDialog")
        is_project = str(self.module_name or "").strip().lower() == Module.PROJECT.value
        title_suffix = self._lang.translate(
            TranslationKeys.DATA_DISPLAY_WIDGETS_DETAIL_TITLE_SUFFIX
        )
        dialog.setWindowTitle(f"{self.config.title} - {title_suffix}")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Title
        if not is_project:
            title = QLabel(self.config.title)
            title.setObjectName("ExtraInfoDialogTitle")
            layout.addWidget(title)

        # Scrollable text area with module-specific content
        scroll_area = QScrollArea()
        scroll_area.setObjectName("ExtraInfoScroll")
        scroll_area.setWidgetResizable(True)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Use module-specific content
        content = self._load_detailed_content()

        if isinstance(content, QWidget):
            content.setParent(text_widget)
            text_layout.addWidget(content)
            preferred_width = getattr(content, "preferred_dialog_width", None)
            if callable(preferred_width):
                try:
                    target_width = max(600, int(preferred_width()) + 72)
                    dialog.resize(target_width, dialog.height())
                except Exception:
                    pass
        else:
            text_layout.addWidget(HtmlDescriptionWidget(str(content or ""), text_widget, inline=False))

        scroll_area.setWidget(text_widget)
        layout.addWidget(scroll_area)

        # Close button
        close_label = self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_CLOSE)
        close_btn = QPushButton(close_label)
        close_btn.setObjectName("ConfirmButton")
        close_btn.setProperty("variant", ButtonVariant.SUCCESS)
        close_btn.setProperty("btnSize", ButtonSize.MEDIUM)
        # Prevent button from being triggered by Return key
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        ThemeManager.apply_app_style(dialog, [QssPaths.MODULE_INFO, QssPaths.BUTTONS])

        dialog.exec_()
