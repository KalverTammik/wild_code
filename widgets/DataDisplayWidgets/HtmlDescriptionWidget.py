import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QSizePolicy, QTextBrowser


class HtmlDescriptionWidget(QTextBrowser):
    _MARK_COLOR_MAP = {
        "purple": "#d9c2ff",
        "blue": "#cde8ff",
        "green": "#d6f5d6",
        "yellow": "#fff3b0",
        "red": "#ffd6d6",
        "gray": "#e4e7ec",
    }

    def __init__(self, html: str, parent=None, *, inline: bool = False, object_name: str = "ExtraInfoContent"):
        super().__init__(parent)
        self._inline = inline
        self.setObjectName(object_name)
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)
        self.setReadOnly(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        if inline:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHtml(self.normalize_html(html or ""))

    @classmethod
    def normalize_html(cls, html: str) -> str:
        normalized = str(html or "").strip()
        if not normalized:
            return ""

        def replace_mark(match):
            attrs = match.group(1) or ""
            lower_attrs = attrs.lower()
            color = "#fff3b0"
            for name, fallback in cls._MARK_COLOR_MAP.items():
                if name in lower_attrs:
                    color = fallback
                    break
            return f'<span style="background-color: {color};">'

        normalized = re.sub(r"<mark\b([^>]*)>", replace_mark, normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"</mark>", "</span>", normalized, flags=re.IGNORECASE)
        normalized = re.sub(
            r"<table(?![^>]*border=)([^>]*)>",
            r'<table border="1" cellspacing="0" cellpadding="6"\1>',
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(
            r"<blockquote>",
            '<blockquote style="margin: 8px 0; padding-left: 12px; border-left: 3px solid #d0d5dd;">',
            normalized,
            flags=re.IGNORECASE,
        )
        return normalized

    def showEvent(self, event):  # noqa: N802 - Qt override
        super().showEvent(event)
        self._sync_inline_height()

    def resizeEvent(self, event):  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._sync_inline_height()

    def _sync_inline_height(self):
        if not self._inline:
            return
        viewport_width = max(0, self.viewport().width())
        if viewport_width <= 0:
            return
        self.document().setTextWidth(viewport_width)
        doc_height = self.document().documentLayout().documentSize().height()
        frame = self.frameWidth() * 2
        margins = self.contentsMargins().top() + self.contentsMargins().bottom()
        target_height = max(24, int(doc_height) + frame + margins + 4)
        self.setMinimumHeight(target_height)
        self.setMaximumHeight(target_height)