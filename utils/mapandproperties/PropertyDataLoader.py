import re
import datetime

from ...utils.MapTools.MapHelpers import MapHelpers
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...constants.cadastral_fields import Katastriyksus, AreaUnit
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from qgis.core import QgsFeatureRequest, QgsRectangle, QgsVariantUtils
from PyQt5.QtCore import QCoreApplication
from ...widgets.DateHelpers import DateHelpers
from .property_row_builder import PropertyRowBuilder
from ...Logs.python_fail_logger import PythonFailLogger


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
            msg = self.lang_manager.translate(TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND).format(
                field_name=field_name
            )
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
    def _sql_quote(value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        v = str(value).replace("'", "''").strip()
        return f"'{v}'"

    @staticmethod
    def _eq_expr(field, value):
        """Turvaline = avaldis (tringid ülakomadega, ülakomade escape)."""
        if value is None:
            # mitte kunagi ei sobi, tagastame false avaldise
            return 'FALSE'
        return f'"{field}" = {PropertyDataLoader._sql_quote(value)}'

    @staticmethod
    def _in_expr(field, values):
        cleaned = [str(v).strip() for v in (values or []) if v is not None and str(v).strip()]
        if not cleaned:
            return 'FALSE'
        if len(cleaned) == 1:
            return PropertyDataLoader._eq_expr(field, cleaned[0])
        literals = ",".join(PropertyDataLoader._sql_quote(v) for v in cleaned)
        return f'"{field}" IN ({literals})'

    @staticmethod
    def _and(*parts):
        clean = [p for p in parts if p and p.upper() != 'FALSE']
        if not clean:
            return None
        return ' AND '.join(f'({p})' for p in clean)

    @staticmethod
    def build_scope_expression(*, county_name=None, municipality_name=None, settlements=None) -> str:
        cleaned_settlements = [str(v).strip() for v in (settlements or []) if str(v).strip()]
        settlement_clause = None
        if cleaned_settlements:
            settlement_clause = PropertyDataLoader._in_expr(Katastriyksus.ay_nimi, cleaned_settlements)

        expression = PropertyDataLoader._and(
            PropertyDataLoader._eq_expr(Katastriyksus.mk_nimi, county_name),
            PropertyDataLoader._eq_expr(Katastriyksus.ov_nimi, municipality_name),
            settlement_clause,
        )
        return expression or ""

    # --- Init --------------------------------------------------------------

    def __init__(self):
        self.lang_manager = LanguageManager()
        self.property_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)


        # väljade nimed (Katastriyksus enum/klass)
        self.tunnus_field = Katastriyksus.tunnus
        self.immo_number_field = Katastriyksus.hkood
        self.county_field = Katastriyksus.mk_nimi
        self.municipality_field = Katastriyksus.ov_nimi
        self.settlement_field = Katastriyksus.ay_nimi
        self.address_field = Katastriyksus.l_aadress
        self.firstr_reg_date_field = Katastriyksus.registr
        self.last_upd_date_field = Katastriyksus.muudet
        self.area_field = Katastriyksus.pindala




        if self.property_layer:
            # kinnita, et väljad on olemas (annab kohe selge vea, mitte hiljem)
            for f in [
                self.county_field, self.municipality_field, self.tunnus_field,
                self.address_field, self.area_field, self.settlement_field,
                self.immo_number_field, self.firstr_reg_date_field, self.last_upd_date_field
            ]:
                self._ensure_field(f)

    # --- Laadijad ----------------------------------------------------------

    @staticmethod
    def read_counties(layer):
        """County names from the layer's distinct-value lookup.

        QGIS answers this inside its own engine instead of a Python loop over every
        feature; on the Estonia file (778 480 units) it takes well under a second, so it
        runs on the GUI thread. Municipalities and settlements load later, per county,
        from the background scope read.
        """
        index = layer.fields().lookupField(Katastriyksus.mk_nimi)
        if index < 0:
            raise ValueError(LanguageManager().translate(TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND).format(
                field_name=Katastriyksus.mk_nimi))
        names = {'' if QgsVariantUtils.isNull(value) else str(value).strip() for value in layer.uniqueValues(index)}
        return sorted(name for name in names if name)

    @staticmethod
    def snapshot_request(source, fields, expression=None):
        indices = [source.fields().lookupField(name) for name in fields]
        if -1 in indices:
            missing = fields[indices.index(-1)]
            raise ValueError(LanguageManager().translate(TranslationKeys.PROPERTY_LAYER_FIELD_NOT_FOUND).format(field_name=missing))
        request = QgsFeatureRequest()
        request.setSubsetOfAttributes(indices)
        if expression:
            request.setFilterExpression(expression)
        return request

    @staticmethod
    def read_location_scope(source, cancelled, scope, include_properties):
        """Build rows, selection IDs and map bounds in one cancellable scan.

        A county-only scope also returns that county's municipality and settlement
        choices from the same pass, so the choices never need a scan of the whole layer.
        """
        county, municipality, settlements = scope
        tree = {} if not municipality and not settlements else None
        expression = PropertyDataLoader.build_scope_expression(
            county_name=county or None, municipality_name=municipality or None, settlements=settlements)
        if not county or not expression:
            raise ValueError('A county is required for a location read')
        fields = [Katastriyksus.mk_nimi, Katastriyksus.ov_nimi, Katastriyksus.ay_nimi]
        if include_properties:
            fields += [Katastriyksus.tunnus, Katastriyksus.l_aadress, Katastriyksus.pindala]
            if source.fields().lookupField(Katastriyksus.muudet) >= 0:
                fields.append(Katastriyksus.muudet)
        request = PropertyDataLoader.snapshot_request(source, fields, expression)
        rows, feature_ids = [], []
        extent = QgsRectangle()
        extent.setNull()
        iterator = source.getFeatures(request)
        try:
            for feature in iterator:
                if cancelled.is_set():
                    return None
                feature_ids.append(feature.id())
                if tree is not None:
                    name, settlement = [
                        '' if QgsVariantUtils.isNull(value) else str(value).strip()
                        for value in (feature.attribute(Katastriyksus.ov_nimi),
                                      feature.attribute(Katastriyksus.ay_nimi))
                    ]
                    if name:
                        names = tree.setdefault(name, set())
                        if settlement:
                            names.add(settlement)
                if feature.hasGeometry():
                    extent.combineExtentWith(feature.geometry().boundingBox())
                if include_properties:
                    feature.clearGeometry()
                    rows.append(PropertyRowBuilder.row_from_feature(feature))
        finally:
            iterator.close()
        return {'scope': scope, 'rows': rows, 'feature_ids': feature_ids, 'extent': extent,
                'include_properties': include_properties,
                'tree': None if tree is None else {name: sorted(values) for name, values in tree.items()}}

    # A house number: digits, an optional single letter, and further parts after / or -.
    _HOUSE_NUMBER = re.compile(r'^\d+[^\W\d_]?(?:[-/]\d+[^\W\d_]?)*$')

    @staticmethod
    def get_address_details_from_street(street):
        """Split a cadastral address into a name and a house number.

        Only a trailing house number is separated; everything else stays in the name,
        including road markers like "L2" and leading road numbers. In Estonian addresses
        `//` joins several equivalent addresses of one object, so such a value is a list,
        not one address, and is never split.
        """

        text = ' '.join(str(street or '').split())
        if text.upper() == 'NULL':
            text = ''

        parts = text.split(' ')
        if '//' not in text and len(parts) > 1 and PropertyDataLoader._HOUSE_NUMBER.match(parts[-1]):
            return {'street': ' '.join(parts[:-1]), 'house': parts[-1]}
        return {'street': text, 'house': ''}



    def prepare_data_for_import_stage1(self, feature):
        """Lae kinnistute andmed impordiks (ilma geomeetriata)."""
        
        street_full = feature.attribute(self.address_field) or ''
        street_data = self.get_address_details_from_street(street_full)
        house_number = street_data.get('house', '')

        first_registration = feature.attribute(self.firstr_reg_date_field)
        print(f"First registration raw value: {first_registration}")
        firest_reg_date_str = DateHelpers().date_to_iso_string(first_registration)

        last_updated = feature.attribute(self.last_upd_date_field)
        print(f"Last updated raw value: {last_updated}")
        last_updated_str = DateHelpers().date_to_iso_string(last_updated)
        
        tunnus = feature.attribute(self.tunnus_field)

        property_data = {
            "immovableNumber": feature.attribute(self.immo_number_field),
            "cadastralUnit": {
                "number": tunnus,
                "firstRegistration": firest_reg_date_str,
                "lastUpdated": last_updated_str
            },
            "address": {
                "street": street_data['street'],
                "houseNumber": house_number, 
                "city": feature.attribute(self.settlement_field),
                "state": feature.attribute(self.municipality_field),
                "county": feature.attribute(self.county_field)
                },    
            "area": {
                "size": feature.attribute(self.area_field),
                "unit": AreaUnit.M
            }
        }
        
        siht_data = propertyUsages.extract_intendedUse_data(feature, num_siht_items=3)

        return property_data, tunnus, siht_data,  last_updated_str
    


class propertyUsages:
    @staticmethod
    def extract_intendedUse_data(feature, num_siht_items: int = 3):
        """Build PropertyIntendedUseInput list from a QgsFeature.

        Mirrors the table-based logic:
        - Reads fields siht1..sihtN and so_prts1..so_prtsN
        - Skips NULL/empty names
        - Coerces percentage to int (fallback 0)
        """

        def _field_exists(fname: str) -> bool:
            try:
                return feature.fields().lookupField(fname) != -1
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="data",
                    event="property_field_lookup_failed",
                )
                return True

        def _to_int(val) -> int:
            if val is None:
                return 0
            # QGIS may return QVariant-like values
            try:
                if hasattr(val, "value"):
                    val = val.value()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="data",
                    event="property_value_unwrap_failed",
                )
            if isinstance(val, bool):
                return int(val)
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                return int(val)
            s = str(val).strip()
            if not s or s.upper() == "NULL":
                return 0
            try:
                return int(s)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="data",
                    event="property_value_parse_int_failed",
                )
                try:
                    return int(float(s.replace(",", ".")))
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="data",
                        event="property_value_parse_float_failed",
                    )
                    return 0

        siht_field_1 = Katastriyksus.siht1
        prts_field_1 = Katastriyksus.so_prts1
        siht_base = str(siht_field_1)[:-1]
        prts_base = str(prts_field_1)[:-1]

        input_data = []
        for i in range(1, int(num_siht_items) + 1):
            siht_name = f"{siht_base}{i}"
            prts_name = f"{prts_base}{i}"

            if not _field_exists(siht_name) or not _field_exists(prts_name):
                continue

            siht_data = feature.attribute(siht_name)
            so_prts_data = feature.attribute(prts_name)

            siht_text = "" if siht_data is None else str(siht_data).strip()
            if not siht_text or siht_text.upper() == "NULL":
                continue

            intended_use = {
                "sortOrder": i,
                "name": siht_text,
                "percentage": _to_int(so_prts_data),
            }
            input_data.append(intended_use)

        return input_data
    

