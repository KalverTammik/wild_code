from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy
from qgis.PyQt.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from qgis.core import Qgis

from ..config.setup import Version
from ..utils.url_manager import OpenLink
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
import datetime


class FooterWidget(QWidget):



    def __init__(self, parent=None, show_left=True, show_right=True, compact=False):
        super().__init__(parent)

        # Outer frame for the glow + top border (styled via QSS)
        frame = QFrame(self)
        frame.setObjectName("footerWidgetFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 2, 8, 2 if compact else 3)
        layout.setSpacing(6)

        # Left: one rich-text label with programmatic links (no visible hrefs)
        if show_left:
            current_year = datetime.datetime.now().year
            wl = OpenLink()

            left_label = FooterLinksLabel(
                [f"© {current_year} Tuloli OÜ/Kavito", "Koduleht", "Privaatsus", "Kasutustingimused"],
                [None, wl.main, wl.privacy, wl.terms],
            )
            left_label.setObjectName("footerLeftLabel")
            left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            left_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            left_label.setCursor(Qt.PointingHandCursor)

            layout.addWidget(left_label)
        else:
            layout.addStretch(1)

        # Right: versions
        if show_right:
            from ..constants.file_paths import ConfigPaths
            metadata_file = ConfigPaths.METADATA
            qgis_version = Qgis.QGIS_VERSION
            plugin_version = Version.get_plugin_version(metadata_file)

            right = QLabel(f"QGIS {qgis_version} | Plugin v{plugin_version}")
            right.setObjectName("footerLabel")
            right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            right.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            layout.addStretch(1)
            layout.addWidget(right)
        else:
            layout.addStretch(1)

        # Set final layout on the widget
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        # Apply QSS (your ThemeManager call)

        self.retheme_footer()
        
    def retheme_footer(self):
        """
        Re-applies the correct theme and QSS to the footer, forcing a style refresh.
        """
        ThemeManager.apply_module_style(self, [QssPaths.FOOTER])


class FooterLinksLabel(QLabel):
    def __init__(self, text_segments, urls, parent=None):
        """
        text_segments: ["© 2025 Valisee", "Koduleht", "Privaatsus", "Kasutustingimused"]
        urls:          [None, home_url, privacy_url, terms_url]
                       (None means not clickable)
        """
        super().__init__(parent)
        self.segments = text_segments
        self.urls = urls

        # Build rich text with href tokens but no visible URLs
        html_parts = []
        for seg, url in zip(text_segments, urls):
            if url:
                html_parts.append(f'<a href="{url}">{seg}</a>')
            else:
                html_parts.append(seg)

        self.setText(" | ".join(html_parts))
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setOpenExternalLinks(False)  # handle ourselves for full control
        self.linkActivated.connect(self.open_link)

    def open_link(self, link: str):
        QDesktopServices.openUrl(QUrl(link))
