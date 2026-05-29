"""
Converts HDX/OCHA sle_admin2.geojson into sle_districts_fixed.json
suitable for Metabase custom map.

- Renames the adm2_name property to NAME_2 (what Metabase expects)
- Fixes the HDX typo: Fabala → Falaba
- Outputs only NAME_2 in properties (clean)

Run from MBSSE/ directory:
    python3 fix_hdx_geojson.py
"""
import json, copy

NAME_FIX = {
    "Fabala": "Falaba",  # HDX typo — our canonical name is Falaba
}

data = json.load(open("sle_admin2.geojson"))
out = {"type": "FeatureCollection", "features": []}

for feature in data["features"]:
    adm2 = feature["properties"]["adm2_name"]
    name = NAME_FIX.get(adm2, adm2)   # fix typo if needed
    out["features"].append({
        "type": "Feature",
        "properties": {"NAME_2": name},
        "geometry": feature["geometry"],
    })

names = sorted(f["properties"]["NAME_2"] for f in out["features"])
print(f"{len(names)} districts:")
for n in names:
    print(f"  {n}")

json.dump(out, open("sle_districts_fixed.json", "w"))
print("\n✓ Saved sle_districts_fixed.json")
