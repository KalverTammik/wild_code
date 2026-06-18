from __future__ import annotations

from PyQt5.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, QSize, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLineEdit, QPushButton, QWidget
from PyQt5.QtGui import QColor
from qgis.utils import iface

from ..constants.button_props import ButtonSize, ButtonVariant
from ..constants.module_icons import IconNames
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.search.UnifiedSearchController import UnifiedSearchController
from ..widgets.SearchResultsWidget import SearchResultsWidget
from ..widgets.theme_manager import ThemeManager


class MapCanvasSearchBar(QWidget):
    """Unified-search overlay fixed to the top-right of the QGIS map canvas."""

    resultClicked = pyqtSignal(str, str, str)
    _active_instance = None

    TARGET_MARGIN = QPoint(18, 18)
    START_Y = -58
    SIZE = (300, 46)

    def __init__(self, *, parent=None) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        parent = parent or canvas
        super().__init__(parent)
        self._canvas = canvas
        self._animation = None
        self._active_token = None
        self._activated = True
        self._lang = LanguageManager()

        self.setObjectName("MapCanvasSearchBar")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if parent is None:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setFixedSize(*self.SIZE)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)

        self.search_controller = UnifiedSearchController(self)
        self.search_controller.searchSucceeded.connect(self._on_search_success)
        self.search_controller.searchFailed.connect(self._on_search_error)
        self.search_controller.searchStatus.connect(self._on_search_status)
        self._search_results = None
        self.resultClicked.connect(self._open_result_in_plugin)

        self._build_ui()
        self._position_at_start()
        if self._canvas is not None:
            self._canvas.installEventFilter(self)

    @property
    def search_results_widget(self):
        if self._search_results is None:
            self._search_results = SearchResultsWidget(self)
            self._search_results.set_glass_mode(True)
            self._search_results.setVisible(False)
            self._search_results.resultClicked.connect(self.resultClicked.emit)
            self._search_results.refreshRequested.connect(self._on_refresh_requested)
        return self._search_results

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        frame = QFrame(self)
        frame.setObjectName("MapCanvasSearchBarFrame")
        frame.setStyleSheet(
            """
            QFrame#MapCanvasSearchBarFrame {
                background: rgba(248, 252, 255, 164);
                border: 1px solid rgba(30, 126, 180, 120);
                border-radius: 8px;
            }
            QLineEdit#MapCanvasSearchEdit {
                height: 28px;
                padding: 0 9px;
                border-radius: 6px;
                border: 1px solid rgba(22, 111, 151, 95);
                background: rgba(255, 255, 255, 136);
                color: #12394a;
                selection-background-color: rgba(22, 111, 151, 90);
            }
            QLineEdit#MapCanvasSearchEdit:focus {
                background: rgba(255, 255, 255, 210);
                border-color: rgba(22, 111, 151, 180);
            }
            QPushButton#MapCanvasSearchButton {
                border-radius: 6px;
                border: 1px solid rgba(22, 111, 151, 90);
                background: rgba(255, 255, 255, 118);
            }
            QPushButton#MapCanvasSearchButton:hover {
                background: rgba(255, 255, 255, 190);
                border-color: rgba(22, 111, 151, 170);
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 60, 80, 78))
        frame.setGraphicsEffect(shadow)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        self.search_edit = QLineEdit(frame)
        self.search_edit.setObjectName("MapCanvasSearchEdit")
        self.search_edit.setPlaceholderText(self._lang.translate(TranslationKeys.SEARCH_PLACEHOLDER))
        self.search_edit.setToolTip(self._lang.translate(TranslationKeys.SEARCH_TOOLTIP))
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        self.search_edit.returnPressed.connect(self._perform_search)
        layout.addWidget(self.search_edit, 1)

        button = QPushButton(frame)
        button.setObjectName("MapCanvasSearchButton")
        button.setProperty("variant", ButtonVariant.ICON)
        button.setProperty("btnSize", ButtonSize.SMALL)
        button.setIcon(ThemeManager.get_qicon(IconNames.ICON_HELP))
        button.setIconSize(QSize(16, 16))
        button.clicked.connect(self._perform_search)
        layout.addWidget(button, 0)

        root.addWidget(frame)

    def _target_pos(self) -> QPoint:
        if self._canvas is not None:
            return QPoint(
                max(0, self._canvas.width() - self.width() - self.TARGET_MARGIN.x()),
                self.TARGET_MARGIN.y(),
            )
        screen = self.screen()
        if screen is None:
            return self.TARGET_MARGIN
        geometry = screen.availableGeometry()
        return QPoint(
            geometry.right() - self.width() - self.TARGET_MARGIN.x(),
            geometry.top() + self.TARGET_MARGIN.y(),
        )

    def _position_at_start(self) -> None:
        target = self._target_pos()
        self.move(target.x(), self.START_Y)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._canvas and event.type() in (QEvent.Resize, QEvent.Show):
            if self.isVisible():
                self.move(self._target_pos())
            else:
                self._position_at_start()
        return super().eventFilter(watched, event)

    def is_token_active(self, token) -> bool:
        if token is None:
            return True
        return bool(self._activated) and token == self._active_token

    def _on_search_text_changed(self, text: str) -> None:
        if len(str(text or "").strip()) < 3:
            self.search_results_widget.hide_results()
            self._search_timer.stop()
            self.search_controller.invalidate()
            return
        self._search_timer.start(500)

    def _perform_search(self) -> None:
        query = self.search_edit.text().strip()
        if len(query) < 3:
            self.search_results_widget.hide_results()
            return
        self.search_controller.search(query)

    def _on_refresh_requested(self) -> None:
        if len(self.search_edit.text().strip()) >= 3:
            self._perform_search()

    def _on_search_status(self, message: str) -> None:
        self.search_results_widget.show_status_message(message, self.search_edit)

    def _on_search_success(self, search_data) -> None:
        if search_data and any(module.get("total", 0) > 0 for module in search_data):
            self.search_results_widget.show_results(search_data, self.search_edit)
        else:
            self.search_results_widget.show_no_results(self.search_edit.text().strip(), self.search_edit)

    def _on_search_error(self, message: str) -> None:
        self.search_results_widget.show_status_message(message or "Otsing ebaõnnestus", self.search_edit, is_error=True)

    def _open_result_in_plugin(self, module: str, item_id: str, title: str) -> None:
        try:
            from ..dialog import PluginDialog
            from ..utils.search.searchHelpers import SearchUIController

            SearchUIController.handle_search_result(PluginDialog.get_instance(), module, item_id, title)
        except Exception:
            pass

    def show_animated(self) -> None:
        self._position_at_start()
        self.show()
        self.raise_()

        self._animation = QPropertyAnimation(self, b"pos", self)
        self._animation.setDuration(240)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self._target_pos())
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    @classmethod
    def show_for_session(cls, *, result_handler=None) -> None:
        if cls._active_instance is not None:
            try:
                if callable(result_handler):
                    cls._active_instance.resultClicked.connect(result_handler)
                cls._active_instance.raise_()
                cls._active_instance.move(cls._active_instance._target_pos())
                return
            except Exception:
                cls._active_instance = None

        bar = cls()
        if callable(result_handler):
            bar.resultClicked.connect(result_handler)
        cls._active_instance = bar
        bar.destroyed.connect(lambda *_: setattr(cls, "_active_instance", None))
        bar.show_animated()

    @classmethod
    def close_active(cls) -> None:
        if cls._active_instance is None:
            return
        try:
            cls._active_instance.search_results_widget.hide_results()
            cls._active_instance.close()
        except Exception:
            pass
        cls._active_instance = None
