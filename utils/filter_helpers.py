# filter_helpers.py
"""
Utility functions for grouping and filtering logic used in TypeFilterWidget and similar widgets.
"""
from typing import List, Dict

def group_key(label: str) -> str:
    """Prefix before first ' - ' (or whole label if not present)."""
    parts = (label or "").split(" - ", 1)
    return parts[0].strip() if parts else (label or "").strip()

def build_group_map(edges: List[dict]) -> Dict[str, List[str]]:
    """
    Build a mapping: group_name -> [type_ids] from a list of edges.
    Each edge should have a node with 'name' and 'id'.
    """
    groups: Dict[str, List[str]] = {}
    for e in edges:
        n = (e or {}).get("node") or {}
        label = n.get("name") or n.get("id") or "?"
        _id = n.get("id")
        g = group_key(label)
        groups.setdefault(g, []).append(_id)
    return groups
