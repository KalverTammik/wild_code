# Centralized auto-fill helper for scrollable feed widgets
from PyQt5.QtCore import QTimer

def autofill_scroll_area(ui, load_next_batch, scroll_area, max_auto_batches=1, log_func=None):
    """
    Loads up to max_auto_batches more if the area isn't scrollable yet.
    Calls the UI's loader to respect guards/revision and theme hooks.
    """
    batches_loaded = [0]

    def _maybe_autofill():
        fl = getattr(ui, 'feed_logic', None)
        if not fl:
            return
        bar = scroll_area.verticalScrollBar()

        if (bar.maximum() <= 0 and
            batches_loaded[0] < max_auto_batches and
            fl.has_more and
            not fl.is_loading):
            if log_func:
                log_func(f"[AutoFillHelper] Auto-filling batch {batches_loaded[0] + 1}/{max_auto_batches}")
            load_next_batch()
            batches_loaded[0] += 1
            QTimer.singleShot(0, _maybe_autofill)

    QTimer.singleShot(0, _maybe_autofill)
