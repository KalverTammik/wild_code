import processing
from PyQt5.QtCore import QObject, pyqtSignal
from qgis.utils import iface
from qgis.core import QgsMapLayer, QgsProject, QgsProcessingFeatureSourceDefinition, QgsVectorLayer
from qgis.gui import QgsMapToolPan


from PyQt5.uic import loadUi
from PyQt5 import QtCore
from ...utils.PrintHelper import PrintHelpers
from .Easements import queryHandling
from .resticon import WaterWorks, GetRuledRestriction
from ..Union import Union
from ..propertie_layer.InsertPropertiesToMailabl import PropertiesLayerFunctions
from ..item_selector_tools import UseQGISNative
from ...processes.OnFirstLoad.AddSetupLayers import SetupLayers, MailablGroupFolders
from ...config.settings import SettingsDataSaveAndLoad
from ...config.QGISSettingPaths import LayerSettings, SettingsLoader
from ...config.settings import Filepaths, Flags, SettingsDataSaveAndLoad, FilesByNames
from ...KeelelisedMuutujad.messages import Headings, HoiatusTexts, EdukuseTexts
from ..intersect import Intersect, TempIntersectLayerName
from ..join_layers import JoinLayers
from ...utils.messagesHelper import ModernMessageDialog


pealkiri = Headings()
sisu = HoiatusTexts()
edu = EdukuseTexts()

on_selection_changed_lambda_easements = None

goup_layer_name = ''



class EasementTools(QObject):
    widgetClosed = pyqtSignal()

    def __init__(self, tweasementView):
        super().__init__()  # Call the __init__ method of the QObject superclass
        self.tweasementView = tweasementView
        self.widget_EasmentTools = None
        self.is_select_tool_activated = False
        self.select_tool = None
        self.select_tool_connection = None


    def load_widget(self):
        global on_selection_changed_lambda_easements
        on_selection_changed_lambda_easements = None
        if self.widget_EasmentTools is None:
            # Create a new instance of the widget if it doesn't exist
            table = self.tweasementView
            selection_model = table.selectionModel()
            if selection_model.hasSelection():
                ui_file_path = Filepaths.get_easements_tools()
                self.widget_EasmentTools = loadUi(ui_file_path)
                save_button = self.widget_EasmentTools.pbSave
                cancel_button = self.widget_EasmentTools.pbCancel
                clear_buffer_button = self.widget_EasmentTools.pbClearCadastrals
                properties_table = self.widget_EasmentTools.tvProperties
                pbGen_easement = self.widget_EasmentTools.pbKoostaServituut
                
                ##### Create function if mind is clear!
                #pbGen_easement.setEnabled(False)
                #if properties_table has model:
                #    pbGen_easement = self.widget_EasmentTools.pbKoostaServituut
                #    pbGen_easement.setEnabled(True)
                # Connect button click signals


                self.connect_button_click_signal()

                self.widget_EasmentTools.show()
                self.widget_EasmentTools.pbprint.setEnabled(False)
                # Get the checkboxes and their associated texts and functions
                self.checkboxes_info = EasementTools.get_checkbox_info(self.widget_EasmentTools)

                # Update checkbox texts and connect them to functions
                EasementTools.update_checkboxes(self.checkboxes_info, properties_table)
                
                number = WidgetTools.load_selected_item_name(table, self.widget_EasmentTools)

                buffer_dialer = self.widget_EasmentTools.dPuhvriSuurus
                buffer_dialer.setValue(20)
                buffer_dialer.setEnabled(False)
                buffer_label = self.widget_EasmentTools.label
                buffer_label.setText("Puhver: 2,0m")
                buffer_label.setEnabled(False)
                
                
                combobox = self.widget_EasmentTools.cmbScale
                available_scale_factors = [(100, 0), (250, 1), (500, 2), (750, 3), (1000, 4), (5000, 5)]
                selection_id = 0
                ComboBoxInputs.add_values_and_set_first(combobox, available_scale_factors, selection_id)
                combobox.setEnabled(False)

                all_line_edits = EasementTools.widget_line_edits(self.widget_EasmentTools)[0] #returns the first return value of the set 
                EasementTools.disable_UIelements(all_line_edits)
                if self.select_tool is None:
                    WidgetTools.loadselectedProperties(self, self.widget_EasmentTools)
                    
                self.widget_EasmentTools.pbprint.clicked.connect(lambda: EasementTools.PrintEasement(self.widget_EasmentTools, number))

                pbGen_easement.clicked.connect(lambda: GenerateEasement.generate_easement(self.widget_EasmentTools))            
                
                clear_buffer_button.clicked.connect(lambda: MapCleaners.clearPuhver2m(properties_table))
                self.widget_EasmentTools.pbAddRoad.clicked.connect(lambda: BufferByLine.create_road_center_line(self.widget_EasmentTools))

                #style_name = FilesByNames().Easement_style         
                #buffer_properties_button.clicked.connect(lambda: BufferTools.generate_buffer_around_selected_item(self.widget_EasmentTools, TempBufferLayerNames.buffer_layer_name, active_layer_name, style_name))
                save_button.clicked.connect(lambda: self.on_save_button_clicked(self.checkboxes_info))
                cancel_button.clicked.connect(lambda: self.on_cancel_button_clicked(self.checkboxes_info))
                
                # Connect closeEvent method to handle window close event
                self.widget_EasmentTools.closeEvent = self.closeEvent

        else:
            # If an instance already exists, simply show it
            self.cleanup()
            self.widget_EasmentTools.show()
        pass

    def closeEvent(self, event):
        self.cleanup()
        self.Buffer_cleanup()
        if on_selection_changed_lambda_easements:
            active_layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)
            active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
            active_layer.selectionChanged.disconnect(on_selection_changed_lambda_easements)

        Flags.active_properties_layer_flag = False
        self.widget_EasmentTools.close()
        self.uncheck_checkboxes(self.widget_EasmentTools, self.checkboxes_info)  # Uncheck checkboxes
        self.widget_EasmentTools.pbprint.setEnabled(False)
        self.widget_EasmentTools.setEnabled(False)

        event.accept()  # Allow the window to close
        self.widgetClosed.emit()

    def on_save_button_clicked(self, checkboxes_info):
        self.Buffer_cleanup()
        if self.widget_EasmentTools is not None:
            text = "Olen alles arenduses. \n mitte midagi ei salvestatud"
            heading = pealkiri.tubli
            self.cleanup()
            self.uncheck_checkboxes(self.widget_EasmentTools, checkboxes_info)  # Uncheck checkboxes
            ModernMessageDialog.Info_messages_modern_REPLACE_WITH_DECISIONMAKER(heading, text)
            if on_selection_changed_lambda_easements:
                active_layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)
                active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
                active_layer.selectionChanged.disconnect(on_selection_changed_lambda_easements)
                #self.widget_EasmentTools.dPuhvriSuurus.disconnet(WidgetTools.activ_dialer)
            Flags.active_properties_layer_flag = False
            self.widget_EasmentTools.pbprint.setEnabled(False)            
            self.widget_EasmentTools.cmbScale.setEnabled(False)
            self.widget_EasmentTools.accept()
        self.widgetClosed.emit()
            
    def on_cancel_button_clicked(self, checkboxes_info):
        self.Buffer_cleanup()
        if self.widget_EasmentTools is not None:
            self.cleanup()
            text = sisu.kasutaja_peatas_protsessi
            heading = pealkiri.infoSimple
            ModernMessageDialog.Info_messages_modern_REPLACE_WITH_DECISIONMAKER(heading, text)
            if on_selection_changed_lambda_easements:
                active_layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)
                active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
                active_layer.selectionChanged.disconnect(on_selection_changed_lambda_easements)
            self.uncheck_checkboxes(self.widget_EasmentTools, checkboxes_info)  # Uncheck checkboxes
            self.widget_EasmentTools.pbprint.setEnabled(False)
            self.widget_EasmentTools.cmbScale.setEnabled(False)
            Flags.active_properties_layer_flag = False
            self.widget_EasmentTools.reject()
        self.widgetClosed.emit()

    @staticmethod
    def PrintEasement(widget, number):
        layout_name = widget.lblLayoutName.text()
        layout_map_item = widget.lblMapObject.text()
        layer_name = Union().UnionLayer
        comboBox = widget.cmbScale
        scale_text = comboBox.currentText()
        value_string = ""
        model = widget.tvProperties.model()
        for row in range(model.rowCount()):
            index_1 = model.index(row, 1)  # 1 represents the second column (0-indexed)
            index_2 = model.index(row, 2)
            index_3 = model.index(row, 3)
            index_4 = model.index(row, 4)
            value1 = index_1.data()
            value2 = index_2.data()
            value3 = index_3.data()
            value4 = index_4.data()
            value_string += str(value1) + ", " + str(value2) + ", "+ str(value3) + ", " + str(value4)

        PrintHelpers.printprewiev_selected_items(layer_name, layout_name, layout_map_item, scale_text, value_string, number)

    def connect_button_click_signal(self):
        if self.widget_EasmentTools:
            # Connect the button click signal only if the widget exists
            select_button = self.widget_EasmentTools.pbValiKinnistu

            if not self.select_tool_connection:
                self.select_tool_connection = select_button.clicked.connect(
                    lambda: WidgetTools.activate_layer_and_use_selectTool(self, self.widget_EasmentTools)
                )
     

    @staticmethod
    def get_checkbox_info(widget):
        water_checkbox = getattr(widget, 'cbV', None)
        sewer_checkbox = getattr(widget, 'cbK', None)
        prSewer_checkbox = getattr(widget, 'cbKSK', None)
        drainage_checkbox = getattr(widget, 'cbD', None)
        sewagePumping_checkbox = getattr(widget, 'cbsewagePupming', None)
        SewageDump_checkbox = getattr(widget, 'cbSewageDump', None) #Purgimissõlm
        sewagePlant_checkbox = getattr(widget, 'cbsewagePlant', None)
        WaterStation_checkbox = getattr(widget, 'cbWaterStation', None)
        Rainwater_checkbox = getattr(widget, 'cbSK', None)
        RainPump_checkbox = getattr(widget, 'cbRainPump', None)

      # Define texts for checkboxes
        checkbox_texts = {
            water_checkbox: WaterWorks().survetorustik_1,
            sewer_checkbox: WaterWorks().vabavoolsed_torustikud_1,
            prSewer_checkbox: WaterWorks().survetorustik_1,
            drainage_checkbox: WaterWorks().vabavoolsed_torustikud_1,
            sewagePumping_checkbox: WaterWorks().pumpla_1,
            SewageDump_checkbox: WaterWorks().purgimissõlm,
            sewagePlant_checkbox: WaterWorks().purgimissõlm,
            WaterStation_checkbox: WaterWorks().purgimissõlm,
            Rainwater_checkbox: WaterWorks().vabavoolsed_torustikud_1,
            RainPump_checkbox: WaterWorks().pumpla_1
        }

        # Define lambdas to connect checkboxes to functions (to be implemented)
        checkbox_functions = {
            water_checkbox: lambda: cbMapSelectors.selectWater_pipes(widget, water_checkbox),
            sewer_checkbox: lambda: cbMapSelectors.selectSewer_pipes(widget, sewer_checkbox),
            prSewer_checkbox: lambda: cbMapSelectors.selectprSewer_pipes(widget, prSewer_checkbox),
            drainage_checkbox: lambda: cbMapSelectors.selectDrainage_pipes(widget, drainage_checkbox),
            sewagePumping_checkbox: None ,
            SewageDump_checkbox: None,
            sewagePlant_checkbox: None,
            WaterStation_checkbox: None,
            Rainwater_checkbox: None,
            RainPump_checkbox: None,
        }

        # Create checkboxes_info dictionary
        checkboxes_info = {}
        for checkbox, text in checkbox_texts.items():
            if checkbox:
                checkboxes_info[checkbox] = (text, checkbox_functions.get(checkbox))

        return checkboxes_info

    @staticmethod
    def widget_line_edits(widget):
        le1 = widget.lblDeK
        le2 = widget.lblDeV
        le3 = widget.lblDeSK
        le4 = widget.lblHK
        le5 = widget.lblHV
        le6 = widget.lblHSK  # Purgimissõlm
        le7 = widget.lblLayoutName
        le8 = widget.lblMapObject

        # Create label_info dictionary
        widget_all_hiden_lineedits = {le1,le2,le3,le4,le5,le6,le7,le8}
        on_selectio_change = {le1,le2,le3,le4,le5,le6}
        preprint_set = {le7,le8}
        
        return widget_all_hiden_lineedits, on_selectio_change, preprint_set

    def disable_UIelements(UI_element_list):
        for element in UI_element_list:
            element.setEnabled(False) 

    def enable_UIelements(UI_element_list):
        for label in UI_element_list:
            label.setEnabled(True) 

    @staticmethod
    def uncheck_checkboxes(widget, checkboxes_info):
        for checkbox, (text, connect_function) in checkboxes_info.items():
            if checkbox:
                checkbox.setChecked(False)

    @staticmethod
    def update_checkboxes(checkboxes_info, table = None):
        if table is not None:
            model = table.model()
           

        for checkbox, (text, connect_function) in checkboxes_info.items():
            if checkbox:
                current_text = checkbox.text()
                if connect_function is not None:
                    if model is None:
                        checkbox.setEnabled(False)
                    elif model is not  None:
                        item_count = model.rowCount()
                        if item_count == 0:
                            checkbox.setEnabled(False)
                        else:
                            checkbox.setEnabled(True)
                            checkbox.clicked.connect(connect_function)
                else:
                    checkbox.setText(f"{current_text}* ({text}m)")
                    checkbox.setEnabled(False)

    def clear_table(self):
        if self.widget_EasmentTools is not None:
            model = self.widget_EasmentTools.tvProperties.model()
            if model is not None:
                model.clear()

    def cleanup(self):
        if self.is_select_tool_activated:
            # Deactivate select tool
            self.deactivate_select_tool()
            self.is_select_tool_activated = False

    def Buffer_cleanup(self):
        layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)        
        all_buffers = TempBufferLayerNames.buffer_layers
        for temp_layer_name in all_buffers:
            MapCleaners.clear_selection_and_delete_temp_layer(layer_name,temp_layer_name)
        
        layer_name = Union().UnionLayer
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if layer:
            layer = layer[0].id()  # Get the first layer if found
            QgsProject.instance().removeMapLayer(layer)
        else:
            # print(f"layer '{layer_name}' not found.")
            pass
        
        WorkLayers = WorkingLayers.list_of_workinglayers()
        for layer_name in WorkLayers:    
            layer = QgsProject.instance().mapLayersByName(layer_name)
            if layer:
                layer = layer[0]
                layer.removeSelection()

    def deactivate_select_tool(self):
        # Deactivate selection tool
        if self.select_tool:
            iface.mapCanvas().setMapTool(QgsMapToolPan(iface.mapCanvas()))
            self.select_tool = None


class WidgetTools:

    @staticmethod
    def activ_dialer(widget):
        WidgetTools.dialer(widget)
        active_layer_name = SettingsDataSaveAndLoad().load_target_cadastral_name()
        style_name = FilesByNames().Easement_style
        BufferTools.generate_buffer_around_selected_item(widget,TempBufferLayerNames.buffer_layer_name, active_layer_name, style_name)

    def dialer(widget):
        value = widget.dPuhvriSuurus.value() / 10  # divide by 10 to convert to the desired units
        puhver = round(value * 2) / 2  # round up to nearest 0.5 increment
        widget.label.setText(f'Puhver: {puhver:.1f}m')

        
    @staticmethod
    def loadselectedProperties(self, widget):
        table_view = widget.tvProperties
        pbGen_easement = widget.pbKoostaServituut

        flag = Flags.active_properties_layer_flag
        flag = True
        Flags.active_properties_layer_flag = flag
        active_layer_name = SettingsDataSaveAndLoad().load_target_cadastral_name()
        active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
        if not isinstance(active_layer, QgsMapLayer):
            return
        iface.setActiveLayer(active_layer)

        if active_layer and active_layer.selectedFeatureCount() > 0:
            # Show the widget when there are selected features
            PropertiesLayerFunctions.generate_table_from_selected_map_items(self, table_view, active_layer_name)
            table_view.update()
            widget.showNormal()
            active_layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)
            style_name = FilesByNames().Easement_style
            BufferTools.generate_buffer_around_selected_item(widget, TempBufferLayerNames.buffer_layer_name, active_layer_name, style_name)
            labels = EasementTools.widget_line_edits(self.widget_EasmentTools)[1] #acces first item set returned by function
            #print(f"lineEdits: {labels}")
            EasementTools.enable_UIelements(labels)

            checkbox_info = EasementTools.get_checkbox_info(widget)
            EasementTools.update_checkboxes(checkbox_info,table_view)

            buffer_dialer = widget.dPuhvriSuurus
            buffer_dialer.setEnabled(True)
            pbGen_easement.setEnabled(True)
            buffer_dialer.valueChanged.connect(
                    lambda: WidgetTools.activ_dialer(widget))
            buffer_label = self.widget_EasmentTools.label
            buffer_label.setEnabled(True)
                
        pass

    def activate_layer_and_use_selectTool(self, widget):
        #print("started with activated layer")
        global on_selection_changed_lambda_easements
        active_layer_name = SettingsDataSaveAndLoad().load_target_cadastral_name()
        active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
        if not isinstance(active_layer, QgsMapLayer):
            return

        iface.setActiveLayer(active_layer)
        iface.actionSelect().trigger()
        #print("start selecting stuff")
        #Hide the main window
        #print(f"Flag status befor if statement {flag}")
        
        if active_layer and active_layer.selectedFeatureCount() > 0:
            # Show the widget when there are selected features
            table_view = widget.tvProperties

            help = PropertiesLayerFunctions()
            help.generate_table_from_selected_map_items(table_view, active_layer_name)
            style_name = FilesByNames().Easement_style
            BufferTools.generate_buffer_around_selected_item(widget, TempBufferLayerNames.buffer_layer_name, active_layer_name, style_name)
            table_view.update()
            widget.showNormal()


        flag = Flags.active_properties_layer_flag
        if flag:
            
          # print(f"value of lambda_esaments before connecting: {on_selection_changed_lambda_easements}")
            on_selection_changed_lambda_easements = lambda: WidgetTools.on_selection_changed(widget)
            active_layer.selectionChanged.connect(on_selection_changed_lambda_easements)
          # print(f"value of lambda_esaments: {on_selection_changed_lambda_easements}")
            widget.showMinimized()  # Assuming widget is defined somewhere     
            
        else:
            # print("Flag is false")
            pass

    @staticmethod
    def on_selection_changed(widget):
            
        active_layer_name = SettingsDataSaveAndLoad().load_target_cadastral_name()
        if Flags.active_properties_layer_flag:
            active_layer = QgsProject.instance().mapLayersByName(active_layer_name)[0]
            if active_layer and active_layer.selectedFeatureCount() > 0:
                table_view = widget.tvProperties
                help = PropertiesLayerFunctions()
                help.generate_table_from_selected_map_items(table_view, active_layer_name)
                style_name = FilesByNames().Easement_style
                BufferTools.generate_buffer_around_selected_item(widget, TempBufferLayerNames.buffer_layer_name, active_layer_name, style_name)

                table_view.update()
                checkbox_info = EasementTools.get_checkbox_info(widget)
                EasementTools.update_checkboxes(checkbox_info,table_view)
                labels = EasementTools.widget_line_edits(widget)[1] #acces first item set returned by function
                EasementTools.enable_UIelements(labels)
                buffer_dialer = widget.dPuhvriSuurus
                buffer_dialer.setEnabled(True)
                
                buffer_dialer.valueChanged.connect(
                        lambda: WidgetTools.activ_dialer(widget))
                widget.showNormal()

        else:
            # If the flag is false, do nothing
            # print("Flag is false")
            pass

    @staticmethod
    def load_selected_item_name(table, widget):
        label = widget.lSelectedEasment

        table_headers = queryHandling()
        selected_row_index = table.selectionModel().currentIndex().row()
        model = table.model()
        value_name = table_headers.header_name
        value_number = table_headers.header_number

        column_index_name = None
        column_index_number = None

        for column in range(model.columnCount()):
            header_data = model.headerData(column, QtCore.Qt.Horizontal)
            if header_data:
                if header_data == value_name:
                    column_index_name = column
                elif header_data == value_number:
                    column_index_number = column

        if column_index_name is not None and column_index_number is not None:
            name = model.data(model.index(selected_row_index, column_index_name))
            number = model.data(model.index(selected_row_index, column_index_number))

            if name !='' and number !='':
                text = f"{number} {name}"
            
            
            elif name is not None:
                text = name
            elif number is not None:
                text = number
            else:
                text = sisu.puudulikud_andmed

            label.setText(text)

            return number




class TempBufferLayerNames:
    water_temp_name = 'Ajutine_V'
    sewer_temp_name = 'Ajutine_K'
    prSewer_temp_name = 'Ajutine_KS'
    drainage_temp_name = 'Ajudine_D'
    road_temp_name = 'Ajutine_tee_puver'
    buffer_layer_name = 'puhver_kinnistu'
    spline_layer_name = 'tee_telgjoon'
    buffer_layers = [water_temp_name, sewer_temp_name, prSewer_temp_name, drainage_temp_name, road_temp_name, spline_layer_name, buffer_layer_name]
    
class WorkingLayers:
    water_layer_name = SettingsLoader.get_setting(LayerSettings.WATER_LAYER)        
    sewer_layer_name = SettingsLoader.get_setting(LayerSettings.SEWER_LAYER)        
    prSewer_layer_name = SettingsLoader.get_setting(LayerSettings.PRESSURE_SEWER_LAYER)        
    drainage_layer_name = SettingsLoader.get_setting(LayerSettings.DRAINAGE_LAYER)        

    @staticmethod
    def list_of_workinglayers():
        a = WorkingLayers
        list_of_working_layers = [a.water_layer_name, a.sewer_layer_name, a.prSewer_layer_name, a.drainage_layer_name]
        return list_of_working_layers    

class BufferTools:    
    def generate_buffer_around_selected_item(widget, tempp_buffer_layer, layer_name, style_name=None, checkbox=None, insert_distance = None):
        #print(f"in generator. tempp_buffer_layer: {tempp_buffer_layer}, layer_name: {layer_name}")
        active_layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        
        if active_layer:
            #print("yess")
            # Check if there are any selected features
            if active_layer.selectedFeatureCount() > 0:
                #print("yess 2")
                # Get the selected features
                selected_features = active_layer.selectedFeatures()
                
                # Determine the distance for buffering
                if insert_distance is not None:
                # Convert comma to period if necessary
                   distance = insert_distance.replace(',', '.')

                else:
                    # Calculate distance based on widget value
                    puhver = widget.dPuhvriSuurus.value() / 10
                    distance = round(puhver * 2) / 2

                rounded = None
                if widget.Round_or_Square.isChecked():
                    rounded = 0  # Set to 0 for rounded
                else:
                    rounded = 1  # Set to 0 for square                

                result = processing.run("native:buffer", {
                    'INPUT': QgsProcessingFeatureSourceDefinition(active_layer.source(), True),
                    'DISTANCE': distance,
                    'SEGMENTS': 5,
                    'OUTPUT': 'memory:',
                    'FEATURES': selected_features,
                    'DISSOLVE': False,
                    'END_CAP_STYLE': rounded,
                    'JOIN_STYLE': 0,
                    'MITER_LIMIT': 2,
                })
                
                # Load the QGIS layer style
                if style_name is not None:
                    QGIS_Layer_style = Filepaths().get_style(style_name)
                else:
                    QGIS_Layer_style = None
                    pass

                # Get the group layer name
                group_layer_name = MailablGroupFolders().SANDBOXING

                # Get the group layer or create it if it doesn't exist
                root = QgsProject.instance().layerTreeRoot()
                group = root.findGroup(group_layer_name)
                if group is None:
                    group = root.addGroup(group_layer_name)

                # Check if a layer with the same name already exists
                existing_layers = QgsProject.instance().mapLayersByName(tempp_buffer_layer)
                if existing_layers:
                    # Remove the existing layer before continuing
                    QgsProject.instance().removeMapLayer(existing_layers[0])
                    
                # Add the buffer layer to the group layer
                buffer_layer = QgsProject.instance().addMapLayer(result['OUTPUT'], False)
                buffer_layer.setName(tempp_buffer_layer)
                group.addLayer(buffer_layer)
                
                # Apply the layer style
                if QGIS_Layer_style is not None:
                    buffer_layer.loadNamedStyle(QGIS_Layer_style)
                buffer_layer.triggerRepaint()

            else:
                heading = Headings().infoSimple
                text = HoiatusTexts().kihil_kinnistu_valik
                ModernMessageDialog.Info_messages_modern_REPLACE_WITH_DECISIONMAKER(heading, text)


                if checkbox is not None:
                    checkbox.setChecked(False)
                
        else:
            heading = Headings().warningCritical
            text = HoiatusTexts().puudulik_kinnistute_seadistus
            ModernMessageDialog.Info_messages_modern_REPLACE_WITH_DECISIONMAKER(heading, text)
            if checkbox is not None:
                    checkbox.setChecked(False)
                
class cbMapSelectors:    

    def selectWater_pipes(widget, checkbox):
        #print(f"checkbox: {checkbox}")
        water_layer_name = SettingsLoader.get_setting(LayerSettings.WATER_LAYER)
                
        temp_layer_name = TempBufferLayerNames.water_temp_name
        properties_buffer = TempBufferLayerNames.buffer_layer_name
        
        depth = widget.lblHV.text()
        inner_diameter = widget.lblDeV.text()

        if checkbox.isChecked():
            selected_features = UseQGISNative.select_elements_from_layer(water_layer_name, properties_buffer, widget)
            #diameters, begin_z_coords = UseQGISNative.get_diameter_and_Z(selected_features)

            #print("diameters")
            #print(diameters)

            #print("z_coordinat")
            #print(begin_z_coords)

            style_name = FilesByNames().Easement_Water

            distance = GetRuledRestriction.check_waterworks_rule(inner_diameter, depth)
            #print(f"Applicable restriction: {distance}")

            checkbox.setText(f"Torud ({distance}m)")
            #distance = WaterWorks.vabavoolsed_torustikud_1
            BufferTools.generate_buffer_around_selected_item(widget, temp_layer_name, water_layer_name, style_name, checkbox, distance)
        if not checkbox.isChecked():
            MapCleaners.clear_selection_and_delete_temp_layer(water_layer_name, temp_layer_name)
    
    def selectSewer_pipes(widget, checkbox):
        #print(f"checkbox: {checkbox}")
        sewer_layer_name = SettingsLoader.get_setting(LayerSettings.SEWER_LAYER)        
        temp_layer_name = TempBufferLayerNames.sewer_temp_name
        properties_buffer = TempBufferLayerNames.buffer_layer_name

        depth = widget.lblHK.text()
        inner_diameter = widget.lblDeK.text()

        distance = GetRuledRestriction.check_waterworks_rule(inner_diameter, depth)
        #print(f"Applicable restriction: {distance}")

        checkbox.setText(f"Torud ({distance}m)")


        if checkbox.isChecked():
            UseQGISNative.select_elements_from_layer(sewer_layer_name, properties_buffer, widget)
            style_name = FilesByNames().Easement_sewage
            distance = GetRuledRestriction.check_waterworks_rule(inner_diameter, depth)
            #print(f"Applicable restriction: {distance}")

            #distance = WaterWorks.vabavoolsed_torustikud_1
            BufferTools.generate_buffer_around_selected_item(widget, temp_layer_name, sewer_layer_name, style_name, checkbox, distance)
        if not checkbox.isChecked():
            MapCleaners.clear_selection_and_delete_temp_layer(sewer_layer_name, temp_layer_name)
    
    def selectprSewer_pipes(widget, checkbox):
        #print(f"ccheckbox: {checkbox}")
        prSerer_layer_name = SettingsLoader.get_setting(LayerSettings.PRESSURE_SEWER_LAYER)        
        temp_layer_name = TempBufferLayerNames.prSewer_temp_name
        properties_buffer = TempBufferLayerNames.buffer_layer_name

        depth = widget.lblHK.text()
        inner_diameter = widget.lblDeK.text()

        distance = GetRuledRestriction.check_waterworks_rule(inner_diameter, depth)
        #print(f"Applicable restriction: {distance}")

        checkbox.setText(f"Surve torud ({distance}m)")


        if checkbox.isChecked():
            UseQGISNative.select_elements_from_layer(prSerer_layer_name, properties_buffer, widget)
            style_name = FilesByNames().Easement_prSewage
            #distance = WaterWorks.survetorustik_1
            BufferTools.generate_buffer_around_selected_item(widget, temp_layer_name, prSerer_layer_name, style_name, checkbox, distance)
        if not checkbox.isChecked():
            MapCleaners.clear_selection_and_delete_temp_layer(prSerer_layer_name, temp_layer_name)
    
    def selectDrainage_pipes(widget, checkbox):
        #print(f"ccheckbox: {checkbox}")
        drainage_layer_name = SettingsLoader.get_setting(LayerSettings.DRAINAGE_LAYER)        
        temp_layer_name = TempBufferLayerNames.drainage_temp_name
        properties_buffer = TempBufferLayerNames.buffer_layer_name
    
        depth = widget.lblHK.text()
        inner_diameter = widget.lblDeK.text()

        distance = GetRuledRestriction.check_waterworks_rule(inner_diameter, depth)
        #print(f"Applicable restriction: {distance}")

        checkbox.setText(f"Drenaaž ({distance}m)")


        if checkbox.isChecked():
            UseQGISNative.select_elements_from_layer(drainage_layer_name, properties_buffer, widget)
            style_name = FilesByNames().Easement_Drainage
            #distance = WaterWorks.vabavoolsed_torustikud_1
            BufferTools.generate_buffer_around_selected_item(widget, temp_layer_name, drainage_layer_name, style_name, checkbox, distance)
        if not checkbox.isChecked():
            MapCleaners.clear_selection_and_delete_temp_layer(drainage_layer_name, temp_layer_name)
        
class MapCleaners:
    @staticmethod
    def clear_selection_and_delete_temp_layer(layer_name, temp_layer_name):
      # print(f"temp_layer_name: {temp_layer_name}")
        # Clear the selection when checkbox is unchecked
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if layer:
            layer = layer[0]
            layer.removeSelection()
        else:
            # print(f"layer '{layer_name}' not found.")
            pass
        # Delete the temporary layer
        temp_layer = QgsProject.instance().mapLayersByName(temp_layer_name)
        if temp_layer:
            temp_layer = temp_layer[0]
            QgsProject.instance().removeMapLayer(temp_layer.id())
        else:
            # print(f"Temporary layer '{temp_layer_name}' not found.")
            pass
        iface.mapCanvas().refresh()


    def clearPuhver2m(table):
        layer_name = SettingsLoader.get_setting(LayerSettings.CADASTRAL_CURRENT)
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer:
            layer.removeSelection()
        else:
            # print('No ei ole ju enam olemas!')
            pass
        temp_layer_name = TempBufferLayerNames.buffer_layer_name
        MapCleaners.clear_selection_and_delete_temp_layer(layer_name, temp_layer_name)
        # Clear the model from rows
        model = table.model()
        rowCount = model.rowCount()
        model.removeRows(0, rowCount)
        iface.mapCanvas().refresh()

class GenerateEasement:

    @staticmethod
    def generate_easement(widget):
        #print("started Intersection")
        active_layer_name = SettingsDataSaveAndLoad().load_target_cadastral_name()

        # Slice the lists to include only the first four items
        buffer_layers = TempBufferLayerNames.buffer_layers[:5]
        intersect_layers = TempIntersectLayerName.intersect_layers[:5]
        

        # Create a dictionary to map buffer layers to intersect layers
        layer_mapping = dict(zip(buffer_layers, intersect_layers))
        #print("mapped layers:")
        #print(layer_mapping)
        # Iterate through the buffer layers and perform operations for each
        
        for buffer_layer in buffer_layers:
            intersect_layer = layer_mapping.get(buffer_layer)

            if intersect_layer:  # Check if intersect layer exists
                Intersect.intersect_two_layers(buffer_layer, active_layer_name, intersect_layer)
        
        intersect_layers = QgsProject.instance().mapLayers().values()
        intersect_layer_names = [layer.name() for layer in intersect_layers if layer.name().startswith("Ajutine_intersect_")]
        #print("intersect_layer_names:")
        #print(intersect_layer_names)
        if not intersect_layer_names:
            #print("No intersect layers found.")
            return
        # Check if join layer exists and remove it if present
        existing_layers = QgsProject.instance().mapLayersByName(JoinLayers.join_layer_name)
        if existing_layers:
            for layer in existing_layers:
                if layer:
                    layer = layer[0].id()  # Get the first layer if found
                    QgsProject.instance().removeMapLayer(layer)
                else:
                    #print(f"layer '{layer}' not found.")
                    pass

 
        # Check the number of intersect layers found
        num_intersect_layers = len(intersect_layer_names)
        #print("num_intersect_layers:")
        #print(num_intersect_layers)
        join_layer_name = "Joined_layer"
        while num_intersect_layers >= 1:
            JoinLayers.join_all_layers(intersect_layer_names, num_intersect_layers, join_layer_name)
                # Decrement the number of intersect layers
            num_intersect_layers -= 1
        # Remove buffer and intersect layers from the project
        
        for layer_name in buffer_layers + TempIntersectLayerName.intersect_layers:
            layer = QgsProject.instance().mapLayersByName(layer_name)
            if layer:
                layer = layer[0].id()  # Get the first layer if found
                QgsProject.instance().removeMapLayer(layer)
            else:
                # print(f"layer '{layer_name}' not found.")
                pass


        joined_layers = QgsProject.instance().mapLayers().values()
        joined_layer_names = [layer.name() for layer in joined_layers if layer.name().startswith("Joined_layer")]
        num_join_layers = len(joined_layer_names)
        #print("num_join_layers")
        #print(num_join_layers)
        final_layer_name = "Final_joined"

        while num_join_layers >= 1:
            #print("num_join_layers in loop")
            #print(num_join_layers)
            JoinLayers.join_all_layers(joined_layer_names, num_join_layers, final_layer_name)
                # Decrement the number of intersect layers
            num_join_layers -= 1
        
        joined_layers = QgsProject.instance().mapLayers().values()
        joined_layer_name = [layer.name() for layer in joined_layers if layer.name().startswith(final_layer_name)]
        #print(f"joined_layer_name: {joined_layer_name}")        
        Union.make_unioned_layer(joined_layer_name)

        working_layers = WorkingLayers.list_of_workinglayers() 
        working_layers.append(active_layer_name)
        
        for layer_name in working_layers:          
            layer = QgsProject.instance().mapLayersByName(layer_name)
            if layer:
                layer = layer[0]
                layer.removeSelection()
            else:
                # print(f"layer '{layer_name}' not found.")
                pass

        properties_buffer = TempBufferLayerNames.buffer_layer_name    
        layer = QgsProject.instance().mapLayersByName(properties_buffer)
        if layer:
            layer = layer[0].id()  # Get the first layer if found
            QgsProject.instance().removeMapLayer(layer)
        else:
            # print(f"layer '{layer_name}' not found.")
            pass
        widget.pbprint.setEnabled(True)
        widget.cmbScale.setEnabled(True)
        
        print_prewiew_lineEdist = EasementTools.widget_line_edits(widget)[2]
        EasementTools.enable_UIelements(print_prewiew_lineEdist)

class ComboBoxInputs:
    def add_values_and_set_first(comboBox, values, standard_id):
        # Clear existing items in the combo box
        comboBox.clear()
        # Add items to the combo box
        for value, item_id in values:
            comboBox.addItem(str(value))
            comboBox.setItemData(comboBox.count() - 1, item_id)
        
        # Find the index of the item with the provided standard_id and set it as current
        for index in range(comboBox.count()):
            if comboBox.itemData(index) == standard_id:
                comboBox.setCurrentIndex(index)
                break


class BufferByLine:
    def create_road_center_line(widget):
        temp_spline_layer = TempBufferLayerNames.spline_layer_name
        group_layer_name = MailablGroupFolders().SANDBOXING
        
        # Get the group layer or create it if it doesn't exist
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_layer_name)
        if group is None:
            group = root.addGroup(group_layer_name)

        # Check if the temp_spline_layer exists and remove it if it does
        existing_layers = QgsProject.instance().mapLayersByName(temp_spline_layer)
        if existing_layers:
            for layer in existing_layers:
                QgsProject.instance().removeMapLayer(layer.id())

        # Create the new temp_spline_layer
        project_crs = QgsProject.instance().crs().authid()
        new_layer = QgsVectorLayer(f'LineString?crs={project_crs}', temp_spline_layer, 'memory')

        QgsProject.instance().addMapLayer(new_layer, False)
        
        # Move the new layer to the group layer
        group.insertLayer(0, new_layer)

        iface.setActiveLayer(new_layer)
        # Activate the temp_spline_layer for editing
        if new_layer.isValid():
            new_layer.startEditing()

        # Connect layer signals and store the connection
        BufferByLine.feature_added_connection = new_layer.featureAdded.connect(
            lambda fid: BufferByLine.generate_buffer_after_drawing(widget, fid, group)
        )
        # Activate the Add Feature tool
        iface.actionAddFeature().trigger()

    @staticmethod
    def generate_buffer_after_drawing(widget, fid, group):
        #print("started generate buffer around line with feature id:", fid)
        temp_spline_layer = TempBufferLayerNames.spline_layer_name
        buffer_layer_name = TempBufferLayerNames.road_temp_name

        style_road = FilesByNames().Easement_Road

        # Get the spline layer
        spline_layer = QgsProject.instance().mapLayersByName(temp_spline_layer)[0]
        if spline_layer:
            # Disconnect the signal before committing changes
            try:
                spline_layer.featureAdded.disconnect(BufferByLine.feature_added_connection)
            except TypeError:
                print("Signal was already disconnected.")

            # Stop editing and save changes
            if spline_layer.isEditable():
                spline_layer.commitChanges()
                print("Editing stopped and changes saved.")

            # Select all features in the layer
            spline_layer.selectAll()
            print(f"Selected {spline_layer.selectedFeatureCount()} features.")

            # Generate buffer around the selected item
            BufferTools.generate_buffer_around_selected_item(widget, buffer_layer_name, temp_spline_layer, style_name=style_road)
            

        else:
            print("Layer missing")
            pass