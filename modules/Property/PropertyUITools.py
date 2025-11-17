
from ...constants.cadastral_fields import Katastriyksus
from ...languages.translation_keys import TranslationKeys




class PropertyUITools:

    def __init__(self, property_ui):
        self.property_ui = property_ui



    def select_property_from_map(self):
        """Activate map selection tool for property selection."""
        try:
            from qgis.core import QgsProject
            from qgis.utils import iface

            # Find and activate the property layer
            from ...constants.layer_constants import PROPERTY_TAG
            project = QgsProject.instance()
            project_layers = project.mapLayers().values()

            for layer in project_layers:
                if layer.customProperty(PROPERTY_TAG):
                    iface.setActiveLayer(layer)
                    break  # Set the first property-tagged layer as active

            active_layer = iface.activeLayer()
            if not active_layer:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.property_ui,
                    self.property_ui.lang_manager.translate(TranslationKeys.ERROR),
                    "No property layer found."
                )
                return

            # Connect selection changed signal
            self._selection_connection = active_layer.selectionChanged.connect(self._on_selection_changed)

            # Activate selection tool
            iface.actionSelectRectangle().trigger()

            # Emit signal to minimize dialog
            self.property_ui.property_selected_from_map.emit()

        except Exception as e:
            print(f"Error selecting property from map: {e}")
            # Show error message
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.property_ui,
                self.property_ui.lang_manager.translate(TranslationKeys.ERROR),
                f"{self.property_ui.lang_manager.translate(TranslationKeys.ERROR_SELECTING_PROPERTY)}: {str(e)}"
            )

    def _on_selection_changed(self):
        """Handle selection changes during map selection process."""
        try:
            from qgis.utils import iface

            active_layer = iface.activeLayer()
            selected_features = active_layer.selectedFeatures()

            if len(selected_features) == 1:
                # Single feature selected: update display
                self.update_property_display(active_layer)

                # Disconnect the signal
                if hasattr(self, '_selection_connection'):
                    active_layer.selectionChanged.disconnect(self._selection_connection)
                    delattr(self, '_selection_connection')

                # Switch back to pan tool
                iface.actionPan().trigger()

                # Emit completion signal to maximize dialog
                self.property_ui.property_selection_completed.emit()

        except Exception as e:
            print(f"Error in selection changed: {e}")

    def update_property_display(self, active_layer):
        """Update the UI labels with the selected property data."""

        features = active_layer.selectedFeatures()
        if not features:
            return  # No selection
        feature = features[0]  # Use the first (and assumed only) selected feature
        try:
            # Helper function to check if value is not NULL
            def is_not_null(value):
                return (value is not None and
                       str(value).strip() and
                       str(value).upper() != 'NULL')

            # Update katastritunnus label
            katastritunnus = feature.attribute(Katastriyksus.tunnus)
            self.property_ui.lbl_katastritunnus_value.setText(str(katastritunnus) if is_not_null(katastritunnus) else "...")

            # Update address label
            l_address = feature.attribute(Katastriyksus.l_aadress)
            ay_name = feature.attribute(Katastriyksus.ay_nimi)
            mk_name = feature.attribute(Katastriyksus.mk_nimi)
            address_parts = []
            if is_not_null(l_address): address_parts.append(str(l_address))
            if is_not_null(ay_name): address_parts.append(str(ay_name))
            if is_not_null(mk_name): address_parts.append(str(mk_name))
            address = ", ".join(address_parts) if address_parts else "..."
            self.property_ui.lbl_address_value.setText(address)

            # Update area label
            area = feature.attribute(Katastriyksus.pindala)
            self.property_ui.lbl_area_value.setText(str(area) if is_not_null(area) else "0.00")

            # Update sihtotstarve labels (3 separate labels, hide if NULL)
            siht1 = feature.attribute(Katastriyksus.siht1)
            siht2 = feature.attribute(Katastriyksus.siht2)
            siht3 = feature.attribute(Katastriyksus.siht3)
            so_prts1 = feature.attribute(Katastriyksus.so_prts1)
            so_prts2 = feature.attribute(Katastriyksus.so_prts2)
            so_prts3 = feature.attribute(Katastriyksus.so_prts3)

            # Siht 1
            if is_not_null(siht1):
                formatted_siht1 = str(siht1).lower().capitalize()
                percentage1 = f" {so_prts1}%" if is_not_null(so_prts1) else ""
                self.property_ui.lbl_siht1_value.setText(f"{formatted_siht1}{percentage1}")
                self.property_ui.lbl_siht1_label.show()
                self.property_ui.lbl_siht1_value.show()
            else:
                self.property_ui.lbl_siht1_label.hide()
                self.property_ui.lbl_siht1_value.hide()

            # Siht 2
            if is_not_null(siht2):
                formatted_siht2 = str(siht2).lower().capitalize()
                percentage2 = f" {so_prts2}%" if is_not_null(so_prts2) else ""
                self.property_ui.lbl_siht2_value.setText(f"{formatted_siht2}{percentage2}")
                self.property_ui.lbl_siht2_label.show()
                self.property_ui.lbl_siht2_value.show()
            else:
                self.property_ui.lbl_siht2_label.hide()
                self.property_ui.lbl_siht2_value.hide()

            # Siht 3
            if is_not_null(siht3):
                formatted_siht3 = str(siht3).lower().capitalize()
                percentage3 = f" {so_prts3}%" if is_not_null(so_prts3) else ""
                self.property_ui.lbl_siht3_value.setText(f"{formatted_siht3}{percentage3}")
                self.property_ui.lbl_siht3_label.show()
                self.property_ui.lbl_siht3_value.show()
            else:
                self.property_ui.lbl_siht3_label.hide()
                self.property_ui.lbl_siht3_value.hide()

            # Update registr (registration date)
            registr = feature.attribute(Katastriyksus.registr)
            if is_not_null(registr):
                # Format date if it's a QDate or datetime object
                if hasattr(registr, 'toString'):
                    # QDate object
                    formatted_date = registr.toString("dd.MM.yyyy")
                else:
                    # Try to parse as string/date
                    try:
                        from datetime import datetime
                        if isinstance(registr, str):
                            # Assume YYYY-MM-DD format and convert to DD.MM.YYYY
                            date_obj = datetime.fromisoformat(str(registr).split('T')[0])
                            formatted_date = date_obj.strftime("%d.%m.%Y")
                        else:
                            formatted_date = str(registr)
                    except:
                        formatted_date = str(registr)
                self.property_ui.lbl_registr_value.setText(formatted_date)
            else:
                self.property_ui.lbl_registr_value.setText("...")

            # Update muudet (modification date)
            muudet = feature.attribute(Katastriyksus.muudet)
            if is_not_null(muudet):
                # Format date if it's a QDate or datetime object
                if hasattr(muudet, 'toString'):
                    # QDate object
                    formatted_date = muudet.toString("dd.MM.yyyy")
                else:
                    # Try to parse as string/date
                    try:
                        from datetime import datetime
                        if isinstance(muudet, str):
                            # Assume YYYY-MM-DD format and convert to DD.MM.YYYY
                            date_obj = datetime.fromisoformat(str(muudet).split('T')[0])
                            formatted_date = date_obj.strftime("%d.%m.%Y")
                        else:
                            formatted_date = str(muudet)
                    except:
                        formatted_date = str(muudet)
                self.property_ui.lbl_muudet_value.setText(formatted_date)
            else:
                self.property_ui.lbl_muudet_value.setText("...")

            # Update kinnistu (property registry number)
            kinnistu = feature.attribute(Katastriyksus.kinnistu)
            self.property_ui.lbl_kinnistu_value.setText(str(kinnistu) if is_not_null(kinnistu) else "...")

        except Exception as e:
            print(f"Error updating property display: {e}")