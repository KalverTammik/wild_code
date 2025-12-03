from typing import Any, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame,
)
from qgis.core import QgsProject
from qgis.utils import iface
from ...constants.layer_constants import PROPERTY_TAG
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from .PropertyUITools import PropertyUITools
from .property_tree_widget import PropertyTreeWidget
from ...widgets.theme_manager import ThemeManager,styleExtras
from ...constants.file_paths import QssPaths
from ...languages.translation_keys import TranslationKeys
from ...utils.url_manager import Module

class PropertyModule(QWidget):
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

        super().__init__()
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
        header_frame.setMinimumHeight(150)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(self.margin_layout, self.margin_layout, self.margin_layout, self.margin_layout)
        header_layout.setSpacing(self.vertical_label_spacing)
        

        self.pbdisplayPropertyInfo = QPushButton(self.lang_manager.translate(TranslationKeys.CHOOSE_FROM_MAP))
        self.pbdisplayPropertyInfo.setObjectName("ChooseFromMapButton")
        self.pbdisplayPropertyInfo.clicked.connect(self.tools.select_property_from_map)
        header_layout.addWidget(self.pbdisplayPropertyInfo)


        # Property details in horizontal layout: General data (green) | Additional data
        details_frame = QFrame()
        details_frame.setObjectName("PropertyDetailsFrame")
        details_frame.setFrameStyle(QFrame.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(self.margin_layout, self.margin_layout, self.margin_layout, self.margin_layout)
        details_layout.setSpacing(self.vertical_label_spacing)

        # Store reference to details frame for theme updates
        self.details_frame = details_frame

        # Details title
        details_title = QLabel("Kinnistu andmed")
        details_title.setObjectName("DetailsTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        details_title.setFont(title_font)
        details_layout.addWidget(details_title)

        # Property data layout
        data_layout = QHBoxLayout()
        data_layout.setSpacing(self.margin_layout * 3)  # 18px spacing between left/right sections

        # Left side: General data (cadastral number and address) in green frame
        basic_frame = QFrame()
        basic_frame.setObjectName("BasicInfoFrame")
        basic_frame.setFrameStyle(QFrame.Box)
        basic_frame.setLineWidth(2)

        basic_layout = QVBoxLayout(basic_frame)
        basic_layout.setContentsMargins(self.horizontal_label_spacing, self.horizontal_label_spacing, self.horizontal_label_spacing, self.horizontal_label_spacing)
        basic_layout.setSpacing(self.vertical_label_spacing)

        # Katastritunnus - horizontal layout (label + value)
        tunnus_layout = QHBoxLayout()
        tunnus_label = QLabel("Katastritunnus:")
        tunnus_label.setObjectName("InfoLabel")
        tunnus_layout.addWidget(tunnus_label)
        self.lbl_katastritunnus_value = QLabel()
        self.lbl_katastritunnus_value.setText("katastritunnus...")
        tunnus_layout.addWidget(self.lbl_katastritunnus_value)
        tunnus_layout.addStretch()
        basic_layout.addLayout(tunnus_layout)

        # Kinnistu registry number - horizontal layout (label + value) underneath katastritunnus
        kinnistu_layout = QHBoxLayout()
        kinnistu_label = QLabel("(reg.nr:)")
        kinnistu_label.setObjectName("InfoLabel")
        kinnistu_layout.addWidget(kinnistu_label)
        self.lbl_kinnistu_value = QLabel()
        self.lbl_kinnistu_value.setText("...")
        kinnistu_layout.addWidget(self.lbl_kinnistu_value)
        kinnistu_layout.addStretch()
        basic_layout.addLayout(kinnistu_layout)

        # Address - horizontal layout (label + value)
        address_layout = QHBoxLayout()
        address_label = QLabel("Aadress:")
        address_label.setObjectName("InfoLabel")
        address_layout.addWidget(address_label)
        self.lbl_address_value = QLabel()
        self.lbl_address_value.setText("...")
        address_layout.addWidget(self.lbl_address_value)
        address_layout.addStretch()
        basic_layout.addLayout(address_layout)

        data_layout.addWidget(basic_frame)

        # Right side: Additional data (area and sihtotstarve)
        additional_frame = QFrame()
        additional_frame.setObjectName("AdditionalInfoFrame")
        additional_layout = QVBoxLayout(additional_frame)
        additional_layout.setContentsMargins(self.margin_layout, self.margin_layout, self.margin_layout, self.margin_layout)
        additional_layout.setSpacing(self.horizontal_label_spacing)

        # Area - horizontal layout (label + value)
        pindala_layout = QHBoxLayout()
        pindala_label = QLabel("Pindala (m²):")
        pindala_label.setObjectName("InfoLabel")
        pindala_layout.addWidget(pindala_label)
        self.lbl_area_value = QLabel()
        self.lbl_area_value.setText("0.00")
        pindala_layout.addWidget(self.lbl_area_value)
        pindala_layout.addStretch()
        additional_layout.addLayout(pindala_layout)

        # Sihtotstarve - three separate labels (hide if NULL)
        sihtotstarve_layout = QVBoxLayout()
        sihtotstarve_layout.setSpacing(self.vertical_label_spacing)

        # Siht 1
        siht1_layout = QHBoxLayout()
        self.lbl_siht1_label = QLabel("Siht 1:")
        self.lbl_siht1_label.setObjectName("InfoLabel")
        siht1_layout.addWidget(self.lbl_siht1_label)
        self.lbl_siht1_value = QLabel()
        self.lbl_siht1_value.setText("...")
        siht1_layout.addWidget(self.lbl_siht1_value)
        siht1_layout.addStretch()
        sihtotstarve_layout.addLayout(siht1_layout)

        # Siht 2
        siht2_layout = QHBoxLayout()
        self.lbl_siht2_label = QLabel("Siht 2:")
        self.lbl_siht2_label.setObjectName("InfoLabel")
        siht2_layout.addWidget(self.lbl_siht2_label)
        self.lbl_siht2_value = QLabel()
        self.lbl_siht2_value.setText("...")
        siht2_layout.addWidget(self.lbl_siht2_value)
        siht2_layout.addStretch()
        sihtotstarve_layout.addLayout(siht2_layout)

        # Siht 3
        siht3_layout = QHBoxLayout()
        self.lbl_siht3_label = QLabel("Siht 3:")
        self.lbl_siht3_label.setObjectName("InfoLabel")
        siht3_layout.addWidget(self.lbl_siht3_label)
        self.lbl_siht3_value = QLabel()
        self.lbl_siht3_value.setText("...")
        siht3_layout.addWidget(self.lbl_siht3_value)
        siht3_layout.addStretch()
        sihtotstarve_layout.addLayout(siht3_layout)

        additional_layout.addLayout(sihtotstarve_layout)

        # Registr - registration date
        registr_layout = QHBoxLayout()
        registr_label = QLabel("Moodustatud:")
        registr_label.setObjectName("InfoLabel")
        registr_layout.addWidget(registr_label)
        self.lbl_registr_value = QLabel()
        self.lbl_registr_value.setText("...")
        registr_layout.addWidget(self.lbl_registr_value)
        registr_layout.addStretch()
        additional_layout.addLayout(registr_layout)

        # Muudet - modification date
        muudet_layout = QHBoxLayout()
        muudet_label = QLabel("Viimati muudetud:")
        muudet_label.setObjectName("InfoLabel")
        muudet_layout.addWidget(muudet_label)
        self.lbl_muudet_value = QLabel()
        self.lbl_muudet_value.setText("...")
        muudet_layout.addWidget(self.lbl_muudet_value)
        muudet_layout.addStretch()
        additional_layout.addLayout(muudet_layout)

        data_layout.addWidget(additional_frame)

        details_layout.addLayout(data_layout)

        header_layout.addWidget(details_frame)

        styleExtras.apply_chip_shadow(details_frame)

        return header_frame

    def retheme(self):
        # Apply main module styling
        ThemeManager.apply_module_style(self, [QssPaths.PROPERTIES_UI, QssPaths.MODULE_CARD])

    def activate(self):
        """Called when the module becomes active."""
        try:

            # Find the property layer
            project = QgsProject.instance()
            for layer in project.mapLayers().values():
                if layer.customProperty(PROPERTY_TAG):
                    active_layer = layer
                    break
            else:
                return  # No property layer found

            # Check if there's a selected feature and display it
            selected_features = active_layer.selectedFeatures()
            if selected_features:
                self.tools.update_property_display(active_layer)

        except Exception as e:
            print(f"Error in activate: {e}")

    def deactivate(self):
        """Called when the module becomes inactive."""
        pass

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

