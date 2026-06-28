"""
Seed the chiefdoms reference table.

Source: SierraLeone-Districts-Chiefdoms.xlsx (167 chiefdoms across 16 districts).
The spreadsheet's district 'Fabala' is normalised to 'Falaba' to match the
district names already seeded by seed_organisations.seed_districts().

Idempotent — skips any chiefdom already present for its district. District IDs
are looked up by district_name from the existing `districts` table (not by the
spreadsheet's own ids), so this stays correct regardless of insert order.

Run from backend/:
    python seed_chiefdoms.py
"""
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub",
).replace("postgresql+asyncpg://", "postgresql://")


# district_name -> [chiefdoms]
# Names corrected to official spellings; the source spreadsheet truncated many at
# 15 chars and used the abbreviation "TMS". District assignments follow the source.
# 'Fabala' normalised to 'Falaba'. Corrections applied (source -> official):
#   Gbanti Kamarank->Gbanti Kamaranka, Gbendembu Ngowa->Gbendembu Ngowahun,
#   Magbaimba Ndorh->Magbaimba Ndorhahun, Wara Wara Bafod->Wara Wara Bafodia,
#   Wara Wara Yagal->Wara Wara Yagala, Dembelia - Sink->Dembelia-Sinkunia,
#   Folosaba Dembel->Folosaba-Dembelia, Mono Sakrim->Mano Sakrim,
#   Panga krim->Panga Krim, Pejeh(Futa peje->Pejeh (Futa Pejeh),
#   Sanda Magbolont->Sanda Magbolontor, Sanda Tendaran->Sanda Tendaren,
#   Bureh Kasseh Ma->Bureh Kasseh Makonteh, TMS->Tinkatupa Makonteh Safroko (TMS).
CHIEFDOMS = {
    'Kailahun': ['Dea', 'Jawie', 'Kissi Kama', 'Kissi Teng', 'Kissi Tongi', 'Kpeje Bongre', 'Kpeje West', 'Luawa', 'Malema', 'Mandu', 'Njaluahun', 'Penguia', 'Upper Bambara', 'Yawei'],
    'Kenema': ['Dama', 'Dodo', 'Gaura', 'Gorama Mende', 'Kandu Leppiama', 'Koya', 'Langrama', 'Lower Bambara', 'Malegohun', 'Niawa', 'Nomo', 'Nongowa', 'Simbaru', 'Small Bo', 'Tunkia', 'Wandor', 'Kenema Town'],
    'Kono': ['Fiama', 'Gbane', 'Gbane Kandor', 'Gbense', 'Gorama Kono', 'Kamara', 'Lei', 'Mafindor', 'Nimikoro', 'Nimiyama', 'Sandor', 'Soa', 'Tankoro', 'Toli', 'Koidu Town'],
    'Bombali': ['Biriwa', 'Bombali Sebora', 'Gbanti Kamaranka', 'Gbendembu Ngowahun', 'Magbaimba Ndorhahun', 'Makari Gbanti', 'Paki Masabong', 'Safroko Limba', 'Makeni Town'],
    'Koinadugu': ['Diang', 'Kasunko', 'Nieni', 'Sengbe', 'Wara Wara Bafodia', 'Wara Wara Yagala'],
    'Tonkolili': ['Gbonkolenken', 'Kafe Simiria', 'Kalansogoia', 'Kholifa Mabang', 'Kholifa Rowala', 'Kunike Barina', 'Kunike', 'Malal Mara', 'Sambaya', 'Tane', 'Yoni'],
    'Falaba': ['Dembelia-Sinkunia', 'Folosaba-Dembelia', 'Mongo', 'Neya', 'Sulima'],
    'Bo': ['Badjia', 'Bagbo', 'Bagbwe (Bagbe)', 'Boama', 'Bumpe Ngao', 'Gbo', 'Jaiama Bongor', 'Kakua', 'Komboya', 'Lugbu', 'Niawa Lenga', 'Selenga', 'Tikonko', 'Valunia', 'Wonde', 'Bo Town'],
    'Bonthe': ['Bendu Cha', 'Bum', 'Dema', 'Imperri', 'Jong', 'Kpanda Kemo', 'Kwamebai Krim', 'Nongoba Bullom', 'Sittia', 'Sogbeni', 'Yawbeko', 'Bonthe Urban'],
    'Moyamba': ['Bagruwa', 'Bumpeh', 'Dasse', 'Fakunya', 'Kagboro', 'Kaiyamba', 'Kamajei', 'Kongbora', 'Kori', 'Kowa', 'Lower Banta', 'Ribbi', 'Timdale', 'Upper Banta'],
    'Pujehun': ['Barri', 'Galliness Perri', 'Kpaka', 'Panga Kabonde', 'Makpele', 'Malen', 'Mano Sakrim', 'Panga Krim', 'Pejeh (Futa Pejeh)', 'Soro Gbema', 'Sowa', 'Yakemu Kpukumu'],
    'Western Area Rural': ['Koya Rural', 'Mountain Rural', 'Waterloo Rural', 'York Rural'],
    'Western Area Urban': ['Central I', 'Central II', 'East I', 'East II', 'East III', 'West I', 'West II', 'West III', 'Tasso Island'],
    'Kambia': ['Bramaia', 'Gbinle Dixing', 'Magbema', 'Mambolo', 'Masungbala', 'Samu', 'Tonko Limba'],
    'Karene': ['Buya Romende', 'Dibia', 'Sanda Magbolontor', 'Libeisaygahun', 'Sanda Loko', 'Sanda Tendaren', 'Sella Limba', 'Tambakha'],
    'Port Loko': ['Bureh Kasseh Makonteh', 'Kaffu Bullom', 'Koya', 'Lokomasama', 'Maforki', 'Marampa', 'Masimera', 'Tinkatupa Makonteh Safroko (TMS)'],
}


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database\n")

    # Map district_name -> id from the existing districts table
    rows = await conn.fetch("SELECT id, district_name FROM districts")
    district_id = {r["district_name"]: r["id"] for r in rows}

    inserted = skipped = missing = 0
    for dname, chiefdoms in CHIEFDOMS.items():
        did = district_id.get(dname)
        if did is None:
            print(f"  !  district not found in DB: {dname!r} — run seed_organisations.py first")
            missing += len(chiefdoms)
            continue
        for cf in chiefdoms:
            exists = await conn.fetchval(
                "SELECT 1 FROM chiefdoms WHERE district_id = $1 AND chiefdom_name = $2",
                did, cf,
            )
            if exists:
                skipped += 1
                continue
            await conn.execute(
                "INSERT INTO chiefdoms (district_id, chiefdom_name) VALUES ($1, $2)",
                did, cf,
            )
            inserted += 1
        print(f"  ✓  {dname}: {len(chiefdoms)} chiefdoms")

    await conn.close()
    print(f"\nDone — {inserted} inserted, {skipped} already present, {missing} skipped (missing district).")


if __name__ == "__main__":
    asyncio.run(main())
