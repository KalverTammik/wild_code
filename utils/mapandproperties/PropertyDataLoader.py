from ...utils.MapTools.MapHelpers import MapHelpers
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...constants.cadastral_fields import Katastriyksus
from ...languages.language_manager import LanguageManager
from qgis.core import QgsFeatureRequest
from PyQt5.QtCore import QCoreApplication


class PropertyDataLoader:
    """
    Kiirem ja hooldatum andmete laadija kinnistute kihilt.
    - Kasutab filter-avaldisi (ei käi kogu kihti läbi)
    - Loeb ainult vajalikud väljad (NoGeometry + subsetOfAttributes)
    - Kontrollib väljade olemasolu ja käsitleb tühiväärtusi
    """

    # --- Utiliidid ---------------------------------------------------------


    def _ensure_field(self, field_name):
        idx = self.property_layer.fields().lookupField(field_name)
        if idx == -1:
            # kasuta keelemänedžeri tõlget, kui saadaval
            msg = self.lang_manager.translate(
                f"Field '{field_name}' not found on the property layer."
            ) or f"Väli '{field_name}' puudub kinnistute kihil."
            raise ValueError(msg)
        return idx

    def _request(self, fields, expr=None):
        """Koosta ühine FeatureRequest ilma geomeetriata ja ainult vajalike väljadega."""
        req = QgsFeatureRequest()
        req.setFlags(QgsFeatureRequest.NoGeometry)
        # lubame ainult vajalikud väljad (indeksite loetelu)
        idxs = [self._ensure_field(f) for f in fields]
        req.setSubsetOfAttributes(idxs)
        if expr:
            req.setFilterExpression(expr)
        return req

    @staticmethod
    def _eq_expr(field, value):
        """Turvaline = avaldis (tringid ülakomadega, ülakomade escape)."""
        if value is None:
            # mitte kunagi ei sobi, tagastame false avaldise
            return 'FALSE'
        if isinstance(value, (int, float)):
            return f'"{field}" = {value}'
        # escape üksikud jutumärgid
        v = str(value).replace("'", "''").strip()
        return f'"{field}" = \'{v}\''

    @staticmethod
    def _and(*parts):
        clean = [p for p in parts if p and p.upper() != 'FALSE']
        if not clean:
            return None
        return ' AND '.join(f'({p})' for p in clean)

    # --- Init --------------------------------------------------------------

    def __init__(self):
        self.lang_manager = LanguageManager()
        self.property_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)


        # väljade nimed (Katastriyksus enum/klass)
        self.county_field = Katastriyksus.mk_nimi
        self.municipality_field = Katastriyksus.ov_nimi
        self.tunnus_field = Katastriyksus.tunnus
        self.address_field = Katastriyksus.l_aadress
        self.area_field = Katastriyksus.pindala
        self.settlement_field = Katastriyksus.ay_nimi


        if self.property_layer:
            # kinnita, et väljad on olemas (annab kohe selge vea, mitte hiljem)
            for f in [
                self.county_field, self.municipality_field, self.tunnus_field,
                self.address_field, self.area_field, self.settlement_field
            ]:
                self._ensure_field(f)

    # --- Laadijad ----------------------------------------------------------

    def load_counties(self, layer):
        """Tagasta unikaalsed maakonnad."""
        try:
            idx = self._ensure_field(self.county_field)
            # uniqueValues on QGIS-is optimeeritud ja kasutab vajadusel DB poolset DISTINCT-i
            values = layer.uniqueValues(idx)
            counties = {str(v).strip() for v in values if v is not None and str(v).strip()}
            return sorted(counties)
        except Exception as e:
            print(f"Error loading counties: {e}")
            raise

    def load_municipalities_for_county(self, county_name):
        """Tagasta valla/linna nimed valitud maakonnas (unikaalsed, sorditud)."""
        if not self.property_layer:
            return []
        try:
            expr = self._eq_expr(self.county_field, county_name)
            req = self._request([self.county_field, self.municipality_field], expr)
            municipalities = set()
            for feat in self.property_layer.getFeatures(req):
                val = feat.attribute(self.municipality_field)
                if val is not None:
                    s = str(val).strip()
                    if s:
                        municipalities.add(s)
            return sorted(municipalities)
        except Exception as e:
            print(f"Error loading municipalities: {e}")
            raise

    def load_settlements_for_municipality(self, county_name, municipality_name):
        """Tagasta asulad valitud vallas/linnas (unikaalsed, sorditud)."""
        #print(f"DEBUG: load_settlements_for_municipality called with county: {county_name}, municipality: {municipality_name}")
        if not self.property_layer:
            print("DEBUG: No property layer")
            return []
        try:
            expr = self._and(
                self._eq_expr(self.county_field, county_name),
                self._eq_expr(self.municipality_field, municipality_name),
            )
            #print(f"DEBUG: Filter expression: {expr}")
            req = self._request(
                [self.county_field, self.municipality_field, self.settlement_field],
                expr,
            )
            settlements = set()
            count = 0
            for feat in self.property_layer.getFeatures(req):
                val = feat.attribute(self.settlement_field)
                if val is not None:
                    s = str(val).strip()
                    if s:
                        settlements.add(s)
                        count += 1
            #print(f"DEBUG: Found {count} settlement values, unique: {len(settlements)}")
            result = sorted(settlements)
            #print(f"DEBUG: Returning settlements: {result}")
            return result
        except Exception as e:
            print(f"Error loading settlements: {e}")
            raise

    def load_properties_for_municipality(self, county_name, municipality_name):
        """Tagasta objektid valitud vallas/linnas (ilma geomeetriata)."""
        if not self.property_layer:
            return []
        try:
            expr = self._and(
                self._eq_expr(self.county_field, county_name),
                self._eq_expr(self.municipality_field, municipality_name),
            )
            fields = [
                self.tunnus_field,
                self.address_field,
                self.area_field,
                self.settlement_field,
                self.county_field,
                self.municipality_field,
            ]
            req = self._request(fields, expr)

            properties = []
            for i, feat in enumerate(self.property_layer.getFeatures(req), start=1):
                properties.append({
                    'cadastral_id': feat.attribute(self.tunnus_field) or '',
                    'address': feat.attribute(self.address_field) or '',
                    'area': feat.attribute(self.area_field) or '',
                    'settlement': feat.attribute(self.settlement_field) or '',
                    # kui vajad hiljem geomeetriat, tee eraldi päring FID alusel
                    'feature': feat
                })
                if i % 250 == 0:
                    QCoreApplication.processEvents()
            return properties
        except Exception as e:
            print(f"Error loading properties: {e}")
            raise

    def load_properties_for_settlement(self, county_name, municipality_name, settlement_name):

        """Tagasta objektid valitud asulas (ilma geomeetriata)."""
        if not self.property_layer:
            return []
        try:
            expr = self._and(
                self._eq_expr(self.county_field, county_name),
                self._eq_expr(self.municipality_field, municipality_name),
                self._eq_expr(self.settlement_field, settlement_name),
            )
            fields = [
                self.tunnus_field,
                self.address_field,
                self.area_field,
                self.settlement_field,
                self.county_field,
                self.municipality_field,
            ]
            req = self._request(fields, expr)

            properties = []
            for i, feat in enumerate(self.property_layer.getFeatures(req), start=1):
                properties.append({
                    'cadastral_id': feat.attribute(self.tunnus_field) or '',
                    'address': feat.attribute(self.address_field) or '',
                    'area': feat.attribute(self.area_field) or '',
                    'settlement': feat.attribute(self.settlement_field) or '',
                    'feature': feat
                })
                if i % 250 == 0:
                    QCoreApplication.processEvents()
            return properties
        except Exception as e:
            print(f"Error loading properties for settlement: {e}")
            raise

    def prepare_data_for_import_stage1(self, features):
        """Lae kinnistute andmed impordiks (ilma geomeetriata)."""
        properties = []
        for feat in features:
            properties.append({
                self.tunnus_field: feat.attribute(self.tunnus_field) or '',
                self.address_field: feat.attribute(self.address_field) or '',
                self.settlement_field: feat.attribute(self.settlement_field) or '',
                self.county_field: feat.attribute(self.county_field) or '',
                self.municipality_field: feat.attribute(self.municipality_field) or '',
                'feature': feat
            })
        return properties