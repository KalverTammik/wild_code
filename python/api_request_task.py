"""Qt transport adapter for synchronous callers; only HTTP IO moves to a thread.

Legacy actions still receive their result synchronously and keep all layer and
session access on their calling thread. Slow requests show a cancellable wait;
short requests return without flashing a dialog. No feature/UI business code
is imported here.
"""
from math import ceil
from threading import Event

from qgis.PyQt.QtCore import QEventLoop, QThread, QTimer, Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout, QApplication

from . import api_rate_limit
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys as K


class _RequestThread(QThread):
    waiting = pyqtSignal(float, str)

    def __init__(self, send, kwargs, parent):
        super().__init__(parent)
        self.send, self.kwargs = send, kwargs
        self.cancel_event = Event()
        self.response = self.error = None

    def run(self):
        try:
            with api_rate_limit.api_request_context(
                    cancel_event=self.cancel_event, on_wait=self.waiting.emit):
                self.response = api_rate_limit.PROCESS_RATE_LIMITER.send(self.send, **self.kwargs)
        except Exception as exc:
            # Preserve exception type: an uncertain write must never become a 429 retry.
            self.error = exc


class _RequestDialog(QDialog):
    def __init__(self):
        super().__init__(QApplication.activeWindow())
        self.lang = LanguageManager()
        self.setWindowTitle(self.lang.translate(K.API_REQUEST_TITLE))
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(380)
        self.label = QLabel(self.lang.translate(K.API_REQUEST_RUNNING), self)
        self.label.setWordWrap(True)
        bar = QProgressBar(self)
        bar.setRange(0, 0)
        self.cancel_button = QPushButton(self.lang.translate(K.CANCEL_BUTTON), self)
        self.cancel_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(bar)
        layout.addWidget(self.cancel_button)
        self.thread = None

    @pyqtSlot(float, str)
    def show_wait(self, seconds, reason):
        if self.thread.cancel_event.is_set():
            return
        key = (K.API_REQUEST_RATE_WAIT if reason == 'rate_limit' else K.API_REQUEST_PACING_WAIT)
        message = (self.lang.translate(key).format(seconds=ceil(seconds)) if seconds > 0
                   else self.lang.translate(K.API_REQUEST_RUNNING))
        self.label.setText(message)

    def reject(self):
        # Let any already-sent write finish and return its real response.
        self.thread.cancel_event.set()
        self.cancel_button.setEnabled(False)
        self.label.setText(self.lang.translate(K.API_REQUEST_CANCELLING))

    def closeEvent(self, event):
        event.ignore()
        self.reject()


def send_api_request(send, *, endpoint, authorization, cost, is_main_thread):
    kwargs = dict(endpoint=endpoint, authorization=authorization, cost=cost)
    if not is_main_thread or QApplication.instance() is None:
        return api_rate_limit.PROCESS_RATE_LIMITER.send(send, **kwargs)

    dialog = _RequestDialog()
    thread = _RequestThread(send, kwargs, dialog)
    dialog.thread = thread
    thread.waiting.connect(dialog.show_wait)
    thread.finished.connect(dialog.accept)
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    thread.finished.connect(loop.quit)
    thread.start()
    timer.start(400)
    try:
        # Block reentrant clicks until either the result or the modal wait view.
        if not thread.isFinished():
            loop.exec_(QEventLoop.ExcludeUserInputEvents)
        timer.stop()
        if not thread.isFinished():
            dialog.exec_()
        thread.wait()
        if thread.error is not None:
            raise thread.error
        return thread.response
    finally:
        dialog.deleteLater()
