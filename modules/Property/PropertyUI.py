from typing import Any, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame,
)
from qgis.core import QgsProject
from ...utils.MapTools.MapHelpers import ActiveLayersHelper
from ...constants.layer_constants import PROPERTY_TAG
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from .PropertyUITools import PropertyUITools
from .property_tree_widget import PropertyTreeWidget
from ...widgets.theme_manager import ThemeManager,styleExtras
from ...constants.button_props import ButtonVariant, ButtonSize
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...utils.url_manager import Module
from ...ui.mixins.token_mixin import TokenMixin
from ...Logs.python_fail_logger import PythonFailLogger
from ...widgets.PropertySummaryCard import PropertySummaryCard

class PropertyModule(TokenMixin, QWidget):
    """
    Property module - focused on displaying and managing data for a single property item.
    Features a header area with info/tools and a tree view for property-related data.
    """
    
    QUERY_FILE = "ListFilteredProperties.graphql" #Not active yet
    USE_TYPE_FILTER = False
    BATCH_SIZE = 0


    # Signal emitted when a property is selected from map
    property_selected_from_map = pyqtSignal()
    # Signal emitted when property selection process is completed
    property_selection_completed = pyqtSignal()
    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:

        QWidget.__init__(self)
        TokenMixin.__init__(self)
        self.name = Module.PROPERTY.value
        self.lang_manager = lang_manager
        self.tools = PropertyUITools(self)

        self.horizontal_label_spacing = 3
        self.margin_layout = 6
        self.vertical_label_spacing = 6

        # Setup UI
        self.setup_ui()
        # Apply theming
        self.retheme()

    def setup_ui(self):
        """Setup the property module interface with header and tree view."""

        root = QVBoxLayout(self)
        root.setContentsMargins(self.margin_layout, self.margin_layout, self.margin_layout, self.margin_layout)
        root.setSpacing(self.vertical_label_spacing)

        # Header section
        header_frame = self.create_header_section()
        root.addWidget(header_frame)

        # Tree view section
        self.tree_section = PropertyTreeWidget(lang_manager=self.lang_manager)
        root.addWidget(self.tree_section, 1)

    def create_header_section(self):
        """Create the header area with property info and tools."""
        header_frame = QFrame()
        header_frame.setObjectName("PropertyHeader")
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(self.margin_layout, self.margin_layout, self.margin_layout, self.margin_layout)
        header_layout.setSpacing(self.vertical_label_spacing)

        # Title + action row
        top_row = QHBoxLayout()
        details_title = QLabel("Kinnistu andmed")
        details_title.setObjectName("DetailsTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        details_title.setFont(title_font)
        top_row.addWidget(details_title)
        top_row.addStretch()

        self.pbdisplayPropertyInfo = QPushButton(self.lang_manager.translate(TranslationKeys.CHOSE_FROM_MAP))
        self.pbdisplayPropertyInfo.setObjectName("ChooseFromMapButton")
        self.pbdisplayPropertyInfo.setProperty("variant", ButtonVariant.PRIMARY)
        self.pbdisplayPropertyInfo.setProperty("btnSize", ButtonSize.SMALL)
        self.pbdisplayPropertyInfo.clicked.connect(self.tools.select_property_from_map)
        top_row.addWidget(self.pbdisplayPropertyInfo)
        header_layout.addLayout(top_row)

        self.property_summary_card = PropertySummaryCard(header_frame)
        self.details_frame = self.property_summary_card.findChild(QFrame, "PropertyDetailsFrame")
        header_layout.addWidget(self.property_summary_card)

        for attr_name in (
            "lbl_katastritunnus_value",
            "lbl_kinnistu_value",
            "lbl_address_value",
            "lbl_area_value",
            "lbl_siht1_label",
            "lbl_siht1_value",
            "lbl_siht2_label",
            "lbl_siht2_value",
            "lbl_siht3_label",
            "lbl_siht3_value",
            "lbl_registr_value",
            "lbl_muudet_value",
        ):
            setattr(self, attr_name, getattr(self.property_summary_card, attr_name))

        styleExtras.apply_chip_shadow(self.details_frame)
        return header_frame

    def retheme(self):
        # Apply main module styling
        ThemeManager.apply_module_style(self, [QssPaths.PROPERTIES_UI, QssPaths.MODULE_CARD, QssPaths.BUTTONS])

    def _resolve_window_manager(self):
        try:
            host_window = self.window()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_module_window_resolve_failed",
            )
            return None
        if host_window is None:
            return None
        return getattr(host_window, "window_manager", None)

    def _disconnect_window_manager_signals(self) -> None:
        window_manager = self._resolve_window_manager()
        if window_manager is None:
            return
        try:
            try:
                self.property_selected_from_map.disconnect(window_manager._minimize_window)
            except TypeError:
                pass
            self.property_selection_completed.disconnect(window_manager._restore_window)
        except TypeError:
            pass
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_module_signal_disconnect_failed",
            )

    def _connect_window_manager_signals(self) -> None:
        window_manager = self._resolve_window_manager()
        if window_manager is None:
            return
        self._disconnect_window_manager_signals()
        try:
            self.property_selected_from_map.connect(
                window_manager._minimize_window,
                type=Qt.UniqueConnection,
            )
            self.property_selection_completed.connect(
                window_manager._restore_window,
                type=Qt.UniqueConnection,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_module_signal_connect_failed",
            )

    def activate(self):
        """Called when the module becomes active."""
        self._connect_window_manager_signals()
        try:
            print("[property_ui] activate")
            # Resolve the property layer using the same helper as map selection
            active_layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
            if not active_layer:
                print("[property_ui] no property layer found via helper")
                return

            # Check if there's a selected feature and display it
            selected_features = active_layer.selectedFeatures()
            print(f"[property_ui] selected features count: {len(selected_features)}")
            if selected_features:
                self.tools.update_property_display(active_layer)

        except Exception as e:
            print(f"Error in activate: {e}")

    def deactivate(self):
        """Called when the module becomes inactive."""
        self._disconnect_window_manager_signals()
        print("[property_ui] deactivate")

    def get_widget(self):
        """Return the module's main QWidget."""
        return self

    def open_item_from_search(self, search_module: str, item_id: str, title: str) -> None:
        """Open a property coming from unified search by property id.

        The unified search already knows the internal property id, so we can
        skip any map selection or cadastral->id lookup and directly ask the
        PropertyUITools to load connections for this id, reusing the same
        tree/entry pipeline used for map-based selection.
        """
        #print(f"[DEBUG open_item_from_search] Opening property from search: module={search_module}, item_id={item_id}, title={title}")
        self.tools.open_property_from_search(item_id)

