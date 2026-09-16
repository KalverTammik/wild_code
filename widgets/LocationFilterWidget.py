from PyQt5 import sip
from PyQt5.QtCore import QObject, QTimer, QSignalBlocker, QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QProgressBar,
    QPushButton,
)
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ..utils.mapandproperties.PropertyUpdateFlowCoordinator import PropertyUpdateFlowCoordinator
from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ..utils.MapTools.MapHelpers import MapHelpers
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..constants.button_props import ButtonVariant
from ..constants.module_icons import IconNames
from ..Logs.python_fail_logger import PythonFailLogger
from ..Logs.switch_logger import SwitchLogger
from .theme_manager import ThemeManager


class LocationFilterHelper(QObject):
    """Keep hierarchical choices responsive and publish only complete, current results."""

    def __init__(self, *, county_combo, municipality_combo, city_combo, properties_table,
                 after_table_update, stop_checks, invalidate_archive_scope,
                 update_add_button_state, stop_map_update, status_widget, parent=None):
        super().__init__(parent)
        self.county_combo = county_combo
        self.municipality_combo = municipality_combo
        self.city_combo = city_combo
        self.properties_table = properties_table
        self._after_table_update = after_table_update
        self._stop_checks = stop_checks
        self._invalidate_archive_scope = invalidate_archive_scope
        self._update_add_button_state = update_add_button_state
        self._stop_map_update = stop_map_update
        self._status = status_widget
        # Counties load at once; each county's municipalities and settlements load when it is picked.
        self._locations = {}
        self._counties_loaded = False
        self._layer = None
        self._closed = False
        self._signals_connected = False
        self._last_city_selection = ()
        self._loader = PropertyUpdateFlowCoordinator(self)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.failed.connect(self._on_failed)
        self._city_reload_timer = QTimer(self)
        self._city_reload_timer.setSingleShot(True)
        self._city_reload_timer.setInterval(250)
        self._city_reload_timer.timeout.connect(self._load_current_scope)
        self._status.retry_button.clicked.connect(self._retry)
        self._status.refresh_button.clicked.connect(self._retry)

    def connect_signals(self):
        if self._signals_connected:
            return
        self.county_combo.currentIndexChanged.connect(self._on_county_combo_changed)
        self.municipality_combo.currentIndexChanged.connect(self._on_municipality_combo_changed)
        self.city_combo.checkedItemsChanged.connect(self._on_city_checked_items_changed)
        # QgsCheckableComboBox updates its text on model changes, but keyboard
        # check-state changes do not emit checkedItemsChanged in QGIS 3.40.
        self.city_combo.model().dataChanged.connect(self._on_city_model_changed)
        self._signals_connected = True

    def _fill_combo(self, combo, values, placeholder_key):
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItem(self._status.lang_manager.translate(placeholder_key), '')
        for value in sorted(values):
            combo.addItem(value, value)
        combo.setEnabled(bool(values))
        del blocker

    def _clear_cities(self):
        blocker = QSignalBlocker(self.city_combo)
        self.city_combo.clear()
        self.city_combo.setEnabled(False)
        self._last_city_selection = ()
        del blocker

    def _clear_table(self):
        self._city_reload_timer.stop()
        self._loader.cancel()
        self._invalidate_archive_scope()
        PropertyTableManager().populate_properties_table([], self.properties_table)
        self._stop_map_update()
        self._stop_checks(False)
        self._update_add_button_state(0)

    def load_counties(self, layer):
        if self._closed:
            return
        self._disconnect_layer()
        self._layer = layer
        if layer is not None and not sip.isdeleted(layer):
            layer.dataChanged.connect(self._on_layer_changed)
            layer.dataSourceChanged.connect(self._on_layer_changed)
            layer.updatedFields.connect(self._on_layer_changed)
            layer.willBeDeleted.connect(self._on_layer_removed)
        self._locations = {}
        self._counties_loaded = False
        self._clear_table()
        self._fill_combo(self.county_combo, [], TranslationKeys.SELECT_COUNTY)
        self._fill_combo(self.municipality_combo, [], TranslationKeys.SELECT_MUNICIPALITY)
        self._clear_cities()
        try:
            if layer is None or sip.isdeleted(layer) or not layer.isValid():
                raise ValueError('The property import layer is missing or invalid')
            counties = PropertyDataLoader.read_counties(layer)
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module='property', event='property_location_load_failed')
            self._on_failed(str(exc))
            return
        self._fill_combo(self.county_combo, counties, TranslationKeys.SELECT_COUNTY)
        self._counties_loaded = True
        self._status.set_status(TranslationKeys.SELECT_COUNTY if counties else TranslationKeys.LOCATION_NO_CHOICES)

    def _disconnect_layer(self):
        layer = self._layer
        if layer is None or sip.isdeleted(layer):
            return
        layer.dataChanged.disconnect(self._on_layer_changed)
        layer.dataSourceChanged.disconnect(self._on_layer_changed)
        layer.updatedFields.disconnect(self._on_layer_changed)
        layer.willBeDeleted.disconnect(self._on_layer_removed)
        self._layer = None

    def _on_layer_changed(self):
        self.load_counties(MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG))

    def _on_layer_removed(self):
        self._disconnect_layer()
        self._clear_table()
        self._locations = {}
        self._counties_loaded = False
        self._fill_combo(self.county_combo, [], TranslationKeys.SELECT_COUNTY)
        self._fill_combo(self.municipality_combo, [], TranslationKeys.SELECT_MUNICIPALITY)
        self._clear_cities()
        self._on_failed('The import layer was removed')

    def close(self):
        self._closed = True
        self._city_reload_timer.stop()
        self._loader.cancel()
        self._stop_map_update()
        self._disconnect_layer()

    def _scope(self):
        return (str(self.county_combo.currentData() or ''),
                str(self.municipality_combo.currentData() or ''),
                tuple(sorted(self.city_combo.checkedItems())))

    def _on_county_combo_changed(self, _index):
        self._clear_table()
        county = self.county_combo.currentData()
        self._fill_combo(self.municipality_combo, self._locations.get(county, {}), TranslationKeys.SELECT_MUNICIPALITY)
        self._clear_cities()
        self._load_current_scope()

    def _on_municipality_combo_changed(self, _index):
        self._clear_table()
        county, municipality, _ = self._scope()
        settlements = self._locations.get(county, {}).get(municipality, [])
        blocker = QSignalBlocker(self.city_combo)
        self.city_combo.clear()
        self.city_combo.addItems(settlements)
        self.city_combo.setEnabled(bool(settlements))
        self._last_city_selection = ()
        del blocker
        self._load_current_scope()

    def _on_city_model_changed(self, _first, _last, roles):
        if not roles or Qt.CheckStateRole in roles or Qt.DisplayRole in roles:
            self._on_city_checked_items_changed()

    def _on_city_checked_items_changed(self):
        if self._closed or self.city_combo.signalsBlocked():
            return
        selection = self._scope()[2]
        if selection == self._last_city_selection:
            return
        self._last_city_selection = selection
        self._clear_table()
        self._status.set_status(TranslationKeys.LOCATION_LOADING_PROPERTIES, busy=True)
        self._city_reload_timer.start()

    def reload_current_table_from_filters(self):
        self._clear_table()
        self._load_current_scope()

    def _load_current_scope(self):
        if self._closed:
            return
        scope = self._scope()
        if not scope[0]:
            self._status.set_status(TranslationKeys.SELECT_COUNTY)
            return
        include_properties = bool(scope[1])
        if include_properties:
            key = TranslationKeys.LOCATION_LOADING_PROPERTIES
        elif scope[0] not in self._locations:
            key = TranslationKeys.LOCATION_LOADING_CHOICES
        else:
            key = TranslationKeys.LOCATION_LOADING_MAP
        self._status.set_status(key, busy=True)
        SwitchLogger.log('property_location_scope_requested', module='property', extra={'scope': scope})
        self._loader.load_scope(self._layer, scope, include_properties=include_properties)

    @pyqtSlot(str, object)
    def _on_loaded(self, _kind, result):
        if self._closed:
            return
        current = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if (current is None or not current.isValid()
                or (current.id(), current.source()) != self._loader.layer_identity):
            self._on_failed('The import layer changed during loading')
            return
        tree = result.get('tree')
        if tree is not None:
            county = result['scope'][0]
            # A county read holds that county's complete choices; keep them even if the user moved on.
            self._locations[county] = tree
            if self._scope()[0] == county and self.municipality_combo.count() <= 1:
                self._fill_combo(self.municipality_combo, tree, TranslationKeys.SELECT_MUNICIPALITY)
        if result['scope'] != self._scope():
            SwitchLogger.log('property_location_scope_discarded', module='property', extra={
                'loaded_scope': result['scope'], 'current_scope': self._scope()})
            return
        if result['include_properties']:
            PropertyTableManager().populate_properties_table(result['rows'], self.properties_table)
            self._after_table_update(self.properties_table)
            self._status.set_status(TranslationKeys.LOCATION_PROPERTIES_READY, count=len(result['rows']))
            SwitchLogger.log('property_location_table_ready', module='property', extra={
                'scope': result['scope'], 'rows': len(result['rows'])})
        else:
            self._status.set_status(TranslationKeys.SELECT_MUNICIPALITY)
        try:
            MapHelpers.apply_scope_preview(current, result['feature_ids'], result['extent'], select=bool(result['scope'][2]))
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module='property', event='property_location_map_failed')
            self._status.set_status(TranslationKeys.LOCATION_MAP_FAILED, error=str(exc))

    @pyqtSlot(str)
    def _on_failed(self, message):
        if self._closed:
            return
        self._invalidate_archive_scope()
        self._status.set_status(TranslationKeys.LOCATION_LOAD_FAILED, error=message)

    def _retry(self):
        if self._closed:
            return
        layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if not self._counties_loaded or layer is not self._layer:
            self.load_counties(layer)
        else:
            self.reload_current_table_from_filters()


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
        self.city_combo.setMaxVisibleItems(12)
        self.city_combo.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SELECT_SETTLEMENTS))
        self.city_combo.setEnabled(False)
        ThemeManager.apply_checkable_combo_popup_style(self.city_combo)
        city_layout.addWidget(self.city_combo)
        location_layout.addLayout(city_layout)

        self.refresh_button = QPushButton('', self)
        self.refresh_button.setObjectName('LocationRefreshButton')
        self.refresh_button.setProperty('variant', ButtonVariant.ICON)
        self.refresh_button.setAutoDefault(False)
        self.refresh_button.setDefault(False)
        self.refresh_button.setFixedSize(22, 22)
        self.refresh_button.setIcon(ThemeManager.get_qicon(IconNames.ICON_REFRESH))
        self.refresh_button.setIconSize(QSize(14, 14))
        refresh_label = self.lang_manager.translate(TranslationKeys.LOCATION_REFRESH)
        self.refresh_button.setToolTip(refresh_label)
        self.refresh_button.setAccessibleName(refresh_label)
        location_layout.addWidget(self.refresh_button, 0, Qt.AlignBottom)

        location_layout.addStretch()
        filter_layout.addLayout(location_layout)

        status_layout = QHBoxLayout()
        self.loading_indicator = QProgressBar(self)
        self.loading_indicator.setRange(0, 0)
        self.loading_indicator.setTextVisible(False)
        self.loading_indicator.setFixedSize(50, 6)
        self.loading_indicator.hide()
        self.status_label = QLabel(self.lang_manager.translate(TranslationKeys.SELECT_COUNTY), self)
        self.status_label.setTextFormat(Qt.PlainText)
        self.status_label.setWordWrap(True)
        self.retry_button = QPushButton(self.lang_manager.translate(TranslationKeys.CARD_LOAD_RETRY), self)
        self.retry_button.setAutoDefault(False)
        self.retry_button.hide()
        status_layout.addWidget(self.loading_indicator)
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.retry_button)
        filter_layout.addLayout(status_layout)

    def set_status(self, key, *, busy=False, count=None, error=None):
        text = self.lang_manager.translate(key)
        self.status_label.setText(text.format(count=count) if count is not None else text)
        self.status_label.setToolTip(error or '')
        self.loading_indicator.setVisible(busy)
        self.retry_button.setVisible(error is not None)
