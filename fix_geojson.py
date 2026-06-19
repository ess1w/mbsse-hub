"""
Fixes NAME_2 values in the GADM Sierra Leone GeoJSON so they match
our canonical district names in the database. Also adds Karene and
Falaba as approximate features (derived from Port Loko and Koinadugu).
Saves output to sle_districts_fixed.json.
"""
import json, copy

NAME_FIX = {
    "PortLoko":    "Port Loko",
    "WesternRural":"Western Area Rural",
    "WesternUrban":"Western Area Urban",
}

data  = json.load(open("sle_districts.json"))
fixed = copy.deepcopy(data)

port_loko_feature  = None
koinadugu_feature  = None

for feature in fixed["features"]:
    original = feature["properties"]["NAME_2"]
    if original in NAME_FIX:
        feature["properties"]["NAME_2"] = NAME_FIX[original]
    # Capture parent features for derived districts
    if feature["properties"]["NAME_2"] == "Port Loko":
        port_loko_feature = feature
    if feature["properties"]["NAME_2"] == "Koinadugu":
        koinadugu_feature = feature

# Add Karene (carved from Port Loko, 2017) — approximate boundary
if port_loko_feature:
    karene = copy.deepcopy(port_loko_feature)
    karene["properties"]["NAME_2"] = "Karene"
    fixed["features"].append(karene)
    print("~ Karene added (approximate Port Loko boundary)")

# Add Falaba (carved from Koinadugu, 2017) — approximate boundary
if koinadugu_feature:
    falaba = copy.deepcopy(koinadugu_feature)
    falaba["properties"]["NAME_2"] = "Falaba"
    fixed["features"].append(falaba)
    print("~ Falaba added (approximate Koinadugu boundary)")

# Verify names
names = sorted(f["properties"]["NAME_2"] for f in fixed["features"])
print(f"\n{len(names)} districts in fixed GeoJSON:")
for n in names:
    print(f"  {n}")

json.dump(fixed, open("sle_districts_fixed.json", "w"))
print("\n✓ Saved sle_districts_fixed.json")
