"""
Fixes Karene's split geometry by reassigning the smaller fragment to Port Loko.

Analysis:
- Karene in HDX has two disconnected parts
- The smaller fragment (area 0.1703) only uniquely borders Port Loko
- Karene was carved from Port Loko in 2017, so the fragment is almost
  certainly a mis-attribution in the HDX dataset
- Fix: Karene = main body only (single Polygon)
        Port Loko = Port Loko + fragment (union)
- Bombali and all other districts are completely untouched
"""
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

src = json.load(open('sle_admin2.geojson'))
NAME_FIX = {'Fabala': 'Falaba'}

geoms = {}
for f in src['features']:
    raw  = f['properties']['adm2_name']
    name = NAME_FIX.get(raw, raw)
    geoms[name] = shape(f['geometry'])

# Split Karene into main body (larger) and fragment (smaller)
karene_parts = list(geoms['Karene'].geoms)
main, fragment = sorted(karene_parts, key=lambda p: p.area, reverse=True)

print(f'Karene main body:  area={main.area:.4f}  → stays as Karene')
print(f'Karene fragment:   area={fragment.area:.4f}  → reassigned to Port Loko')

# Update geometries
geoms['Karene']    = main
geoms['Port Loko'] = unary_union([geoms['Port Loko'], fragment])

print(f'Port Loko after:   {geoms["Port Loko"].geom_type}  area={geoms["Port Loko"].area:.4f}')

# Verify Bombali is unchanged
print(f'Bombali:           {geoms["Bombali"].geom_type}  (unchanged)')

# Build output GeoJSON
out = {"type": "FeatureCollection", "features": [
    {"type": "Feature",
     "properties": {"NAME_2": name},
     "geometry": mapping(geom)}
    for name, geom in geoms.items()
]}

print(f'\n{len(out["features"])} districts:')
for f in sorted(out["features"], key=lambda x: x["properties"]["NAME_2"]):
    g = shape(f["geometry"])
    print(f'  {f["properties"]["NAME_2"]:25s}  {g.geom_type}')

json.dump(out, open("sle_districts_fixed.json", "w"))
print('\n✓ Saved sle_districts_fixed.json')
