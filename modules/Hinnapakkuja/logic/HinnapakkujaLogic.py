"""
Business logic for Hinnapakkuja module: handles calculation of nodes, materials, and price aggregation.
"""
from typing import Dict, Any

class HinnapakkujaLogic:
    @staticmethod
    def calculate_nodes_and_materials(user_input: Dict[str, Any], price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate node quantities, material breakdown, and total price based on user input and price data.
        Returns a dict with all calculation results for rendering.
        """
        import json
        from ....constants.file_paths import DataPaths
        # Load typical nodes definition from centralized constant
        with open(DataPaths.TYPICAL_NODES, 'r', encoding='utf-8') as f:
            node_defs = json.load(f)["nodes"]

        # Calculate quantities based on user input
        apartments = user_input.get("apartments", 1)
        staircases = user_input.get("staircases", 1)
        floors = user_input.get("floors", 1)
        bathrooms = user_input.get("bathrooms", 1)
        separate_wc = user_input.get("separate_wc", False)
        kitchen_water = user_input.get("kitchen_water", False)
        underfloor_heating = user_input.get("underfloor_heating", False)
        heating_zones = user_input.get("heating_zones", 0)
        collector_branches = user_input.get("collector_branches", 0)
        supplier = user_input.get("supplier", "FEB")
        material = user_input.get("material", "PEX")
        reserve = user_input.get("reserve", False)

        # Node quantity logic (simplified for demo)
        nodes = []
        total = 0
        for node in node_defs:
            node_name = node["name"]
            node_qty = 0
            if node_name == "Korteri veeühendus (külm + soe)":
                node_qty = apartments
            elif node_name == "Kanalisatsioonisõlm (köök, wc, vannituba)":
                node_qty = apartments * (bathrooms + (1 if kitchen_water else 0) + (1 if separate_wc else 0))
            elif node_name == "Püstikud ja arvestid":
                node_qty = staircases * floors
            elif node_name == "Põrandaküttetorustik":
                node_qty = apartments if underfloor_heating else 0
            elif node_name == "Jaotuskollektor":
                node_qty = heating_zones if underfloor_heating else 0
            if node_qty == 0:
                continue
            # Calculate components
            components = []
            for comp in node["components"]:
                comp_name = comp["name"]
                if "default_length" in comp:
                    qty = comp["default_length"] * node_qty
                    unit = comp["unit"]
                elif "default_count" in comp:
                    qty = comp["default_count"] * node_qty
                    unit = comp["unit"]
                else:
                    qty = node_qty
                    unit = comp.get("unit", "tk")
                # Add 10% reserve if needed
                if reserve:
                    qty = round(qty * 1.1, 2)
                # Price lookup (mock: only for pipes by material)
                price_per_unit = 0
                if "toru" in comp_name.lower() or "küttetoru" in comp_name.lower():
                    price_per_unit = price_data.get(supplier, {}).get(material, 0)
                comp_total = round(qty * price_per_unit, 2)
                total += comp_total
                components.append({
                    "name": comp_name,
                    "qty": qty,
                    "unit": unit,
                    "price_per_unit": price_per_unit,
                    "total": comp_total
                })
            nodes.append({
                "name": node_name,
                "qty": node_qty,
                "components": components
            })
        return {
            "summary": user_input,
            "nodes": nodes,
            "total": round(total, 2),
            "supplier": supplier
        }

    @staticmethod
    def get_mock_price_data() -> Dict[str, Any]:
        """
        Return mock price data for FEB, Tekamerk, Onninen.
        """
        return {
            "FEB": {"PEX": 2.5, "PE": 2.0, "Multilayer": 3.0},
            "Tekamerk": {"PEX": 2.6, "PE": 2.1, "Multilayer": 3.1},
            "Onninen": {"PEX": 2.7, "PE": 2.2, "Multilayer": 3.2}
        }
