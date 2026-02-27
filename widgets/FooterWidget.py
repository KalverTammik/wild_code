import datetime

from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis

from ..utils.url_manager import OpenLink, loadWebpage
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths, ConfigPaths


class FooterWidget(QWidget):
    def __init__(self, parent=None, show_left=True, show_right=True):
        super().__init__(parent)

        self._version_label: QLabel | None = None

        frame = QFrame(self)
        frame.setObjectName("footerWidgetFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 2, 8, 3)
        layout.setSpacing(6)

        if show_left:
            current_year = datetime.date.today().year
            wl = OpenLink()

            left_label = FooterLinksLabel(
                [f"© {current_year} Tuloli OÜ/Kavito", "Koduleht", "Privaatsus", "Kasutustingimused"],
                [None, wl.main, wl.privacy, wl.terms],
                parent=frame,
            )
            left_label.setObjectName("footerLeftLabel")
            left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            left_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            left_label.setCursor(Qt.PointingHandCursor)
            layout.addWidget(left_label)
        else:
            layout.addStretch(1)

        if show_right:
            self._version_label = QLabel("", frame)
            self._version_label.setObjectName("footerLabel")
            self._version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._version_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            layout.addStretch(1)
            layout.addWidget(self._version_label)

            self.refresh_versions()
        else:
            layout.addStretch(1)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self.retheme_footer()

    def refresh_versions(self) -> None:
        if not self._version_label:
            return

        qgis_version = getattr(Qgis, "QGIS_VERSION", "?")
        plugin_version = str(getattr(ConfigPaths, "PLUGIN_VERSION", "?") or "?").strip() or "?"
        is_dev = bool(getattr(ConfigPaths, "IS_DEV", False))
        env_suffix = " DEV" if is_dev else ""

        self._version_label.setText(f"QGIS {qgis_version} | Plugin v{plugin_version}{env_suffix}")

    def retheme_footer(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.FOOTER])


class FooterLinksLabel(QLabel):
    def __init__(self, text_segments, urls, parent=None):
        super().__init__(parent)

        if len(text_segments) != len(urls):
            raise ValueError("FooterLinksLabel: text_segments and urls length mismatch")

        html_parts = []
        for seg, url in zip(text_segments, urls):
            if url:
                html_parts.append(f'<a href="{url}">{seg}</a>')
            else:
                html_parts.append(seg)

        self.setText(" | ".join(html_parts))
        self.setTextFormat(Qt.RichText)

        self.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)

        self.setOpenExternalLinks(False)
        self.linkActivated.connect(loadWebpage.open_webpage)