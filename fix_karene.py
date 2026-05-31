"""
Fixes Karene's split geometry in sle_districts_fixed.json.
Karene appears as a MultiPolygon (2 parts) in the HDX source, with a ~9 km
gap bridged by Bombali and Kambia. This script merges the two parts into a
single Polygon using a buffer-union-unbuffer approach, then overwrites
sle_districts_fixed.json.
"""
import json, copy
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

data  = json.load(open("sle_districts_fixed.json"))
fixed = copy.deepcopy(data)

for feature in fixed["features"]:
    if feature["properties"]["NAME_2"] != "Karene":
        continue

    geom = shape(feature["geometry"])
    if geom.geom_type != "MultiPolygon":
        print("Karene is already a single Polygon — no fix needed.")
        break

    parts = list(geom.geoms)
    dist  = parts[0].distance(parts[1])
    buf   = dist * 0.6          # smallest factor that yields a single Polygon

    merged = unary_union([p.buffer(buf) for p in parts]).buffer(-buf * 0.8)

    print(f"Karene: {geom.geom_type} ({len(parts)} parts) → {merged.geom_type}")
    print(f"  Gap was {dist*111:.1f} km  |  area {geom.area:.4f} → {merged.area:.4f} sq-deg")

    feature["geometry"] = mapping(merged)
    break

json.dump(fixed, open("sle_districts_fixed.json", "w"))
print("✓ Saved sle_districts_fixed.json")
