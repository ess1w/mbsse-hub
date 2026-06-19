"""
Loads Sierra Leone district GeoJSON geometries into the districts table.

- Maps GADM name variants to our canonical district names
- Karene (split from Port Loko 2017) and Falaba (split from Koinadugu 2017)
  are not in GADM 4.1; they get approximate geometries derived from their
  parent districts for visualisation purposes.

Run from the MBSSE/ directory:
    python3 load_district_geometry.py
"""
import json, asyncio, asyncpg, os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

# Map GADM NAME_2 → our canonical district_name
NAME_MAP = {
    "PortLoko":    "Port Loko",
    "WesternRural":"Western Area Rural",
    "WesternUrban":"Western Area Urban",
    # identical names — listed for completeness
    "Kailahun": "Kailahun", "Kenema": "Kenema", "Kono": "Kono",
    "Bombali":  "Bombali",  "Kambia": "Kambia",
    "Koinadugu":"Koinadugu","Tonkolili":"Tonkolili",
    "Bo": "Bo", "Bonthe": "Bonthe", "Moyamba": "Moyamba", "Pujehun": "Pujehun",
}

async def main():
    data = json.load(open("sle_districts.json"))
    conn = await asyncpg.connect(DATABASE_URL)

    # Store geometries and collect parent geometries for derived districts
    port_loko_geom = None
    koinadugu_geom  = None

    for feature in data["features"]:
        gadm_name = feature["properties"]["NAME_2"]
        our_name  = NAME_MAP.get(gadm_name)
        if not our_name:
            print(f"  ⚠ No mapping for GADM name: {gadm_name}")
            continue

        geom = json.dumps(feature["geometry"])

        updated = await conn.fetchval(
            "UPDATE districts SET geometry = $1 WHERE district_name = $2 RETURNING id",
            geom, our_name,
        )
        if updated:
            print(f"  ✓ {our_name}")
        else:
            print(f"  ✗ {our_name} — not found in districts table")

        if our_name == "Port Loko":   port_loko_geom  = geom
        if our_name == "Koinadugu":    koinadugu_geom  = geom

    # Karene (carved from Port Loko) and Falaba (carved from Koinadugu)
    # Use parent geometry as a visual placeholder — better than blank
    for district, parent_geom, parent_name in [
        ("Karene",  port_loko_geom,  "Port Loko"),
        ("Falaba",  koinadugu_geom,  "Koinadugu"),
    ]:
        if parent_geom:
            await conn.execute(
                "UPDATE districts SET geometry = $1 WHERE district_name = $2",
                parent_geom, district,
            )
            print(f"  ~ {district} (approximate — uses {parent_name} boundary)")
        else:
            print(f"  ✗ {district} — parent geometry not found")

    # Summary
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM districts WHERE geometry IS NOT NULL"
    )
    print(f"\n✓ {count} of 16 districts have geometry")
    await conn.close()

asyncio.run(main())
