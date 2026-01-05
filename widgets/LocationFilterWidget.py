from typing import Callable, Optional

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.mapandproperties.PropertyUpdateFlowCoordinator import PropertyUpdateFlowCoordinator


class LocationFilterHelper(QObject):
    """Owns the location filter behavior (county/municipality/settlement) for a dialog.

    Keeps the dialog focused on building UI and non-location flows.
    """

    def __init__(
        self,
        *,
        county_combo: QComboBox,
        municipality_combo: QComboBox,
        city_combo: QgsCheckableComboBox,
        properties_table,
        after_table_update: Callable,
        stop_checks: Callable[[bool], None],
        update_add_button_state: Callable[[int], None],
        zoom_map: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)

        self.county_combo = county_combo
        self.municipality_combo = municipality_combo
        self.city_combo = city_combo
        self.properties_table = properties_table

        self._after_table_update = after_table_update
        self._stop_checks = stop_checks
        self._update_add_button_state = update_add_button_state
        self._zoom_map = zoom_map

        self._zoom_after_table_update = False

        self._city_reload_timer = QTimer(self)
        self._city_reload_timer.setSingleShot(True)
        self._city_reload_timer.setInterval(250)
        self._city_reload_timer.timeout.connect(self._apply_city_filter_update)

        self._signals_connected = False

    def connect_signals(self) -> None:
        if self._signals_connected:
            return
        self.county_combo.currentTextChanged.connect(self._on_county_combo_changed)
        self.municipality_combo.currentTextChanged.connect(self._on_municipality_combo_changed)
        self.city_combo.checkedItemsChanged.connect(self._on_city_checked_items_changed)
        self._signals_connected = True

    def load_counties(self, property_layer) -> None:
        PropertyUpdateFlowCoordinator.load_county_combo(self.county_combo, property_layer)

    def stop_pending_city_reload(self) -> None:
        self._city_reload_timer.stop()

    def request_zoom_after_next_table_update(self) -> None:
        self._zoom_after_table_update = True

    def handle_after_table_update(self) -> None:
        if self._zoom_after_table_update:
            self._zoom_after_table_update = False
            try:
                self._zoom_map()
            except Exception:
                # Zoom is best-effort; don't break the UI flow.
                pass

    def reload_current_table_from_filters(self, *, zoom: bool = False) -> None:
        self._stop_checks(True)

        if zoom:
            self.request_zoom_after_next_table_update()

        # Prefer reloading via city handler: if no cities are checked, it loads all municipality properties.
        if self.city_combo is not None and bool(self.city_combo.isEnabled()):
            self._city_reload_timer.start()
            return

        # Fallback: reload via municipality handler.
        self._on_municipality_combo_changed(self.municipality_combo.currentText())

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------
    def _on_county_combo_changed(self, text: str) -> None:
        self.stop_pending_city_reload()
        PropertyUpdateFlowCoordinator.on_county_changed(
            text,
            self.municipality_combo,
            self.properties_table,
            after_table_update=self._after_table_update,
        )

    def _on_municipality_combo_changed(self, text: str) -> None:
        self.stop_pending_city_reload()
        PropertyUpdateFlowCoordinator.on_municipality_changed(
            text,
            self.county_combo,
            self.municipality_combo,
            self.city_combo,
            self.properties_table,
            after_table_update=self._after_table_update,
        )

    def _on_city_checked_items_changed(self) -> None:
        # Stop checks immediately (results would be stale once the table reloads).
        self._stop_checks(False)
        try:
            self._update_add_button_state(0)
        except Exception:
            pass

        self.request_zoom_after_next_table_update()
        self._city_reload_timer.start()

    def _apply_city_filter_update(self) -> None:
        PropertyUpdateFlowCoordinator.on_city_changed(
            self.properties_table,
            self.county_combo,
            self.municipality_combo,
            self.city_combo,
            after_table_update=self._after_table_update,
            update_map=False,
        )


class LocationFilterWidget(QFrame):
    """Reusable county/municipality/settlement filter widget."""

    def __init__(self, lang_manager: LanguageManager, parent=None):
        super().__init__(parent)

        self.lang_manager = lang_manager

        self.setObjectName("FilterFrame")
        self.setFrameStyle(QFrame.StyledPanel)

        filter_layout = QVBoxLayout(self)
        filter_layout.setContentsMargins(6, 6, 6, 6)
        filter_layout.setSpacing(6)

        filter_title = QLabel(self.lang_manager.translate(TranslationKeys.FILTER_BY_LOCATION))
        filter_title.setObjectName("FilterTitle")
        filter_layout.addWidget(filter_title)

        location_layout = QHBoxLayout()
        location_layout.setSpacing(6)

        county_layout = QVBoxLayout()
        county_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.COUNTY)}:")
        county_label.setObjectName("CountyLabel")
        county_layout.addWidget(county_label)

        self.county_combo = QComboBox()
        self.county_combo.setObjectName("CountyCombo")
        self.county_combo.addItem(self.lang_manager.translate(TranslationKeys.SELECT_COUNTY), "")
        county_layout.addWidget(self.county_combo)
        location_layout.addLayout(county_layout)

        municipality_layout = QVBoxLayout()
        municipality_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.MUNICIPALITY)}:")
        municipality_label.setObjectName("MunicipalityLabel")
        municipality_layout.addWidget(municipality_label)

        self.municipality_combo = QComboBox()
        self.municipality_combo.setObjectName("MunicipalityCombo")
        self.municipality_combo.addItem(self.lang_manager.translate(TranslationKeys.SELECT_MUNICIPALITY), "")
        self.municipality_combo.setEnabled(False)
        municipality_layout.addWidget(self.municipality_combo)
        location_layout.addLayout(municipality_layout)

        city_layout = QVBoxLayout()
        city_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.SETTLEMENT)}:")
        city_label.setObjectName("CityLabel")
        city_layout.addWidget(city_label)

        self.city_combo = QgsCheckableComboBox()
        self.city_combo.setObjectName("CityCombo")
        self.city_combo.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SELECT_SETTLEMENTS))
        self.city_combo.setEnabled(False)
        city_layout.addWidget(self.city_combo)
        location_layout.addLayout(city_layout)

        location_layout.addStretch()
        filter_layout.addLayout(location_layout)
