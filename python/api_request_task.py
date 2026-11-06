"""Qt transport adapter for synchronous callers; only HTTP IO moves to a thread.

Legacy actions still receive their result synchronously and keep all layer and
session access on their calling thread. Slow requests show a cancellable wait;
short requests return without flashing a dialog. Requests sent one after another
share one wait window, and its Cancel also stops those not sent yet. No
feature/UI business code is imported here.
"""
from math import ceil
from threading import Event

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QEventLoop, QThread, QTimer, Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout, QApplication

from . import api_rate_limit
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys as K


class _RequestThread(QThread):
    waiting = pyqtSignal(float, str)

    def __init__(self, send, kwargs, cancel_event, *, retry_rate_limits=True):
        super().__init__()
        self.send, self.kwargs = send, kwargs
        self.retry_rate_limits = bool(retry_rate_limits)
        self.cancel_event = cancel_event
        self.response = self.error = None

    def run(self):
        try:
            with api_rate_limit.api_request_context(
                    cancel_event=self.cancel_event, on_wait=self.waiting.emit,
                    retry_rate_limits=self.retry_rate_limits):
                self.response = api_rate_limit.PROCESS_RATE_LIMITER.send(self.send, **self.kwargs)
        except Exception as exc:
            # Preserve exception type: an uncertain write must never become a 429 retry.
            self.error = exc


class _RequestDialog(QDialog):
    open_window = None

    def __init__(self):
        parent = QApplication.activeWindow()
        # A closing wait window can still be the active one, and its children die with it.
        super().__init__(parent.parentWidget() if isinstance(parent, _RequestDialog) else parent)
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
        self.cancel_event = Event()
        self.active_requests = 0
        # A zero timer runs only once the GUI thread is back in an event loop. A flow sends
        # its requests without returning there, so its next request finds this window open.
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.setInterval(0)
        self.close_timer.timeout.connect(self.close_window)

    @classmethod
    def for_request(cls):
        window = cls.open_window
        return window if window is not None and not sip.isdeleted(window) else cls()

    def begin_request(self):
        self.active_requests += 1
        self.close_timer.stop()

    def end_request(self):
        self.active_requests -= 1
        if self.active_requests > 0:
            return
        if self.isVisible():
            self.close_timer.start()
        else:
            self.deleteLater()

    def show_window(self):
        _RequestDialog.open_window = self
        self.show()

    def close_window(self):
        if _RequestDialog.open_window is self:
            _RequestDialog.open_window = None
        self.hide()
        self.deleteLater()

    @pyqtSlot(float, str)
    def show_wait(self, seconds, reason):
        if self.cancel_event.is_set():
            return
        key = (K.API_REQUEST_RATE_WAIT if reason == 'rate_limit' else K.API_REQUEST_PACING_WAIT)
        message = (self.lang.translate(key).format(seconds=ceil(seconds)) if seconds > 0
                   else self.lang.translate(K.API_REQUEST_RUNNING))
        self.label.setText(message)

    def reject(self):
        # Let any already-sent write finish and return its real response.
        self.cancel_event.set()
        self.cancel_button.setEnabled(False)
        self.label.setText(self.lang.translate(K.API_REQUEST_CANCELLING))

    def closeEvent(self, event):
        event.ignore()
        self.reject()


def send_api_request(
    send,
    *,
    endpoint,
    authorization,
    cost,
    is_main_thread,
    retry_rate_limits=True,
):
    kwargs = dict(endpoint=endpoint, authorization=authorization, cost=cost)
    if not is_main_thread or QApplication.instance() is None:
        if not retry_rate_limits:
            with api_rate_limit.api_request_context(retry_rate_limits=False):
                return api_rate_limit.PROCESS_RATE_LIMITER.send(send, **kwargs)
        return api_rate_limit.PROCESS_RATE_LIMITER.send(send, **kwargs)

    dialog = _RequestDialog.for_request()
    dialog.begin_request()
    thread = _RequestThread(
        send,
        kwargs,
        dialog.cancel_event,
        retry_rate_limits=retry_rate_limits,
    )
    thread.waiting.connect(dialog.show_wait)
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    thread.finished.connect(loop.quit)
    thread.start()
    try:
        if not dialog.isVisible():
            timer.start(400)
            # Block reentrant clicks until either the result or the modal wait view.
            if not thread.isFinished():
                loop.exec_(QEventLoop.ExcludeUserInputEvents)
            timer.stop()
        if not thread.isFinished():
            dialog.show_window()
            loop.exec_()
    finally:
        thread.wait()
        if not sip.isdeleted(dialog):
            dialog.end_request()
    if thread.error is not None:
        raise thread.error
    return thread.response
