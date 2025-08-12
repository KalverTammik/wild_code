from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox


class WelcomePage(QWidget):


    openSettingsRequested = pyqtSignal()

    def __init__(self, lang_manager=None, theme_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        self.lang_manager = lang_manager
        # Keep a reference to the current letter animation to avoid early GC
        self._letter_anim = None

        # Build UI widgets and keep references for retranslation
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("WelcomeTitle")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("WelcomeSubtitle")
        self.subtitle_lbl.setWordWrap(True)
        self.open_btn = QPushButton()
        self.open_btn.clicked.connect(self.openSettingsRequested.emit)
        self.open_btn.setObjectName("WelcomeOpenSettingsButton")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addStretch(1)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.subtitle_lbl)
        hl = QHBoxLayout()
        hl.addWidget(self.open_btn)
        hl.addStretch(1)
        layout.addLayout(hl)
        layout.addStretch(2)

        # --- Custom header frame for A Tähe õppimine ---
        self.custom_header_frame = QWidget()
        self.custom_header_frame.setObjectName("WelcomeCustomHeaderFrame")
        header_layout = QHBoxLayout(self.custom_header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        # --- Tähe ikooni suur ja värviline kuvamine ---
        self.letter_icon = QLabel()
        self.letter_icon.setObjectName("WelcomeLetterIcon")
        self.letter_icon.setFixedSize(80, 80)
        self.letter_icon.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.letter_icon)  # kõige esimeseks
        # Pealkiri
        self.header_title = QLabel("A Tähe õppimine")
        self.header_title.setObjectName("WelcomeHeaderTitle")
        header_layout.addWidget(self.header_title)
    # --- Tähe valiku rippmenüü ---
        self.letter_selector = QComboBox()
        self.letter_selector.setObjectName("WelcomeLetterSelector")
        self.letter_selector.addItems(["A", "B", "C"])
        self.letter_selector.setFixedWidth(60)
        # Paiguta rippmenüü pealkirja ja ikooni vahele
        header_layout.insertWidget(1, self.letter_selector)
        self.letter_selector.currentTextChanged.connect(self._update_letter_info)
        layout.addWidget(self.custom_header_frame)
        # --- Teksti hoidja ---
        self.text_holder = QLabel("A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.")
        self.text_holder.setObjectName("WelcomeHeaderTextHolder")
        self.text_holder.setWordWrap(True)
        layout.addWidget(self.text_holder)

        # Initial text setup
        self.retranslate(self.lang_manager)
        # Initialize letter icon/title/body for current selection
        try:
            self._update_letter_info(self.letter_selector.currentText())
        except Exception:
            pass
        # Theme is applied at dialog level; child inherits. Optionally apply module QSS here if needed.
        # if theme_manager:
        #     try:
        #         from ..constants.file_paths import QssPaths
        #         theme_manager.apply_module_style(self, [QssPaths.MAIN])
        #     except Exception:
        #         pass

    # Public API ------------------------------------------------------
    def retranslate(self, lang_manager=None):
        if lang_manager is not None:
            self.lang_manager = lang_manager
        lm = self.lang_manager
        if lm:
            self.title_lbl.setText(lm.translate("Welcome"))
            self.subtitle_lbl.setText(lm.translate("Select a module from the left or open Settings to set your preferred module."))
            self.open_btn.setText(lm.translate("Open Settings"))
        else:
            self.title_lbl.setText("Welcome")
            self.subtitle_lbl.setText("Select a module from the left or open Settings to set your preferred module.")
            self.open_btn.setText("Open Settings")

    def _update_letter_info(self, letter):
        from PyQt5.QtCore import QPropertyAnimation
        color_map = {"A": "#e74c3c", "B": "#3498db", "C": "#27ae60"}
        self.letter_icon.setText(f'<span style="font-size:64px; font-weight:700; color:{color_map.get(letter, "#333")}">{letter}</span>')
        # Bounce animatsioon
        # Stop and dispose previous animation if any
        try:
            if getattr(self, "_letter_anim", None):
                self._letter_anim.stop()
                self._letter_anim.deleteLater()
        except Exception:
            pass
        # Parent the animation to self and keep a reference so it isn't GC'd
        self._letter_anim = QPropertyAnimation(self.letter_icon, b"geometry", self)
        rect = self.letter_icon.geometry()
        self._letter_anim.setDuration(350)
        self._letter_anim.setStartValue(rect)
        self._letter_anim.setKeyValueAt(0.5, rect.adjusted(0, -20, 0, 20))
        self._letter_anim.setEndValue(rect)
        # Clear reference on finish
        try:
            self._letter_anim.finished.connect(lambda: setattr(self, "_letter_anim", None))
        except Exception:
            pass
        self._letter_anim.start()
        if letter == "A":
            self.header_title.setText("A Tähe õppimine")
            self.text_holder.setText("A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.")
        elif letter == "B":
            self.header_title.setText("B Tähe õppimine")
            self.text_holder.setText("B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust.")
        elif letter == "C":
            self.header_title.setText("C Tähe õppimine")
            self.text_holder.setText("C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu.")
