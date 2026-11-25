"""Characterisation of the easement preview dialog before and after it was split up.

The assertions pin what the dialog did before the split (they were run against the
single-class version first). Only the small adapter below changed with the split: it
names where each rule now lives.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import AreaUnit, Katastriyksus
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.easements import easement_distance_rules as rules
from Kavitro_dev.modules.easements import easement_property_edges as edges
from Kavitro_dev.modules.easements.easement_geometry_form_dialog import EasementGeometryFormDialog
from Kavitro_dev.modules.easements.easement_preview_dialog import EasementPreviewDialog
from Kavitro_dev.utils.project_base_layers import ProjectBaseLayerKeys, ProjectBaseLayersService

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()


# --------------------------------------------------------------------------- adapter
D = EasementPreviewDialog


def _host(**attrs):
    host = D.__new__(D)
    for name, value in attrs.items():
        setattr(host, name, value)
    return host


class Api:
    coerce_number = staticmethod(rules.coerce_number)
    format_distance = staticmethod(rules.format_distance)
    find_field_names = staticmethod(rules.find_field_names)
    normalize_area_unit = staticmethod(edges.normalize_area_unit)
    normalize_currency = staticmethod(edges.normalize_currency)
    calculate_total_amount = staticmethod(edges.calculate_total_amount)
    format_total_amount = staticmethod(edges.format_total_amount)
    property_display_label = staticmethod(edges.property_display_label)
    normalize_property_edge = staticmethod(edges.normalize_property_edge)
    format_area_display = staticmethod(edges.format_area_display)
    format_property_label = staticmethod(edges.format_property_label)

    @staticmethod
    def suggest_distance(*, diameter, depth, is_pressure, default_depth):
        return rules.suggest_distance(diameter=diameter, depth=depth, is_pressure=is_pressure,
                                      default_depth=default_depth)

    @staticmethod
    def row_distance(layer_key, layer, *, default_depth=2.0):
        return rules.row_distance(layer_key, layer, default_depth=default_depth)

    @staticmethod
    def cut_areas(final_layer, property_layer):
        host = _host(_property_layer=property_layer, _property_row_widgets={},
                     _calculated_property_area_sqm={}, _final_area_sqm=0.0)
        host._apply_final_cut_area_calculations(final_layer)
        return host._calculated_property_area_sqm, host._final_area_sqm


# --------------------------------------------------------------------------- helpers
def _layer(geometry_type, fields, rows, *, select=None):
    spec = "&".join(f"field={name}:{kind}" for name, kind in fields)
    layer = QgsVectorLayer(f"{geometry_type}?crs=EPSG:3301&{spec}", "t", "memory")
    features = []
    for row in rows:
        attrs, wkt = (row if isinstance(row, tuple) and len(row) == 2 and isinstance(row[1], str) and row[1][:4].isupper()
                      else (row, None))
        feature = QgsFeature(layer.fields())
        feature.setAttributes(list(attrs))
        if wkt:
            feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    ids = [f.id() for f in layer.getFeatures()]
    layer.selectByIds(ids if select is None else [ids[i] for i in select])
    return layer


# --------------------------------------------------------------------------- distance rules
class NumberAndTextRulesTest(unittest.TestCase):
    def test_coerce_number(self):
        cases = {None: None, 5: 5.0, -3: 3.0, 2.5: 2.5, "1,5 m": 1.5, "DN 300": 300.0,
                 "\xa02,25": 2.25, "abc": None, "": None, "-7.5": 7.5}
        for value, expected in cases.items():
            self.assertEqual(Api.coerce_number(value), expected, value)

    def test_format_distance(self):
        self.assertEqual(Api.format_distance(2.0), "2")
        self.assertEqual(Api.format_distance(2.5), "2.5")
        self.assertEqual(Api.format_distance(30), "30")
        self.assertEqual(Api.format_distance(2.75), "2.8")
        self.assertEqual(Api.format_distance("x"), "x")

    def test_find_field_names_exact_and_partial(self):
        layer = _layer("NoGeometry", [("Läbimõõt, mm", "double"), ("Sügavus (m)", "double"), ("Muu", "string")], [])

        self.assertEqual(Api.find_field_names(layer, rules.DIAMETER_FIELD_CANDIDATES), ["Läbimõõt, mm"])
        self.assertEqual(Api.find_field_names(layer, rules.DEPTH_FIELD_CANDIDATES), ["Sügavus (m)"])
        self.assertEqual(Api.find_field_names(layer, ("Vooluhulk",)), [])
        self.assertEqual(Api.find_field_names(None, ("x",)), [])


class SuggestDistanceTest(unittest.TestCase):
    def _d(self, diameter, depth=None, pressure=False, default_depth=2.0):
        return Api.suggest_distance(diameter=diameter, depth=depth, is_pressure=pressure, default_depth=default_depth)

    def test_pressure_pipes_by_diameter(self):
        self.assertEqual([self._d(d, pressure=True) for d in (200, 249, 250, 499, 500)], [2.0, 2.0, 2.5, 2.5, 3.0])

    def test_gravity_pipes_by_diameter_and_depth(self):
        self.assertEqual(self._d(200, 1.5), 2.0)
        self.assertEqual(self._d(200, 3.0), 2.5)
        self.assertEqual(self._d(500, 2.0), 2.5)
        self.assertEqual(self._d(500, 2.5), 3.0)
        self.assertEqual(self._d(1200, 2.0), 2.5)
        self.assertEqual(self._d(1200, 3.0), 5.0)

    def test_missing_depth_uses_the_buffer_distance(self):
        self.assertEqual(self._d(200, None, default_depth=1.0), 2.0)
        self.assertEqual(self._d(200, None, default_depth=4.0), 2.5)

    def test_no_diameter_no_suggestion(self):
        self.assertIsNone(self._d(None, 3.0))
        self.assertIsNone(self._d(None, pressure=True))


class RowDistanceTest(unittest.TestCase):
    PIPE_FIELDS = [("Läbimõõt", "double"), ("Sügavus", "double"), ("Survetoru", "string")]

    def test_fixed_rows(self):
        for key in (ProjectBaseLayerKeys.SEWAGE_DUMP, ProjectBaseLayerKeys.SEWAGE_PLANT, ProjectBaseLayerKeys.WATER_STATION):
            self.assertEqual(Api.row_distance(key, _layer("Point", [("x", "int")], [])), 30.0)

    def test_pump_rows_by_largest_selected_flow(self):
        small = _layer("Point", [("Vooluhulk", "double")], [[5.0], [10.0]])
        large = _layer("Point", [("Vooluhulk", "double")], [[5.0], [15.0]])
        unselected = _layer("Point", [("Vooluhulk", "double")], [[5.0], [15.0]], select=[0])
        for key in (ProjectBaseLayerKeys.SEWAGE_PUMPING, ProjectBaseLayerKeys.RAIN_PUMP):
            self.assertEqual(Api.row_distance(key, small), 10.0)
            self.assertEqual(Api.row_distance(key, large), 20.0)
            self.assertEqual(Api.row_distance(key, unselected), 10.0)

    def test_pipes_take_the_largest_rule_of_the_selected_features(self):
        layer = _layer("LineString", self.PIPE_FIELDS, [[200, 1.0, ""], [600, 3.0, ""], [1500, 3.0, ""]], select=[0, 1])

        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.WATERPIPES, layer), 3.0)

    def test_pressure_from_the_layer_key_or_the_field(self):
        by_field = _layer("LineString", self.PIPE_FIELDS, [[300, 1.0, "true"]])
        by_key = _layer("LineString", self.PIPE_FIELDS, [[300, 1.0, ""]])

        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.WATERPIPES, by_field), 2.5)
        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.WATERPIPES, by_key), 2.5)  # gravity, depth 1 -> 2.5
        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.PRESSURE_SEWERPIPES,
                                          _layer("LineString", self.PIPE_FIELDS, [[600, 4.0, ""]])), 3.0)
        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.WATERPIPES,
                                          _layer("LineString", self.PIPE_FIELDS, [[600, 4.0, ""]])), 3.0)
        self.assertEqual(Api.row_distance(ProjectBaseLayerKeys.WATERPIPES,
                                          _layer("LineString", self.PIPE_FIELDS, [[1500, 4.0, "1"]])), 3.0)

    def test_no_rule_without_a_diameter(self):
        no_field = _layer("LineString", [("Sügavus", "double")], [[3.0]])
        no_value = _layer("LineString", self.PIPE_FIELDS, [[None, 3.0, ""]])
        nothing_selected = _layer("LineString", self.PIPE_FIELDS, [[300, 3.0, ""]], select=[])

        self.assertIsNone(Api.row_distance(ProjectBaseLayerKeys.SEWERPIPES, no_field))
        self.assertIsNone(Api.row_distance(ProjectBaseLayerKeys.SEWERPIPES, no_value))
        self.assertIsNone(Api.row_distance(ProjectBaseLayerKeys.SEWERPIPES, nothing_selected))
        self.assertIsNone(Api.row_distance(ProjectBaseLayerKeys.SEWERPIPES, None))


# --------------------------------------------------------------------------- property edges
class PropertyEdgeTest(unittest.TestCase):
    def test_display_label(self):
        self.assertEqual(Api.property_display_label("1:2", "Tee 1"), "Tee 1 — 1:2")
        self.assertEqual(Api.property_display_label("1:2", "1:2"), "1:2")
        self.assertEqual(Api.property_display_label("1:2"), "1:2")
        self.assertEqual(Api.property_display_label("", "Tee 1"), "Tee 1")
        self.assertEqual(Api.property_display_label("", ""), "-")

    def test_units_and_currency(self):
        self.assertEqual([Api.normalize_area_unit(v) for v in ("m", "SQM", "h", "x", None)],
                         [AreaUnit.M, AreaUnit.M, AreaUnit.H, AreaUnit.M, AreaUnit.M])
        self.assertEqual([Api.normalize_currency(v) for v in ("usd", None, "", "  ")], ["USD", "EUR", "EUR", "EUR"])

    def test_normalize_full_edge(self):
        edge = {
            "node": {"id": " P1 ", "cadastralUnitNumber": "1:2", "displayAddress": "Tee 1"},
            "area": {"size": "12,5", "unit": "H"},
            "pricePerAreaUnit": {"amount": "3", "currencyCode": "usd"},
            "totalPrice": {"amount": 37.5},
            "isPayable": 1,
            "nextPaymentDate": " 2026-01-01 ",
        }
        self.assertEqual(Api.normalize_property_edge(edge), {
            "id": "P1", "cadastralUnitNumber": "1:2", "displayAddress": "Tee 1", "display": "Tee 1 — 1:2",
            "area": {"size": 12.5, "unit": AreaUnit.H},
            "pricePerAreaUnit": {"amount": 3.0, "currencyCode": "USD"},
            "totalPrice": {"amount": 37.5, "currencyCode": "EUR"},
            "isPayable": True, "nextPaymentDate": "2026-01-01",
        })

    def test_normalize_flat_and_empty_edge(self):
        flat = Api.normalize_property_edge({"id": "P2", "cadastralUnitNumber": "3:4"})
        self.assertEqual((flat["id"], flat["cadastralUnitNumber"], flat["display"]), ("P2", "3:4", "3:4"))
        empty = Api.normalize_property_edge(None)
        self.assertEqual(empty["display"], "-")
        self.assertEqual(empty["area"], {"size": None, "unit": AreaUnit.M})
        self.assertFalse(empty["isPayable"])

    def test_totals(self):
        self.assertEqual(Api.calculate_total_amount(100.0, 2.5), 250.0)
        self.assertIsNone(Api.calculate_total_amount(0.0, 2.5))
        self.assertIsNone(Api.calculate_total_amount(10.0, 0))
        self.assertIsNone(Api.calculate_total_amount(None, 2.0))
        self.assertEqual(Api.format_total_amount(250.0, "EUR"), "250.00 EUR")
        self.assertEqual(Api.format_total_amount(None, "EUR"), "–")

    def test_area_display(self):
        self.assertEqual(Api.format_area_display(1234.567), "1234.57 m²")
        self.assertEqual(Api.format_area_display(12345.0, AreaUnit.H), "1.2345 ha")
        self.assertEqual(Api.format_area_display(-5), "0.00 m²")
        self.assertEqual(Api.format_area_display("x"), "0.00 m²")

    def test_property_label_from_feature_fields(self):
        layer = _layer("NoGeometry", [(Katastriyksus.l_aadress, "string"), (Katastriyksus.ay_nimi, "string")],
                       [["", "Küla"], ["Tee 5", "Küla"]])
        first, second = list(layer.getFeatures())

        self.assertEqual(Api.format_property_label("1:2", first), "Küla — 1:2")
        self.assertEqual(Api.format_property_label("1:2", second), "Tee 5 — 1:2")
        self.assertEqual(Api.format_property_label("1:2"), "1:2")


class CutAreaTest(unittest.TestCase):
    def test_area_of_the_final_cut_on_each_selected_property(self):
        final = _layer("Polygon", [("x", "int")], [([1], "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")])
        properties = _layer("Polygon", [(Katastriyksus.tunnus, "string")], [
            (["A"], "POLYGON((5 0, 20 0, 20 10, 5 10, 5 0))"),     # half of the cut
            (["B"], "POLYGON((50 50, 60 50, 60 60, 50 60, 50 50))"),  # outside
            (["C"], "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"),     # not selected
        ], select=[0, 1])

        areas, total = Api.cut_areas(final, properties)

        self.assertEqual(sorted(areas), ["A", "B"])
        self.assertAlmostEqual(areas["A"], 50.0, places=1)
        self.assertEqual(areas["B"], 0.0)
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_missing_layers_reset_the_areas(self):
        final = _layer("Polygon", [("x", "int")], [([1], "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")])

        self.assertEqual(Api.cut_areas(final, None), ({}, 0.0))
        self.assertEqual(Api.cut_areas(None, final), ({}, 0.0))


# --------------------------------------------------------------------------- dialog behaviour
ITEM = {"id": "E1", "number": "S-1", "name": "Servituut"}


class DialogTest(unittest.TestCase):
    def setUp(self):
        resolve = patch.object(ProjectBaseLayersService, "resolve_layer", return_value=None)
        resolve.start()
        self.addCleanup(resolve.stop)
        self.dialog = EasementPreviewDialog(item_data=ITEM)
        self.addCleanup(self.dialog.deleteLater)

    def _edges(self):
        return [
            {"node": {"id": "P1", "cadastralUnitNumber": "1:1", "displayAddress": "Tee 1"},
             "pricePerAreaUnit": {"amount": 2.0, "currencyCode": "EUR"}, "isPayable": True},
            {"node": {"id": "", "cadastralUnitNumber": "2:2"}},
        ]

    def test_rows_without_layers_say_missing(self):
        missing = self.dialog._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_MISSING)
        self.assertEqual({label.text() for label in self.dialog._row_status_labels.values()}, {missing})
        self.assertEqual(len(self.dialog._row_status_labels), len(D._ROW_KEYS))

    def test_property_rows_follow_the_edges(self):
        self.dialog._set_property_edges(self._edges())

        self.assertEqual(sorted(self.dialog._property_row_widgets), ["1:1", "2:2"])
        self.assertEqual(self.dialog._connected_property_numbers, ["1:1", "2:2"])
        self.assertTrue(self.dialog._save_properties_button.isEnabled())

        self.dialog._set_property_edges([])

        self.assertEqual(self.dialog._property_row_widgets, {})
        self.assertFalse(self.dialog._save_properties_button.isEnabled())

    def test_payloads_carry_the_calculated_area_and_the_price(self):
        self.dialog._set_property_edges(self._edges())
        self.dialog._calculated_property_area_sqm = {"1:1": 100.0}

        payloads, invalid = self.dialog._collect_property_payloads()

        self.assertEqual(invalid, [])
        self.assertEqual(payloads, [
            {"id": "P1", "cadastralUnitNumber": "1:1", "isPayable": True,
             "area": {"size": 100.0, "unit": AreaUnit.M},
             "pricePerAreaUnit": {"amount": 2.0, "currencyCode": "EUR"}},
            {"id": "", "cadastralUnitNumber": "2:2", "isPayable": False},
        ])

    def test_selected_properties_are_merged_without_duplicates(self):
        self.dialog._set_property_edges(self._edges())
        layer = _layer("NoGeometry", [(Katastriyksus.tunnus, "string"), (Katastriyksus.l_aadress, "string")],
                       [["3:3", "Tee 3"]])

        self.dialog._merge_selected_properties_into_editor(["2:2", "3:3", " ", "4:4"], list(layer.getFeatures()))

        self.assertEqual([e["cadastralUnitNumber"] for e in self.dialog._property_edges], ["1:1", "2:2", "3:3", "4:4"])
        edges = {e["cadastralUnitNumber"]: e for e in self.dialog._property_edges}
        self.assertEqual(edges["3:3"]["display"], "Tee 3 — 3:3")
        self.assertEqual(edges["4:4"]["display"], "4:4")
        self.assertEqual(edges["1:1"]["id"], "P1")

    def test_form_values_from_the_edges_and_the_cut(self):
        edges = [{"cadastralUnitNumber": "1:1", "totalPrice": {"amount": "10.5"}},
                 {"cadastralUnitNumber": "2:2", "totalPrice": {"amount": None}},
                 {"cadastralUnitNumber": " ", "totalPrice": {"amount": 4}}]
        self.dialog._final_area_sqm = 123.456

        self.assertEqual(self.dialog._easement_form_initial_values(edges), {
            EasementGeometryFormDialog.FIELD_CADASTRAL: "1:1, 2:2",
            "Kaitsevööndi pindala": 123.46,
            EasementGeometryFormDialog.FIELD_COMPENSATION: 14.5,
        })
        self.dialog._final_area_sqm = 0.0
        self.assertEqual(self.dialog._easement_form_initial_values([]), {})

    def test_no_connected_properties_asks_to_define_them(self):
        self.dialog._set_property_edges([])
        self.dialog._run_connected_property_preview_flow()

        skipped = self.dialog._lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROW_SKIPPED)
        self.assertFalse(self.dialog._define_properties_button.isHidden())
        self.assertEqual({label.text() for label in self.dialog._row_status_labels.values()}, {skipped})
        self.assertEqual(self.dialog._status_label.text(),
                         self.dialog._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT))

    def test_final_cut_without_a_property_layer_does_nothing(self):
        self.dialog._property_layer = None
        self.assertEqual(self.dialog._create_final_cut_preview(), "")

    def test_final_cut_without_previews_is_skipped(self):
        self.dialog._property_layer = _layer("Polygon", [(Katastriyksus.tunnus, "string")], [])

        status = self.dialog._create_final_cut_preview()

        self.assertEqual(status, self.dialog._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_SKIPPED))
        self.assertEqual(self.dialog._final_preview_name, "")

    def test_preview_names(self):
        translate = self.dialog._lang.translate
        self.assertEqual(self.dialog._final_preview_layer_name(),
                         f"{translate(TranslationKeys.PREVIEW_EASEMENT_AREA)} · S-1")
        self.assertEqual(self.dialog._merged_cut_preview_name(),
                         f"{translate(TranslationKeys.PREVIEW_EASEMENT_CUT_MERGE)} · S-1")
        title = translate(TranslationKeys.SETTINGS_BASE_LAYER_WATERPIPES)
        self.assertEqual(self.dialog._preview_name_for(ProjectBaseLayerKeys.WATERPIPES),
                         f"{translate(TranslationKeys.PREVIEW_EASEMENT)} · S-1 · {title}")
        self.assertEqual(self.dialog._cut_preview_name_for(ProjectBaseLayerKeys.WATERPIPES),
                         f"{translate(TranslationKeys.PREVIEW_EASEMENT_CUT)} · S-1 · {title}")

    def test_clear_previews_removes_every_named_preview(self):
        self.dialog._preview_layer_names = {"a", "b"}
        self.dialog._property_preview_name = "p"
        self.dialog._final_preview_name = "f"
        with patch("Kavitro_dev.utils.layers.MemoryLayerResultService.remove_existing", return_value=1) as remove:
            self.dialog._clear_previews()

        self.assertEqual(sorted(c.args[0] for c in remove.call_args_list), ["a", "b", "f", "p"])
        self.assertEqual((self.dialog._preview_layer_names, self.dialog._property_preview_name,
                          self.dialog._final_preview_name), (set(), "", ""))
        self.assertEqual(self.dialog._status_label.text(),
                         self.dialog._lang.translate(TranslationKeys.EASEMENT_PREVIEW_CLEARED).format(count=4))

    def test_distance_change_reruns_automation_only_after_start(self):
        with patch("Kavitro_dev.modules.easements.easement_preview_dialog.QTimer.singleShot") as single_shot:
            self.dialog._on_distance_changed(3.0)
            single_shot.assert_not_called()
            self.dialog._auto_initialized = True
            self.dialog._on_distance_changed(3.0)
            self.dialog._automation_running = True
            self.dialog._on_distance_changed(3.0)
        self.assertEqual(single_shot.call_count, 1)

    def test_row_distance_falls_back_to_the_chosen_buffer(self):
        self.dialog._distance_spin.setValue(7.0)
        pipes = _layer("LineString", [("Läbimõõt", "double"), ("Sügavus", "double")], [[200, 3.0]])

        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.WATERPIPES, None), 7.0)
        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.SEWERPIPES,
                                                             _layer("LineString", [("x", "int")], [[1]])), 7.0)
        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.SEWAGE_DUMP, pipes), 30.0)
        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.WATERPIPES, pipes), 2.5)
        no_depth = _layer("LineString", [("Läbimõõt", "double"), ("Sügavus", "double")], [[200, None]])
        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.WATERPIPES, no_depth), 2.5)
        self.dialog._distance_spin.setValue(1.5)
        self.assertEqual(self.dialog._effective_row_distance(ProjectBaseLayerKeys.WATERPIPES, no_depth), 2.0)

    def test_end_cap_style_follows_the_round_ends_checkbox(self):
        self.assertEqual(self.dialog._buffer_end_cap_style(), 0)
        self.dialog._round_ends_checkbox.setChecked(False)
        self.assertEqual(self.dialog._buffer_end_cap_style(), 1)


if __name__ == "__main__":
    unittest.main()
