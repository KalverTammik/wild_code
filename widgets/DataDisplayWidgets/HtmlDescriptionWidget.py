import os
import re

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFrame, QSizePolicy, QTextBrowser

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.security_boundaries import (
    DESCRIPTION_LINK_BLOCKED,
    DESCRIPTION_LINK_LOCAL_PATH,
    DESCRIPTION_LINK_NETWORK_PATH,
    DESCRIPTION_LINK_WEB,
    DescriptionLinkTarget,
    classify_description_link,
    resolve_allowed_external_extension,
)
from .TaskFilePreviewDialog import TaskFilePreviewDialog


class HtmlDescriptionWidget(QTextBrowser):
    _MARK_COLOR_MAP = {
        "purple": "#d9c2ff",
        "blue": "#cde8ff",
        "green": "#d6f5d6",
        "yellow": "#fff3b0",
        "red": "#ffd6d6",
        "gray": "#e4e7ec",
    }

    def __init__(
        self,
        html: str,
        parent=None,
        *,
        inline: bool = False,
        object_name: str = "ExtraInfoContent",
        lang_manager=None,
    ):
        super().__init__(parent)
        self._inline = inline
        self._lang = lang_manager or LanguageManager()
        self.setObjectName(object_name)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self._handle_anchor_clicked)
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

    def _handle_anchor_clicked(self, link: QUrl) -> None:
        try:
            raw_target = link.toString(QUrl.FullyDecoded)
        except Exception:
            raw_target = link.toString()

        destination = classify_description_link(raw_target)
        if destination.kind == DESCRIPTION_LINK_BLOCKED:
            try:
                decoded_target = QUrl.fromPercentEncoding(bytes(link.toEncoded()))
            except Exception:
                decoded_target = raw_target
            if decoded_target != raw_target:
                decoded_destination = classify_description_link(decoded_target)
                if decoded_destination.kind != DESCRIPTION_LINK_BLOCKED:
                    destination = decoded_destination

        if destination.kind == DESCRIPTION_LINK_WEB:
            self._open_web_destination(destination)
            return
        if destination.kind == DESCRIPTION_LINK_NETWORK_PATH:
            if not self._confirm_network_destination(destination):
                return
            self._open_filesystem_destination(destination, network_confirmed=True)
            return
        if destination.kind == DESCRIPTION_LINK_LOCAL_PATH:
            self._open_filesystem_destination(destination, network_confirmed=False)
            return
        if destination.kind == DESCRIPTION_LINK_BLOCKED:
            self._show_blocked(destination.display or raw_target)

    def _open_web_destination(self, destination: DescriptionLinkTarget) -> None:
        http_warning = ""
        if destination.scheme == "http":
            http_warning = self._lang.translate(TranslationKeys.DESCRIPTION_LINK_HTTP_WARNING)
        message = self._lang.translate(TranslationKeys.DESCRIPTION_LINK_WEB_CONFIRM).format(
            url=self._dialog_value(destination.display),
            http_warning=http_warning,
        )
        if not self._ask_confirmation(message):
            return

        try:
            opened = bool(QDesktopServices.openUrl(QUrl(destination.target, QUrl.TolerantMode)))
        except Exception:
            opened = False
        if not opened:
            self._show_open_failed(destination.display)

    def _confirm_network_destination(self, destination: DescriptionLinkTarget) -> bool:
        message = self._lang.translate(TranslationKeys.DESCRIPTION_LINK_NETWORK_CONFIRM).format(
            host=self._dialog_value(destination.host or "-"),
            path=self._dialog_value(destination.display),
        )
        return self._ask_confirmation(message)

    def _open_filesystem_destination(
        self,
        destination: DescriptionLinkTarget,
        *,
        network_confirmed: bool,
    ) -> None:
        path = str(destination.target or "").strip()
        if not path or not os.path.exists(path):
            self._show_not_found(destination.display or path)
            return

        if os.path.isdir(path):
            if not network_confirmed:
                message = self._lang.translate(TranslationKeys.DESCRIPTION_LINK_FOLDER_CONFIRM).format(
                    path=self._dialog_value(destination.display or path),
                )
                if not self._ask_confirmation(message):
                    return
            self._open_folder(path, destination.display or path)
            return

        if not os.path.isfile(path):
            self._show_not_found(destination.display or path)
            return

        extension = resolve_allowed_external_extension(local_file_path=path)
        if not extension:
            self._show_blocked(destination.display or path)
            return

        if TaskFilePreviewDialog.is_internal_preview_candidate(local_file_path=path):
            dialog = TaskFilePreviewDialog.open_preview(
                local_file_path=path,
                local_title=os.path.basename(path) or path,
                lang_manager=self._lang,
                parent=self.window(),
                compact=TaskFilePreviewDialog.is_image_preview_candidate(local_file_path=path),
            )
            if dialog is not None:
                dialog.exec_()
            return

        message = self._lang.translate(TranslationKeys.DESCRIPTION_LINK_FILE_CONFIRM).format(
            path=self._dialog_value(destination.display or path),
            extension=self._dialog_value(extension),
        )
        if not self._ask_confirmation(message):
            return
        if TaskFilePreviewDialog.open_in_default_application(
            local_file_path=path,
            user_confirmed=True,
        ):
            return
        self._show_open_failed(destination.display or path)

    def _open_folder(self, path: str, display: str) -> None:
        try:
            opened = bool(QDesktopServices.openUrl(QUrl.fromLocalFile(path)))
        except Exception:
            opened = False
        if not opened:
            self._show_open_failed(display)

    def _ask_confirmation(self, message: str) -> bool:
        yes_label = self._lang.translate(TranslationKeys.YES)
        no_label = self._lang.translate(TranslationKeys.NO)
        choice = ModernMessageDialog.ask_choice_modern(
            self._lang.translate(TranslationKeys.CONFIRM),
            message,
            buttons=[yes_label, no_label],
            parent=self,
            default=no_label,
            cancel=no_label,
        )
        return choice == yes_label

    def _show_blocked(self, target: str) -> None:
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.WARNING),
            self._lang.translate(TranslationKeys.DESCRIPTION_LINK_BLOCKED).format(
                target=self._dialog_value(target or "-"),
            ),
            parent=self,
        )

    def _show_not_found(self, target: str) -> None:
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.WARNING),
            self._lang.translate(TranslationKeys.DESCRIPTION_LINK_NOT_FOUND).format(
                target=self._dialog_value(target or "-"),
            ),
            parent=self,
        )

    def _show_open_failed(self, target: str) -> None:
        ModernMessageDialog.show_warning(
            self._lang.translate(TranslationKeys.ERROR),
            self._lang.translate(TranslationKeys.DESCRIPTION_LINK_OPEN_FAILED).format(
                target=self._dialog_value(target or "-"),
            ),
            parent=self,
        )

    @staticmethod
    def _dialog_value(value: object) -> str:
        text = "".join(
            character if ord(character) >= 32 and ord(character) != 127 else " "
            for character in str(value or "")
        )
        return text.replace("<", "‹").replace(">", "›")

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
