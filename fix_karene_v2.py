"""
Fixes Karene's split geometry cleanly.

Karene has two disconnected parts with a ~9 km gap occupied by Bombali
and Kambia. Strategy:
  1. Buffer-merge the two Karene parts into one polygon
  2. Compute the bridge area (merged minus original Karene)
  3. Subtract the bridge from Bombali and Kambia so there are zero overlaps
  4. Save sle_districts_fixed.json

All other districts are untouched.
"""
import json, copy
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Start fresh from the HDX source
src   = json.load(open('sle_admin2.geojson'))
NAME_FIX = {'Fabala': 'Falaba'}

# Build {canonical_name: shapely_geom} and {canonical_name: feature_index}
geoms   = {}
idx_map = {}
for i, f in enumerate(src['features']):
    raw  = f['properties']['adm2_name']
    name = NAME_FIX.get(raw, raw)
    geoms[name]   = shape(f['geometry'])
    idx_map[name] = i

# ── Step 1: merge the two Karene parts ─────────────────────────────────────
karene = geoms['Karene']
parts  = list(karene.geoms)
dist   = parts[0].distance(parts[1])
buf    = dist * 0.6

merged_karene = unary_union([p.buffer(buf) for p in parts]).buffer(-buf * 0.8)
print(f'Merged Karene: {merged_karene.geom_type}  area={merged_karene.area:.4f}')

# ── Step 2: bridge = area added to Karene ──────────────────────────────────
bridge = merged_karene.difference(karene)
print(f'Bridge area: {bridge.area:.6f} sq-deg  ({bridge.area * 111**2:.1f} km²)')

# ── Step 3: trim bridge from neighbours ────────────────────────────────────
for name in ('Bombali', 'Kambia', 'Port Loko'):
    orig     = geoms[name]
    trimmed  = orig.difference(bridge)
    removed  = orig.area - trimmed.area
    if removed > 1e-8:
        print(f'  Trimmed {name}: removed {removed*111**2:.2f} km²  '
              f'({trimmed.geom_type})')
        geoms[name] = trimmed
    else:
        print(f'  {name}: no change')

geoms['Karene'] = merged_karene

# ── Step 4: rebuild GeoJSON ─────────────────────────────────────────────────
out = {"type": "FeatureCollection", "features": []}
for name in geoms:
    out["features"].append({
        "type": "Feature",
        "properties": {"NAME_2": name},
        "geometry": mapping(geoms[name]),
    })

# Add any districts not touched (they won't be in geoms if they weren't in src)
# (all 16 districts should be covered already)
print(f'\n{len(out["features"])} districts in output:')
for f in sorted(out["features"], key=lambda x: x["properties"]["NAME_2"]):
    g = shape(f["geometry"])
    print(f'  {f["properties"]["NAME_2"]:25s}  {g.geom_type}')

json.dump(out, open("sle_districts_fixed.json", "w"))
print("\n✓ Saved sle_districts_fixed.json")
