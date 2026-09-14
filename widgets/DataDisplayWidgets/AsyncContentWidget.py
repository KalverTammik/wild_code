"""Load plain data off the GUI thread and build its widgets on the GUI thread."""

from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.workers import FunctionWorker, start_worker
from ...Logs.python_fail_logger import PythonFailLogger
from ..theme_manager import ThemeManager


class AsyncContentWidget(QWidget):
    def __init__(self, load_data, build_widget, *, lang_manager=None, parent=None):
        super().__init__(parent)
        self._lang = lang_manager or LanguageManager()
        self._load_data = load_data
        self._build_widget = build_widget
        self._loading = False
        self._content = None
        self._worker = None
        self._thread = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._status = QLabel(self._lang.translate(TranslationKeys.LOADING), self)
        self._status.setTextFormat(Qt.PlainText)
        self._status.setWordWrap(True)
        self._layout.addWidget(self._status)
        self._retry = QPushButton(self._lang.translate(TranslationKeys.CARD_LOAD_RETRY), self)
        self._retry.setProperty("variant", "ghost")
        self._retry.setAutoDefault(False)
        self._retry.clicked.connect(self.reload)
        self._retry.hide()
        self._layout.addWidget(self._retry, 0, Qt.AlignLeft)
        self.retheme()
        QTimer.singleShot(0, self.reload)

    def reload(self):
        if self._loading or self._content is not None:
            return
        self._loading = True
        self._status.setText(self._lang.translate(TranslationKeys.LOADING))
        self._retry.hide()
        worker = FunctionWorker(self._load_data)
        # QObject receiver connections disconnect automatically if the card is removed.
        worker.finished.connect(self._loaded)
        worker.error.connect(self._failed)
        self._worker = worker
        self._thread = start_worker(worker)

    @pyqtSlot(object)
    def _loaded(self, payload):
        self._loading = False
        try:
            content = self._build_widget(payload)
            content.setParent(self)
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module="ui", event="card_detail_render_failed")
            self._failed(str(exc))
            return
        self._content = content
        self._status.hide()
        self._retry.hide()
        self._layout.addWidget(content)
        self.updateGeometry()

    @pyqtSlot(str)
    def _failed(self, _message):
        self._loading = False
        self._status.setText(self._lang.translate(TranslationKeys.CARD_DETAIL_LOAD_FAILED))
        self._retry.show()
        self.updateGeometry()

    def retheme(self):
        ThemeManager.apply_module_style(self, [QssPaths.MODULE_INFO, QssPaths.BUTTONS])
        if self._content is not None:
            callback = getattr(self._content, "retheme", None)
            if callable(callback):
                callback()
