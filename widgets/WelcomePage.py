from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox, QMessageBox
from PyQt5.QtGui import QIcon
from ..constants.file_paths import ResourcePaths
from ..languages.language_manager import LanguageManager
from ..engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders


class LetterIconFrame(QWidget):
    """A colorful, debug-labeled frame that renders and animates the selected letter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeLetterIconFrame")
        self.setStyleSheet("background:#ffe6e6; border:2px solid #ff4d4d; border-radius:8px;")
        self._anim = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.debug_lbl = QLabel("FRAME: WelcomeLetterIconFrame")
        layout.addWidget(self.debug_lbl)

        self.icon = QLabel()
        self.icon.setObjectName("WelcomeLetterIcon")
        self.icon.setFixedSize(80, 80)
        self.icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon, 0, Qt.AlignCenter)

    def set_debug(self, enabled: bool):
        try:
            self.debug_lbl.setVisible(bool(enabled))
        except Exception:
            pass

    def set_letter(self, letter: str):
        from PyQt5.QtCore import QPropertyAnimation

        color_map = {"A": "#e74c3c", "B": "#3498db", "C": "#27ae60"}
        self.icon.setText(
            f'<span style="font-size:64px; font-weight:700; color:{color_map.get(letter, "#333")}">{letter}</span>'
        )

        # bounce animation
        try:
            if self._anim:
                self._anim.stop()
                self._anim.deleteLater()
        except Exception:
            pass

        self._anim = QPropertyAnimation(self.icon, b"geometry", self)
        rect = self.icon.geometry()
        self._anim.setDuration(350)
        self._anim.setStartValue(rect)
        self._anim.setKeyValueAt(0.5, rect.adjusted(0, -20, 0, 20))
        self._anim.setEndValue(rect)
        try:
            self._anim.finished.connect(lambda: setattr(self, "_anim", None))
        except Exception:
            pass
        self._anim.start()


class LetterSection(QWidget):
    """Õppimiseks mõeldud eraldi tähe sektsioon koos värviliste raamide ja siltidega.
    Sisaldab: tähe ikooni (LetterIconFrame), rippmenüüd, pealkirja ja tekstihoidjat.
    """

    def __init__(self, parent=None, debug: bool = True):
        super().__init__(parent)
        self._lang = LanguageManager()
        self.setObjectName("LetterSection")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # --- Ülemine päis/pea blokk ---
        self.custom_header_frame = QWidget()
        self.custom_header_frame.setObjectName("WelcomeCustomHeaderFrame")
        self.custom_header_frame.setStyleSheet(
            "background:#fff8dc; border:2px solid #f39c12; border-radius:10px;"
        )
        outer_header_layout = QVBoxLayout(self.custom_header_frame)
        outer_header_layout.setContentsMargins(8, 8, 8, 8)
        outer_header_layout.setSpacing(6)
        self.header_debug_lbl = QLabel("FRAME: WelcomeCustomHeaderFrame")
        self.header_debug_lbl.setStyleSheet("color:#8a4b08; font-weight:600; font-size:10px;")
        outer_header_layout.addWidget(self.header_debug_lbl, 0, Qt.AlignLeft)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # --- Tähe ikoon ---
        self.letter_icon_frame = LetterIconFrame()
        header_layout.addWidget(self.letter_icon_frame)

        # --- Tähe valiku rippmenüü ---
        self.letter_selector = QComboBox()
        self.letter_selector.setObjectName("WelcomeLetterSelector")
        self.letter_selector.addItems(["A 🍎", "B 🚍", "C 🎪"])
        try:
            self.letter_selector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        except Exception:
            pass
        self.letter_selector.currentTextChanged.connect(
            lambda text: self.update_letter(text.split()[0])
        )
        self.letter_selector_frame = QWidget()
        self.letter_selector_frame.setObjectName("WelcomeLetterSelectorFrame")
        self.letter_selector_frame.setStyleSheet(
            "background:#e6ffe6; border:2px solid #27ae60; border-radius:8px;"
        )
        lsf_layout = QVBoxLayout(self.letter_selector_frame)
        lsf_layout.setContentsMargins(6, 6, 6, 6)
        lsf_layout.setSpacing(4)
        self.lsf_debug_lbl = QLabel("FRAME: WelcomeLetterSelectorFrame")
        lsf_layout.addWidget(self.lsf_debug_lbl)
        lsf_layout.addWidget(self.letter_selector)
        header_layout.addWidget(self.letter_selector_frame)

        # --- Pealkiri ---
        self.header_title = QLabel(self._lang.translate("A Tähe õppimine"))
        self.header_title.setObjectName("WelcomeHeaderTitle")
        self.header_title_frame = QWidget()
        self.header_title_frame.setObjectName("WelcomeHeaderTitleFrame")
        self.header_title_frame.setStyleSheet(
            "background:#e6f7ff; border:2px solid #3498db; border-radius:8px;"
        )
        htf_layout = QVBoxLayout(self.header_title_frame)
        htf_layout.setContentsMargins(6, 6, 6, 6)
        htf_layout.setSpacing(4)
        self.htf_debug_lbl = QLabel("FRAME: WelcomeHeaderTitleFrame")
        htf_layout.addWidget(self.htf_debug_lbl)
        htf_layout.addWidget(self.header_title)
        header_layout.addWidget(self.header_title_frame)

        outer_header_layout.addLayout(header_layout)
        root.addWidget(self.custom_header_frame)

        # --- Teksti hoidja ---
        self.text_holder = QLabel(
            self._lang.translate("A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.")
        )
        self.text_holder.setObjectName("WelcomeHeaderTextHolder")
        self.header_title.setWordWrap(True)
        self.text_holder.setWordWrap(True)
        self.text_holder_frame = QWidget()
        self.text_holder_frame.setObjectName("WelcomeTextHolderFrame")
        self.text_holder_frame.setStyleSheet(
            "background:#fbe7ff; border:2px solid #9b59b6; border-radius:8px;"
        )
        thf_layout = QVBoxLayout(self.text_holder_frame)
        thf_layout.setContentsMargins(8, 8, 8, 8)
        thf_layout.setSpacing(4)
        self.thf_debug_lbl = QLabel("FRAME: WelcomeTextHolderFrame")
        thf_layout.addWidget(self.thf_debug_lbl)
        thf_layout.addWidget(self.text_holder)
        root.addWidget(self.text_holder_frame)

        # Initsialiseeri valik
        try:
            self.update_letter(self.letter_selector.currentText().split()[0])
        except Exception:
            pass
        # apply initial debug visibility
        self.set_debug(debug)

    def update_letter(self, letter: str):
        try:
            self.letter_icon_frame.set_letter(letter)
        except Exception:
            pass
        if letter == "A":
            self.header_title.setText(self._lang.translate("A Tähe õppimine"))
            self.text_holder.setText(
                self._lang.translate("A täht on eesti tähestiku esimene täht. See on täht, millega algab paljude sõnade ja nimede kirjutamine. Õppides A tähte, teed esimese sammu lugemise ja kirjutamise oskuse poole.")
            )
        elif letter == "B":
            self.header_title.setText(self._lang.translate("B Tähe õppimine"))
            self.text_holder.setText(
                self._lang.translate("B täht on eesti tähestikus teine täht. Seda kasutatakse paljudes sõnades, näiteks 'banaan' ja 'buss'. B tähe õppimine aitab laiendada sõnavara ja parandada hääldust.")
            )
        elif letter == "C":
            self.header_title.setText(self._lang.translate("C Tähe õppimine"))
            self.text_holder.setText(
                self._lang.translate("C täht esineb eesti keeles peamiselt võõrsõnades, näiteks 'cirkus' või 'cello'. C tähe tundmine aitab mõista ja lugeda rahvusvahelisi sõnu.")
            )

    def set_debug(self, enabled: bool):
        # Toggle all debug "FRAME:" labels visibility
        for lbl in [
            getattr(self, "header_debug_lbl", None),
            getattr(self, "lsf_debug_lbl", None),
            getattr(self, "htf_debug_lbl", None),
            getattr(self, "thf_debug_lbl", None),
        ]:
            try:
                if lbl is not None:
                    lbl.setVisible(bool(enabled))
            except Exception:
                pass
        # forward to icon frame
        try:
            self.letter_icon_frame.set_debug(enabled)
        except Exception:
            pass


class WelcomePage(QWidget):
    openSettingsRequested = pyqtSignal()

    def __init__(self, lang_manager=None, theme_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        self.lang_manager = lang_manager
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
        # Prevent button from being triggered by Return key
        self.open_btn.setAutoDefault(False)
        self.open_btn.setDefault(False)

        # Debug toggle button
        self.debug_btn = QPushButton()
        self.debug_btn.setObjectName("WelcomeToggleDebugButton")
        # Prevent button from being triggered by Return key
        self.debug_btn.setAutoDefault(False)
        self.debug_btn.setDefault(False)
        self.debug_btn.setCheckable(True)
        self.debug_btn.setChecked(True)  # initial state matches LetterSection(debug=True)
        # Apply an existing icon (non-themed quick pick). For themed icons, use ThemeManager.get_qicon(...)
        try:
            self.debug_btn.setIcon(QIcon(ResourcePaths.EYE_ICON))
            self.debug_btn.setIconSize(QSize(16, 16))
        except Exception:
            pass

        # Layer Creation Engine buttons
        self.create_layer_btn = QPushButton("Loo Mailabl grupp kiht")
        self.create_layer_btn.setObjectName("WelcomeCreateLayerButton")
        self.create_layer_btn.setToolTip("Loo uus kiht Mailabl grupis testimiseks")
        # Prevent button from being triggered by Return key
        self.create_layer_btn.setAutoDefault(False)
        self.create_layer_btn.setDefault(False)
        self.create_layer_btn.clicked.connect(self._on_create_layer_clicked)

        self.create_all_subgroups_btn = QPushButton("Loo kõik alagrupid")
        self.create_all_subgroups_btn.setObjectName("WelcomeCreateAllSubgroupsButton")
        self.create_all_subgroups_btn.setToolTip("Loo test kihid kõigis Mailabl alagruppides")
        # Prevent button from being triggered by Return key
        self.create_all_subgroups_btn.setAutoDefault(False)
        self.create_all_subgroups_btn.setDefault(False)
        self.create_all_subgroups_btn.clicked.connect(self._on_create_all_subgroups_clicked)

        self.remove_layer_btn = QPushButton("Eemalda grupp kiht")
        self.remove_layer_btn.setObjectName("WelcomeRemoveLayerButton")
        self.remove_layer_btn.setToolTip("Eemalda Mailabl grupp ja selle kihid")
        # Prevent button from being triggered by Return key
        self.remove_layer_btn.setAutoDefault(False)
        self.remove_layer_btn.setDefault(False)
        self.remove_layer_btn.clicked.connect(self._on_remove_layer_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addStretch(1)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.subtitle_lbl)
        hl = QHBoxLayout()
        hl.addWidget(self.open_btn)
        hl.addWidget(self.debug_btn)
        hl.addWidget(self.create_layer_btn)
        hl.addWidget(self.create_all_subgroups_btn)
        hl.addWidget(self.remove_layer_btn)
        hl.addStretch(1)
        layout.addLayout(hl)
        layout.addStretch(2)

        # --- TÄHE SEKTOR eraldi komponendina ---
        self.letter_section = LetterSection(self, debug=True)
        layout.addWidget(self.letter_section)

        # Initial text setup
        self.retranslate(self.lang_manager)
        # Theme can be applied by parent/theme_manager if needed

        # Wire debug toggle after section exists
        self.debug_btn.toggled.connect(self._on_debug_toggled)
        self._update_debug_button_text(self.debug_btn.isChecked())

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

    # Eraldi _update_letter_info pole enam vaja; loogika on LetterSection klassis

    # Public helper to toggle debug labels from parent controller
    def set_debug(self, enabled: bool):
        try:
            self.letter_section.set_debug(enabled)
        except Exception:
            pass
        try:
            self.debug_btn.setChecked(bool(enabled))
            self._update_debug_button_text(bool(enabled))
        except Exception:
            pass

    def _on_debug_toggled(self, checked: bool):
        try:
            self.letter_section.set_debug(checked)
        except Exception:
            pass
        self._update_debug_button_text(checked)

    def _update_debug_button_text(self, checked: bool):
        # Toggle button label in Estonian (dev env, no i18n wiring per requirement)
        try:
            self.debug_btn.setText("Peida FRAME sildid" if checked else "Näita FRAME silte")
        except Exception:
            pass

    def _on_create_layer_clicked(self):
        """Handle create layer button click."""
        try:
            # Get the layer creation engine
            engine = get_layer_engine()

            # Create a test layer in the SANDBOXING subgroup
            layer_name = f"TestLayer_{len(engine.get_layers_in_group(MailablGroupFolders.SANDBOXING)) + 1}"
            result = engine.copy_virtual_layer_for_properties(
                layer_name,
                MailablGroupFolders.SANDBOXING
            )

            if result:
                QMessageBox.information(
                    self,
                    "Kiht loodud",
                    f"Kiht '{result}' on edukalt loodud grupis '{MailablGroupFolders.SANDBOXING}'"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Viga",
                    "Kihi loomine ebaõnnestus"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Viga",
                f"Kihi loomisel tekkis viga: {str(e)}"
            )

    def _on_create_all_subgroups_clicked(self):
        """Handle create all subgroups button click."""
        try:
            # Get the layer creation engine
            engine = get_layer_engine()

            # Create test layers in all subgroups
            created_layers = engine.create_test_layers_in_all_subgroups()

            if created_layers:
                layer_list = "\n".join(f"• {group}: {layer}" for group, layer in created_layers.items())
                QMessageBox.information(
                    self,
                    "Alagrupid loodud",
                    f"Edukalt loodi test kihid järgmistes alagruppides:\n\n{layer_list}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Viga",
                    "Ühegi alagrupi loomine ebaõnnestus"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Viga",
                f"Alagruppide loomisel tekkis viga: {str(e)}"
            )

    def _on_remove_layer_clicked(self):
        """Handle remove layer button click."""
        try:
            # Get the layer creation engine
            engine = get_layer_engine()

            # Get layers from all Mailabl subgroups
            layers = engine.get_all_layers_in_mailabl_groups()

            if not layers:
                QMessageBox.information(
                    self,
                    "Teave",
                    f"Mailabl gruppides ei ole ühtegi kihti"
                )
                return

            # Show confirmation dialog
            layer_names = [layer.name() for layer in layers]
            reply = QMessageBox.question(
                self,
                "Kinnita kustutamine",
                f"Kas olete kindel, et soovite kustutada järgmised kihid kõigist Mailabl gruppides?\n\n" +
                "\n".join(f"• {name}" for name in layer_names),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Remove all layers from all subgroups
                removed_count = 0
                for layer in layers:
                    try:
                        engine.project.removeMapLayer(layer.id())
                        removed_count += 1
                    except Exception as e:
                        print(f"Error removing layer {layer.name()}: {e}")

                # Check if any subgroups are now empty and remove them
                main_group = engine.layer_tree_root.findGroup(MailablGroupFolders.MAILABL_MAIN)
                if main_group:
                    subgroups_to_check = [
                        MailablGroupFolders.NEW_PROPERTIES,
                        MailablGroupFolders.SANDBOXING,
                        MailablGroupFolders.IMPORT,
                        MailablGroupFolders.SYNC,
                        MailablGroupFolders.ARCHIVE
                    ]

                    for subgroup_name in subgroups_to_check:
                        subgroup = main_group.findGroup(subgroup_name)
                        if subgroup and not subgroup.children():
                            main_group.removeChildNode(subgroup)
                            print(f"[LayerEngine] Removed empty subgroup: {subgroup_name}")

                # Check if main group is now empty and remove it
                remaining_layers = engine.get_all_layers_in_mailabl_groups()
                if not remaining_layers:
                    group_removed = engine.remove_group_if_empty(MailablGroupFolders.MAILABL_MAIN)
                    if group_removed:
                        QMessageBox.information(
                            self,
                            "Kihid ja grupp eemaldatud",
                            f"Edukalt eemaldati {removed_count} kihti ja Mailabl grupp"
                        )
                    else:
                        QMessageBox.information(
                            self,
                            "Kihid eemaldatud",
                            f"Edukalt eemaldati {removed_count} kihti"
                        )
                else:
                    QMessageBox.information(
                        self,
                        "Kihid eemaldatud",
                        f"Edukalt eemaldati {removed_count} kihti"
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Viga",
                f"Kihi eemaldamisel tekkis viga: {str(e)}"
            )
