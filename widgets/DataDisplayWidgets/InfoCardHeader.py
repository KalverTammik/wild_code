from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy
)
try:
    import sip
except Exception:  # pragma: no cover - runtime availability depends on QGIS/PyQt packaging
    sip = None
from ...widgets.theme_manager import ThemeManager
from ...constants.module_icons import MiscIcons
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...module_manager import ModuleManager
from ...python.responses import DataDisplayExtractors
from ...utils.url_manager import Module
from .PriorityWidget import PriorityWidget
from .TagsWidget import TagsWidget


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text or ""
        self._is_eliding = False
        self._pending_elide = False
        self._elide_timer = QTimer(self)
        self._elide_timer.setSingleShot(True)
        self._elide_timer.timeout.connect(self._safe_elide)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setWordWrap(False)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setObjectName("ElidedLabel")
        self.setMinimumHeight(12)

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        super().setText(self._full)
        self._schedule_elide()

    def resizeEvent(self, e):
        if self._is_eliding:
            super().resizeEvent(e)
            return
        super().resizeEvent(e)
        self._schedule_elide()

    def _schedule_elide(self):
        if self._is_deleted():
            return
        if self._is_eliding:
            return
        if self.width() > 0:
            self._safe_elide()
            return
        if self._pending_elide:
            return
        self._pending_elide = True
        self._elide_timer.start(0)

    def _is_deleted(self) -> bool:
        try:
            return bool(sip and sip.isdeleted(self))
        except Exception:
            return False

    def _safe_elide(self):
        if self._is_deleted():
            return
        try:
            self._elide()
        except RuntimeError:
            return

    def _elide(self):
        if self._pending_elide:
            self._pending_elide = False
        if self._is_eliding:
            return
        if self._is_deleted():
            return
        if self.width() <= 0:
            return
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width()))
        if elided == self.text():
            return
        self._is_eliding = True
        try:
            super().setText(elided)
        finally:
            self._is_eliding = False


class InfocardHeaderFrame(QFrame):
    def __init__(self, item_data, module_name=None, parent=None, lang_manager=None):
        super().__init__(parent)
        
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("InfocardHeaderFrame")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(0)
        self._lang = lang_manager or LanguageManager()
        self._number_badge = None
        self._name_label = None
        self._client_label = None
        self._type_badge = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # Left column
        left = QFrame(self)
        left.setObjectName("HeaderLeft")
        leftL = QVBoxLayout(left)
        leftL.setContentsMargins(0, 0, 0, 0)
        leftL.setSpacing(4)

        
        # Name row: conditional layout based on number display setting
        nameRow = QHBoxLayout()
        nameRow.setContentsMargins(0,0,0,0) 
        nameRow.setSpacing(6)

        if module_name != Module.PROJECT.value and DataDisplayExtractors.extract_is_public(item_data):
            privateIcon = QLabel()
            privateIcon.setObjectName("ProjectPrivateIcon")
            privateIcon.setToolTip(self._lang.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_INFOCARDHEADER_TOOLTIP))
            icon = ThemeManager.get_qicon(MiscIcons.ICON_IS_PRIVATE)
            privateIcon.setPixmap(icon.pixmap(12, 12))
            nameRow.addWidget(privateIcon, 0, Qt.AlignVCenter)
        
        number = DataDisplayExtractors.extract_item_number(item_data) or '-'
        if number and number != '-':
            numberBadge = QLabel(str(number))
            numberBadge.setObjectName("ProjectNumberBadge")
            numberBadge.setAlignment(Qt.AlignCenter)
            numberBadge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            self._number_badge = numberBadge
            nameRow.addWidget(numberBadge, 0, Qt.AlignVCenter)

        priority_widget = PriorityWidget(item_data, parent=self, lang_manager=self._lang)
        if not priority_widget.isHidden():
            nameRow.addWidget(priority_widget, 0, Qt.AlignVCenter)

        name = DataDisplayExtractors.extract_item_name(item_data)
        nameLabel = ElidedLabel(name)
        nameLabel.setObjectName("ProjectNameLabel")
        nameLabel.setMinimumWidth(0)
        nameLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        nameRow.addWidget(nameLabel, 1, Qt.AlignVCenter)
        self._name_label = nameLabel

        tags = DataDisplayExtractors.extract_tag_names(item_data)
        if tags:
            nameRow.addWidget(TagsWidget(tags), 0, Qt.AlignVCenter)
        leftL.addLayout(nameRow)

        type_badge = self._create_type_badge(item_data, module_name)
        self._type_badge = type_badge
        client = DataDisplayExtractors.extract_client_display_name(item_data)
        if type_badge is not None or client:
            metaRow = QHBoxLayout()
            metaRow.setContentsMargins(0, 0, 0, 0)
            metaRow.setSpacing(6)

            if type_badge is not None:
                metaRow.addWidget(type_badge, 0, Qt.AlignLeft | Qt.AlignVCenter)

            if client:
                icon = ThemeManager.get_qicon(MiscIcons.ICON_IS_CLIENT)
                clientIcon = QLabel()
                clientIcon.setPixmap(icon.pixmap(12, 12))
                clientIcon.setObjectName("ClientIcon")
                metaRow.addWidget(clientIcon, 0, Qt.AlignVCenter)

                clientLabel = ElidedLabel(client)
                clientLabel.setObjectName("ProjectClientLabel")
                clientLabel.setMinimumWidth(0)
                clientLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                metaRow.addWidget(clientLabel, 1, Qt.AlignVCenter)
                self._client_label = clientLabel
            leftL.addLayout(metaRow)

        root.addWidget(left, 1, Qt.AlignVCenter)
        self._sync_number_badge_width()
        self._sync_vertical_metrics()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.StyleChange, QEvent.FontChange):
            self._sync_number_badge_width()
            self._sync_vertical_metrics()

    def _sync_number_badge_width(self):
        badge = self._number_badge
        if badge is None:
            return
        badge.ensurePolished()
        text_width = badge.fontMetrics().horizontalAdvance(badge.text())
        badge.setFixedWidth(max(24, text_width + 18))

    def _sync_vertical_metrics(self):
        if self._name_label is not None:
            name_h = max(16, self._name_label.fontMetrics().height() + 3)
            self._name_label.setMinimumHeight(name_h)
        if self._client_label is not None:
            client_h = max(14, self._client_label.fontMetrics().height() + 2)
            self._client_label.setMinimumHeight(client_h)
        if self._type_badge is not None:
            chip_h = max(16, self._type_badge.fontMetrics().height() + 5)
            self._type_badge.setFixedHeight(chip_h)

    def _create_type_badge(self, item_data, module_name=None):
        supports_types = False
        module_key = (module_name or "").strip().lower()
        if module_key in ("task", "tasks"):
            supports_types = True
        elif module_key:
            supports = ModuleManager().getModuleSupports(module_key)
            if supports:
                supports_types = bool(supports[0])

        type_info = DataDisplayExtractors.extract_type(item_data)
        name = (type_info.name or "").strip() or "-"
        if name == "-" and not supports_types:
            return None

        badge = ElidedLabel(name)
        badge.setObjectName("TypeInlineLabel")
        badge.setAlignment(Qt.AlignCenter)
        badge.setToolTip(name)
        badge.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        badge.setMinimumWidth(56)
        badge.setMaximumWidth(160)
        return badge
