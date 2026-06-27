"""Helpers for wiring Superset dashboard layout components to chart slices."""

from __future__ import annotations

import uuid
from typing import Any


def fix_layout_parents(position: dict[str, Any]) -> None:
    """Ensure ROW/CHART parent chains include TAB ids (required for rendering)."""
    for key, node in position.items():
        if not isinstance(node, dict) or node.get("type") != "TAB":
            continue
        tab_id = key
        tab_parents = node.get("parents", [])
        for row_id in node.get("children", []):
            row = position.get(row_id)
            if not isinstance(row, dict) or row.get("type") != "ROW":
                continue
            row["parents"] = tab_parents + [tab_id]
            for comp_id in row.get("children", []):
                comp = position.get(comp_id)
                if isinstance(comp, dict) and comp.get("type") == "CHART":
                    comp["parents"] = tab_parents + [tab_id, row_id]


def remap_chart_component(
    position: dict[str, Any], old_key: str, chart_id: int, node: dict[str, Any]
) -> str:
    """Move a CHART node to CHART-{chart_id} and fix ROW child references."""
    new_key = f"CHART-{chart_id}"
    node["id"] = new_key
    node["meta"]["chartId"] = chart_id

    if old_key != new_key:
        for item in position.values():
            if isinstance(item, dict) and item.get("type") == "ROW":
                children = item.get("children", [])
                if old_key in children:
                    item["children"] = [
                        new_key if child == old_key else child for child in children
                    ]
        position.pop(old_key, None)

    position[new_key] = node
    return new_key


def find_tab_id(position: dict[str, Any], label: str) -> str | None:
    for key, node in position.items():
        if not isinstance(node, dict):
            continue
        if node.get("type") == "TAB" and node.get("meta", {}).get("text") == label:
            return key
    return None


def add_chart_to_tab(
    position: dict[str, Any],
    tab_id: str,
    chart_id: int,
    name: str,
    width: int,
    height: int,
) -> str:
    tab_node = position.get(tab_id)
    if not isinstance(tab_node, dict):
        raise ValueError(f"Tab {tab_id} not found in layout")
    tab_parents = tab_node.get("parents", [])
    if not tab_parents:
        raise ValueError(f"Tab {tab_id} has no parents")

    row_id = f"ROW-{uuid.uuid4().hex[:12]}"
    comp_id = f"CHART-{chart_id}"
    position[row_id] = {
        "id": row_id,
        "type": "ROW",
        "parents": tab_parents + [tab_id],
        "children": [comp_id],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }
    position[comp_id] = {
        "id": comp_id,
        "type": "CHART",
        "parents": tab_parents + [tab_id, row_id],
        "children": [],
        "meta": {
            "chartId": chart_id,
            "sliceName": name,
            "uuid": str(uuid.uuid4()),
            "width": width,
            "height": height,
        },
    }
    tab_node.setdefault("children", []).append(row_id)
    return comp_id


def link_chart_by_name(
    position: dict[str, Any],
    name: str,
    chart_id: int,
    tab: str,
    width: int,
    height: int,
) -> str:
    """Ensure a named chart is in the layout with the correct slice id."""
    comp_id = f"CHART-{chart_id}"

    for key, node in list(position.items()):
        if not isinstance(node, dict) or node.get("type") != "CHART":
            continue
        if node.get("meta", {}).get("sliceName") == name:
            return remap_chart_component(position, key, chart_id, node)

    tab_id = find_tab_id(position, tab)
    if tab_id:
        return add_chart_to_tab(position, tab_id, chart_id, name, width, height)

    raise ValueError(f"Tab {tab!r} not found — cannot place chart {name!r}")


def remove_stale_chart_components(
    position: dict[str, Any], names: set[str], valid_ids: set[int]
) -> None:
    """Drop layout CHART nodes for named charts that reference non-existent slice ids."""
    to_delete: list[str] = []
    for key, node in position.items():
        if not isinstance(node, dict) or node.get("type") != "CHART":
            continue
        cid = node.get("meta", {}).get("chartId")
        slice_name = node.get("meta", {}).get("sliceName")
        if slice_name in names and cid not in valid_ids:
            to_delete.append(key)

    for key in to_delete:
        row_key = position[key]["parents"][-1]
        row = position.get(row_key, {})
        if isinstance(row, dict):
            row["children"] = [c for c in row.get("children", []) if c != key]
        del position[key]
