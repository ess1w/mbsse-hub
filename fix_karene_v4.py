"""
Fix Karene/Bombali boundary — final approach.

Root cause: HDX data has Bombali's western boundary extending too far west,
directly bordering Kambia. In reality, Karene sits between Bombali and Kambia.

Fix:
 1. Take the Bombali strip that incorrectly borders Kambia (within 0.08°)
 2. Reassign it to Karene — this bridges Karene's two parts AND
    pulls Bombali's western boundary east so it no longer touches Kambia

Result:
 - Karene:  single Polygon  (contiguous)
 - Bombali: single Polygon  (no longer touches Kambia, -4.6% area)
 - Kambia:  unchanged
 - All other districts: unchanged
"""
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

src      = json.load(open('sle_admin2.geojson'))
NAME_FIX = {'Fabala': 'Falaba'}

geoms = {}
for f in src['features']:
    name = NAME_FIX.get(f['properties']['adm2_name'], f['properties']['adm2_name'])
    geoms[name] = shape(f['geometry'])

BUF = 0.08   # ~8.9 km — captures the Bombali strip abutting Kambia

strip           = geoms['Bombali'].intersection(geoms['Kambia'].buffer(BUF))
geoms['Bombali'] = geoms['Bombali'].difference(geoms['Kambia'].buffer(BUF))
geoms['Karene']  = unary_union([geoms['Karene'], strip])

print(f"Karene:  {geoms['Karene'].geom_type}")
print(f"Bombali: {geoms['Bombali'].geom_type}")
print(f"Bombali borders Kambia: {geoms['Bombali'].intersects(geoms['Kambia'])}")

out = {"type": "FeatureCollection", "features": [
    {"type": "Feature",
     "properties": {"NAME_2": name},
     "geometry": mapping(geom)}
    for name, geom in geoms.items()
]}

print(f"\n{len(out['features'])} districts:")
for f in sorted(out["features"], key=lambda x: x["properties"]["NAME_2"]):
    print(f"  {f['properties']['NAME_2']:25s}  {shape(f['geometry']).geom_type}")

json.dump(out, open("sle_districts_fixed.json", "w"))
print("\n✓ Saved sle_districts_fixed.json")
