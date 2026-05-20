"""
Seeds partner organisations + projects into the database using v3 schema.
Field names match the data dictionary (Sections 5.1-5.2).

Data sourced from: Mapping tool 2025 for SRGBV coordination hub FINAL.xlsx
                   (Safe_School_Partnership_Mapping worksheet, 53 organisations)

Run from backend/ directory:
    python seed_organisations.py

Uses asyncpg directly (no SQLAlchemy) to avoid greenlet dependency.
Docker: docker exec -it mbsse_backend python seed_organisations.py
"""
import asyncio
import os
import uuid
from datetime import date
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")


# ── Focus area label → code ──────────────────────────────────────────────────
_FA_MAP = {
    "1. SRGBV Prevention & Response": "fa1",
    "2. MHPSS":                       "fa2",
    "3. School Governance":            "fa3",
    "4. Life Skills / SRH":            "fa4",
    "5. WASH":                         "fa5",
    "6. Social Norms":                 "fa6",
    "7. Social Protection":            "fa7",
}

# Objective label → code
_OBJ_MAP = {
    "Obj 1": "obj1",
    "Obj 2": "obj2",
    "Obj 3": "obj3",
}


def _fa(labels):
    """Map a list of focus-area labels to deduplicated fa-codes."""
    return list(dict.fromkeys(_FA_MAP.get(l, "fa8") for l in (labels or [])))


def _obj(labels):
    """Map a list of objective labels to deduplicated obj-codes."""
    return list(dict.fromkeys(_OBJ_MAP[l] for l in (labels or []) if l in _OBJ_MAP))


def _dt(s):
    """Parse an ISO date string, returning None if s is None/empty."""
    return date.fromisoformat(s) if s else None


def _org_status(projects):
    """All orgs in the registry are treated as Active partners.
    They appear in the partner directory regardless of whether their
    current project cycle has ended — 'Inactive' is reserved for orgs
    that have formally disengaged from the hub."""
    return "Active"


def _sla_signed(projects):
    """Orgs with at least one recorded project are treated as signed partners."""
    return bool(projects)


# ── Partner data (53 organisations from spreadsheet) ────────────────────────

PARTNERS = [
    {
        "org_name": "Leh Wi Lan",
        "org_type": "CSO",
        "focal_person": "Salaymatu Kamara",
        "email": "salaymatu.kamara@mottmac.com",
        "phone": "076760366",
        "districts": ["Western Area Rural", "Kailahun", "Port Loko", "Bombali", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Improving Safety and Wellbeing of Secondary School Students Through Addressing SRGBV and Improving Knowledge About SRH",
                "start": "2017-05-01", "end": "2027-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Kailahun", "Port Loko", "Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": ["MBSSE"], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Plan International",
        "org_type": "CSO",
        "focal_person": "Alhaji F.K. Daramy",
        "email": "Alhaji.Daramy@plan-international.org",
        "phone": "+23276499067",
        "districts": ["Kailahun", "Western Area Rural", "Western Area Urban", "Koinadugu", "Moyamba", "Port Loko"],
        "objectives": ["Obj 3", "Obj 2", "Obj 1"],
        "focus_areas": ["4. Life Skills / SRH", "1. SRGBV Prevention & Response", "3. School Governance", "6. Social Norms", "7. Social Protection"],
        "projects": [
            {
                "title": "Teacher Training for Inclusive Girls Education (TTIGE) Project",
                "start": "2020-09-20", "end": "2024-11-15",
                "focus_areas": ["1. SRGBV Prevention & Response", "3. School Governance", "6. Social Norms"],
                "districts": ["Kailahun"],
                "budget_usd": None, "gov_counterpart": ["MBSSE", "TSC"], "status": "Closed",
            },
            {
                "title": "SHE LEADS",
                "start": "2021-01-01", "end": "2025-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response", "6. Social Norms"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Moyamba"],
                "budget_usd": 900000.0, "gov_counterpart": ["MGCA"], "status": "Closed",
            },
            {
                "title": "Integrated School Feeding Programme – Phase 3, 4 & 5",
                "start": "2021-01-01", "end": "2025-12-31",
                "focus_areas": ["7. Social Protection"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Kailahun", "Moyamba"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
            {
                "title": "Community Sponsorship Programme",
                "start": None, "end": None,
                "focus_areas": ["7. Social Protection"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Kailahun", "Moyamba"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Promoting Universal Sexual and Reproductive Health and Rights of Vulnerable Adolescents in West Africa",
                "start": "2021-01-01", "end": "2025-12-31",
                "focus_areas": ["4. Life Skills / SRH"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Kailahun", "Moyamba"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Girl Child Network SL",
        "org_type": "CSO",
        "focal_person": None, "email": None, "phone": None,
        "districts": ["Bombali", "Bo"],
        "objectives": ["Obj 3", "Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response", "3. School Governance"],
        "projects": [
            {
                "title": "Strengthening FAHP for the Coordination of FGM Reduction in Sierra Leone, Influencing Zero Tolerance",
                "start": "2025-04-01", "end": "2026-03-01",
                "focus_areas": ["1. SRGBV Prevention & Response", "3. School Governance"],
                "districts": ["Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "ActionAid Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Valerie N. Momoh",
        "email": "Valerie.Mansaray@actionaid.org",
        "phone": "078781416",
        "districts": ["Koinadugu", "Tonkolili", "Bombali", "Pujehun", "Kambia", "Bo", "Western Area Urban", "Bonthe"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["4. Life Skills / SRH", "6. Social Norms", "7. Social Protection"],
        "projects": [
            {
                "title": "Expanding Cross Sectoral Opportunities for the Empowerment of Adolescent Girls and Reduction of Teenage Pregnancy and Child Marriage through Gender-Transformative Engagements and Social Protection (Cash+) Programmes",
                "start": "2024-09-23", "end": "2026-12-31",
                "focus_areas": ["4. Life Skills / SRH", "6. Social Norms", "7. Social Protection"],
                "districts": ["Koinadugu", "Tonkolili", "Bombali", "Pujehun", "Kambia", "Bo"],
                "budget_usd": 1170332.96, "gov_counterpart": ["MSW"], "status": "Active",
            },
            {
                "title": "Action to Empower Marginalised Adolescent Girls",
                "start": "2021-03-01", "end": "2024-03-31",
                "focus_areas": [],
                "districts": ["Western Area Urban", "Bonthe", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "UNICEF",
        "org_type": "UN Agency",
        "focal_person": "Neha Naidu",
        "email": "nnaidu@unicef.org",
        "phone": "072 118 102",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Bombali", "Moyamba", "Pujehun", "Kambia", "Kenema", "Bo"],
        "objectives": ["Obj 2"],
        "focus_areas": ["4. Life Skills / SRH"],
        "projects": [
            {
                "title": "Expanding Cross Sectoral Opportunities for the Empowerment of Adolescent Girls and Reduction of Teenage Pregnancy and Child Marriage through Gender-Transformative Engagements and Social Protection (Cash+) Programmes",
                "start": "2024-10-01", "end": "2026-12-31",
                "focus_areas": ["4. Life Skills / SRH"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Bombali", "Moyamba", "Pujehun", "Kambia", "Kenema", "Bo"],
                "budget_usd": 30000000.0, "gov_counterpart": ["MSW", "MBSSE", "MOH"], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Sightsavers",
        "org_type": "CSO",
        "focal_person": "Steven Kaindaneh",
        "email": "skaindaneh@sightsavers.org",
        "phone": "078-685778",
        "districts": ["Karene"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Safely at School: Reducing Risks of School-Related Gender-Based Violence for Children with Disabilities in Sierra Leone",
                "start": "2024-05-01", "end": "2025-08-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Karene"],
                "budget_usd": 118000.0, "gov_counterpart": ["Karene District Council", "MOGCA", "MBSSE", "MOSW"], "status": "Closed",
            },
            {
                "title": "Safely at School: Reducing Risks of SRGBV for Children with Disabilities (Phase 2)",
                "start": "2024-05-01", "end": "2025-04-01",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Karene"],
                "budget_usd": None, "gov_counterpart": ["MOGCA", "MOSW", "Karene DC"], "status": "Closed",
            },
            {
                "title": "Secondary Education Improvement Programme (“Leh Wi Lan”)",
                "start": "2023-01-01", "end": "2028-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": [],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Innovation for Community Resilience Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Josephine Lansana",
        "email": "icrslcontact@gmail.com",
        "phone": "078031603",
        "districts": ["Western Area Urban"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["4. Life Skills / SRH", "2. MHPSS", "1. SRGBV Prevention & Response", "5. WASH"],
        "projects": [
            {
                "title": "Safe to Learn – Promoting School Learning Safety for Children and Girls",
                "start": "2025-07-01", "end": "2026-06-30",
                "focus_areas": ["1. SRGBV Prevention & Response", "2. MHPSS", "4. Life Skills / SRH", "5. WASH"],
                "districts": ["Western Area Urban"],
                "budget_usd": 15000.0, "gov_counterpart": ["MBSSE"], "status": "Active",
            },
        ],
    },
    {
        "org_name": "BRAC Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Dominic Wadegu",
        "email": "dominic.owadegu@brac.net",
        "phone": "075-157-462",
        "districts": ["Port Loko", "Kailahun", "Pujehun", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Community-Led Two Generation Approach",
                "start": "2023-09-01", "end": "2027-08-01",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Port Loko", "Kailahun", "Pujehun", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Community-Led Two Generation Approach in Sierra Leone",
                "start": "2023-09-01", "end": "2027-08-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Port Loko", "Kailahun", "Pujehun", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Catholic Relief Services",
        "org_type": "CSO",
        "focal_person": "Paul Diouf",
        "email": "paul.diouf@crs.org",
        "phone": "079-500-866",
        "districts": ["Koinadugu", "Falaba"],
        "objectives": ["Obj 2"],
        "focus_areas": ["7. Social Protection"],
        "projects": [
            {
                "title": "McGovern-Dole International Food for Education and Child Nutrition",
                "start": "2022-10-03", "end": "2025-06-30",
                "focus_areas": ["7. Social Protection"],
                "districts": ["Koinadugu", "Falaba"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "EduNations Inc",
        "org_type": "CSO",
        "focal_person": "Isaac (Program Manager)",
        "email": "isaac@edunations.org",
        "phone": "076-110-373",
        "districts": ["Koinadugu", "Port Loko", "Tonkolili", "Bombali", "Karene", "Bo"],
        "objectives": ["Obj 3"],
        "focus_areas": ["3. School Governance"],
        "projects": [
            {
                "title": "Education for All Project",
                "start": "2012-09-03", "end": None,
                "focus_areas": ["3. School Governance"],
                "districts": ["Koinadugu", "Port Loko", "Tonkolili", "Bombali", "Karene", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Street Child of Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Mohamed Sheku Turay",
        "email": "medpapa@streetchild.sl",
        "phone": "076-280-865",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Education for All Project",
                "start": "2022-06-01", "end": "2026-06-01",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Times of Transformation UKAM-6",
                "start": "2024-04-01", "end": "2025-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Koinadugu", "Tonkolili", "Bombali", "Falaba", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Education For All Coalition Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Charles Desmond Kamara",
        "email": "charlesdesmondk@gmail.com",
        "phone": "076957972",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Accelerating CSOs Policy Engagement for Responsive Gender and Special Needs Education",
                "start": None, "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Evangelical Fellowship of Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Jonathan Bambara",
        "email": "Jbambara1976@gmail.com",
        "phone": "076-637-753",
        "districts": ["Bonthe", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "School Safety and Child Welfare Programme",
                "start": "2025-01-01", "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Bonthe", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "World Hope International",
        "org_type": "CSO",
        "focal_person": "Sahr Kpakima",
        "email": "sahr.kpakima@worldhope.org",
        "phone": "076-902-893",
        "districts": ["Western Area Rural", "Western Area Urban", "Tonkolili", "Bombali", "Karene", "Bo"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response", "7. Social Protection"],
        "projects": [
            {
                "title": "Child Sponsorship and Enable the Children",
                "start": "1999-06-01", "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response", "7. Social Protection"],
                "districts": ["Western Area Rural", "Western Area Urban", "Tonkolili", "Bombali", "Karene", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Cotton Tree Foundation Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Umaru Fofanah",
        "email": "umarufofanah@yahoo.com",
        "phone": "076-161-945",
        "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Ensuring Quality Education in Sierra Leone",
                "start": "2025-01-01", "end": "2025-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "CGA Technologies",
        "org_type": "CSO",
        "focal_person": "Muniru Kawa",
        "email": "munirukawa@cgatechnologies.org.uk",
        "phone": "076-539-718",
        "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
        "objectives": ["Obj 2"],
        "focus_areas": ["7. Social Protection"],
        "projects": [
            {
                "title": "Girls In School Initiative",
                "start": "2024-09-01", "end": "2026-12-31",
                "focus_areas": ["7. Social Protection"],
                "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Free Education Project",
        "org_type": "Government",
        "focal_person": None, "email": None, "phone": None,
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
        "objectives": [],
        "focus_areas": [],
        "projects": [
            {
                "title": "Policy, Governance, Accountability and System Administration Component",
                "start": "2020-08-01", "end": "2027-12-31",
                "focus_areas": [],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "UNFPA",
        "org_type": "UN Agency",
        "focal_person": "Niamh Ni Ruairc",
        "email": "orourke@unfpa.org",
        "phone": "030953199",
        "districts": ["Koinadugu", "Kailahun", "Moyamba", "Pujehun", "Falaba", "Kambia"],
        "objectives": [],
        "focus_areas": [],
        "projects": [
            {
                "title": "Global Programme to End Child Marriage",
                "start": "2018-01-01", "end": "2030-12-31",
                "focus_areas": [],
                "districts": ["Koinadugu", "Kailahun", "Moyamba", "Pujehun", "Falaba", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Protecting and Empowering Girls to Reach their Full Potential",
                "start": "2018-01-01", "end": "2030-12-31",
                "focus_areas": [],
                "districts": ["Koinadugu", "Kailahun", "Moyamba", "Pujehun", "Falaba", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Spotlight Initiative",
                "start": "2018-01-01", "end": "2030-12-31",
                "focus_areas": [],
                "districts": ["Koinadugu", "Kailahun", "Moyamba", "Pujehun", "Falaba", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "AVSI Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Tamba Jimmy",
        "email": "Jimmy.tamba@avsi.org",
        "phone": "+23276221629",
        "districts": ["Western Area Urban", "Bombali", "Bo"],
        "objectives": [],
        "focus_areas": [],
        "projects": [
            {
                "title": "Distance Support Project",
                "start": "2025-01-01", "end": "2025-12-31",
                "focus_areas": [],
                "districts": ["Western Area Urban", "Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "The Association of Language and Literacy Educators – Reading Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Alhajie Sallieu Kanu",
        "email": "hajjkanu@yahoo.com",
        "phone": "+23278444902",
        "districts": ["Western Area Urban", "Port Loko", "Kenema", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Teaching and Learning in Fragile Context Project",
                "start": "2022-11-06", "end": "2026-03-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Urban", "Port Loko", "Kenema", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "National Youth Awareness Forum-Sierra Leone",
        "org_type": "CSO",
        "focal_person": "George Abu Foday",
        "email": "gfoday@nyafsl.com",
        "phone": "+23278472578",
        "districts": ["Moyamba", "Pujehun", "Bonthe", "Bo"],
        "objectives": ["Obj 3", "Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response", "3. School Governance"],
        "projects": [
            {
                "title": "Sierra Leone Education Innovation Challenge (SLEIC)",
                "start": "2022-09-01", "end": "2025-08-31",
                "focus_areas": ["3. School Governance", "1. SRGBV Prevention & Response"],
                "districts": ["Moyamba", "Pujehun", "Bonthe", "Bo"],
                "budget_usd": 18000000.0, "gov_counterpart": ["DSTI", "GoSL"], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "ONE GIRL",
        "org_type": "CSO",
        "focal_person": "Sia Mamah Lajaku-Williams",
        "email": "slw@onegirl.org.au",
        "phone": "+23276626450",
        "districts": ["Western Area Rural", "Western Area Urban", "Tonkolili"],
        "objectives": ["Obj 2"],
        "focus_areas": ["4. Life Skills / SRH"],
        "projects": [
            {
                "title": "Girls in School Programme",
                "start": "2023-09-07", "end": "2028-07-30",
                "focus_areas": ["4. Life Skills / SRH"],
                "districts": ["Western Area Rural", "Western Area Urban", "Tonkolili"],
                "budget_usd": 175482.0, "gov_counterpart": ["District Education Offices", "Local School Boards"], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Pikin-To-Pikin Movement",
        "org_type": "CSO",
        "focal_person": "Abdulai Deadehwai Swaray",
        "email": None,
        "phone": "+23276646220",
        "districts": ["Tonkolili", "Kailahun", "Bombali", "Bo"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response", "5. WASH"],
        "projects": [
            {
                "title": "WASH in Schools, Safe Space for Women and Children, Study Group for Slow Learners",
                "start": "2024-01-15", "end": "2028-12-29",
                "focus_areas": ["5. WASH", "1. SRGBV Prevention & Response"],
                "districts": ["Tonkolili", "Kailahun", "Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "The Learning Foundation Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Saio G. Marah",
        "email": "programs@thelearningfoundation-sl.org",
        "phone": "+232 88 630 582",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Tonkolili", "Bonthe", "Falaba", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Improving Reading Skills of Students in Targeted Primary and JSS Schools",
                "start": "2013-09-26", "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Tonkolili", "Bonthe", "Falaba", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Elshadai Foundation SL",
        "org_type": "CSO",
        "focal_person": "Abator Funna & Augustine Moses",
        "email": "Mabintyfunna@gmail.com",
        "phone": "+23278888961",
        "districts": ["Kono"],
        "objectives": ["Obj 2"],
        "focus_areas": ["7. Social Protection"],
        "projects": [
            {
                "title": "National School Feeding Programme",
                "start": None, "end": None,
                "focus_areas": ["7. Social Protection"],
                "districts": ["Kono"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "SOS Children's Villages Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Kargbo Osman",
        "email": "osman.kargbo@sossierraleone.org",
        "phone": "076564086",
        "districts": ["Western Area Urban", "Bombali", "Bo"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["6. Social Norms", "2. MHPSS", "7. Social Protection"],
        "projects": [
            {
                "title": "Safe Home",
                "start": "1975-09-01", "end": None,
                "focus_areas": ["2. MHPSS", "6. Social Norms", "7. Social Protection"],
                "districts": ["Western Area Urban", "Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": ["MOGCA", "MOSW"], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Develop Africa Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Mr Emeka King",
        "email": "emekaking@developafrica.org",
        "phone": "076668416",
        "districts": ["Western Area Rural", "Western Area Urban", "Bombali", "Karene", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Child Friendly Education",
                "start": "2021-01-01", "end": "2031-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Bombali", "Karene", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Restless Development SL",
        "org_type": "CSO",
        "focal_person": "Lesley Garura",
        "email": "lesley@restlessdevelopment.org",
        "phone": "+23274183671",
        "districts": ["Bombali", "Moyamba", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Power Up – Girls Education Initiative",
                "start": "2023-04-04", "end": "2026-03-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Bombali", "Moyamba", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Humanity & Inclusion SL",
        "org_type": "CSO",
        "focal_person": "Yankuba Forbie",
        "email": "y.forbie@hi.org",
        "phone": "+23288028888",
        "districts": ["Port Loko", "Kailahun", "Moyamba", "Karene", "Kenema", "Kono"],
        "objectives": ["Obj 3", "Obj 2", "Obj 1"],
        "focus_areas": ["3. School Governance", "1. SRGBV Prevention & Response", "5. WASH"],
        "projects": [
            {
                "title": "Girls Education Challenge Transition",
                "start": "2017-04-01", "end": "2021-07-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Port Loko", "Kailahun", "Moyamba", "Karene", "Kenema", "Kono"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
            {
                "title": "Global Partnership for Education – Education Sector COVID-19 Response Project",
                "start": "2021-03-01", "end": "2022-04-30",
                "focus_areas": ["1. SRGBV Prevention & Response", "5. WASH", "3. School Governance"],
                "districts": ["Kenema"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Direct Response Development Organisation",
        "org_type": "CSO",
        "focal_person": "Ibrahim B. Kamara",
        "email": "directresponse2012@gmail.com",
        "phone": "+23276647970",
        "districts": ["Kono"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response", "5. WASH"],
        "projects": [
            {
                "title": "School Sanitation and Hygiene Education – Under the Rural WASH Programme",
                "start": "2016-06-20", "end": "2020-08-20",
                "focus_areas": ["5. WASH", "1. SRGBV Prevention & Response"],
                "districts": ["Kono"],
                "budget_usd": None, "gov_counterpart": ["MOSW", "MOGCA"], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Elevating Education Everywhere (E3-SL)",
        "org_type": "CSO",
        "focal_person": "Abdul Kemoh",
        "email": "e3sierraleone2019@gmail.com",
        "phone": "078457378",
        "districts": ["Bo"],
        "objectives": [],
        "focus_areas": [],
        "projects": [
            {
                "title": "Integrated Health for Child Survival",
                "start": "2024-04-01", "end": "2024-06-30",
                "focus_areas": [],
                "districts": ["Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Direct Aid",
        "org_type": "CSO",
        "focal_person": "Haitham Shouman",
        "email": "sierraleone@direct-aid.org",
        "phone": "+23230104736",
        "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Bombali", "Kenema", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Support to Education",
                "start": "2024-09-23", "end": "2025-07-04",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Bombali", "Kenema", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "SEND SIERRA LEONE",
        "org_type": "CSO",
        "focal_person": "Joseph Ayamga",
        "email": "ayamga@sendsierraleone.com",
        "phone": "+23278206853",
        "districts": ["Kailahun", "Kenema", "Kono"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Promoting Equality and Women's Leadership in Education",
                "start": "2022-11-01", "end": "2025-04-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Kailahun", "Kenema", "Kono"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Save the Children SL",
        "org_type": "CSO",
        "focal_person": "Modupe Taiwo",
        "email": "Modupe.Taiwo@savethechildren.org",
        "phone": "+234 80 62234960",
        "districts": ["Kailahun", "Pujehun", "Kenema", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Education Outcomes Fund / Right to be a Child / FOUNDATIONS Projects",
                "start": "2021-07-01", "end": "2027-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Kailahun", "Pujehun", "Kenema", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "ChildFund SL",
        "org_type": "CSO",
        "focal_person": "Bando Marah",
        "email": "bmarah@childfund.org",
        "phone": "+23276416047",
        "districts": ["Western Area Rural", "Western Area Urban"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["2. MHPSS", "1. SRGBV Prevention & Response", "7. Social Protection"],
        "projects": [
            {
                "title": "Increasing Access to Secondary School Education for Out-of-School Girls in Western Area",
                "start": "2023-04-03", "end": "2025-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response", "2. MHPSS", "7. Social Protection"],
                "districts": ["Western Area Rural", "Western Area Urban"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Sierra Leone Opportunities Industrialization Centres (SLOIC)",
        "org_type": "CSO",
        "focal_person": "Mr. Ben Allieu Sei",
        "email": "sloicnationaloffice@yahoo.com",
        "phone": "+232791620",
        "districts": ["Port Loko", "Bombali", "Bonthe", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Vocational Skill Training and Other Support Measures for Young People",
                "start": "2025-02-01", "end": "2028-01-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Port Loko", "Bombali", "Bonthe", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Teach For Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Josephine Saidu",
        "email": "jsaidu@teachforsierraleone.org",
        "phone": "075023677",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Moyamba", "Pujehun", "Falaba", "Karene", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Graduate Leadership Fellowship",
                "start": "2020-01-06", "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Moyamba", "Pujehun", "Falaba", "Karene", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Development Initiative Programme Sierra Leone (DIP-SL)",
        "org_type": "CSO",
        "focal_person": "Hawa Roselyn Siafa",
        "email": "dipsl.hrs@gmail.com",
        "phone": "+23276-635-717",
        "districts": ["Kailahun", "Pujehun", "Bonthe", "Kambia", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "School Enrolment and Safe Learning Environment of Out-of-School Children (OOSC) and Menstrual Hygiene Management",
                "start": "2021-01-10", "end": "2022-07-10",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Kailahun", "Pujehun", "Bonthe", "Kambia", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Imagine Worldwide",
        "org_type": "CSO",
        "focal_person": "Regina Mamidy Yillah",
        "email": "regina.yillah@imagineworldwide.org",
        "phone": "+232 76 582172",
        "districts": ["Western Area Urban", "Port Loko", "Kailahun", "Moyamba", "Bonthe", "Karene", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Digital Foundational Learning Programme",
                "start": "2023-09-01", "end": "2026-04-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Urban", "Port Loko", "Kailahun", "Moyamba", "Bonthe", "Karene", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "EducAid Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Miriam Mason Sesay",
        "email": "miriam@educaid.org.uk",
        "phone": "+44 7766 353908",
        "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Sierra Leone Education Innovation Challenge",
                "start": "2022-09-01", "end": "2025-08-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "OneFamilyPeople SL",
        "org_type": "CSO",
        "focal_person": "Samuel P. O. V Macauley",
        "email": "samuel@onefamilypeople.org",
        "phone": "+23278771859",
        "districts": ["Western Area Rural", "Western Area Urban", "Bombali", "Kambia", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Child Empowerment Programme and Programme for Inclusion and Empowerment",
                "start": "2025-01-01", "end": "2028-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Bombali", "Kambia", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "KNIGHT WOMEN FOUNDATION",
        "org_type": "CSO",
        "focal_person": "Mrs Khadi Jonjo",
        "email": "khadibaihe@gmail.com",
        "phone": "+232 78 515887",
        "districts": ["Tonkolili"],
        "objectives": ["Obj 2"],
        "focus_areas": ["7. Social Protection"],
        "projects": [
            {
                "title": "The National School Feeding Programme",
                "start": "2023-01-02", "end": "2025-06-02",
                "focus_areas": ["7. Social Protection"],
                "districts": ["Tonkolili"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Concern Worldwide SL",
        "org_type": "CSO",
        "focal_person": "Abu Bakarr Koroma",
        "email": "abubakarr.koroma@concern.net",
        "phone": "+23276541170",
        "districts": ["Tonkolili"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Safe Learning Model Programme",
                "start": "2017-01-01", "end": "2022-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Tonkolili"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Christian Hands on Women and Children in Need (CHOWCHIN) Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Mrs Jestina Farma",
        "email": None,
        "phone": "+23276654011",
        "districts": ["Western Area Rural", "Western Area Urban", "Kambia"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Supporting Community Schools through Strengthening Teacher Retention and Providing School Materials to Pupils",
                "start": "2023-01-01", "end": "2027-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Kambia"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Edify Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Rev. Dr. Samuel G.A Kargbo",
        "email": "skargbo@edify.org",
        "phone": "+23276680656",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Bombali", "Kenema", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "School Transformation Programme",
                "start": "2024-10-01", "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Bombali", "Kenema", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Human Capital Development Plus",
        "org_type": "CSO",
        "focal_person": "Madam Finda Koroma",
        "email": "Finda.koroma@hcdplus.com",
        "phone": "+2348140000858",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
        "objectives": ["Obj 2", "Obj 1"],
        "focus_areas": ["4. Life Skills / SRH", "1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Supporting Girl Child Education, Out-of-School Children, and Development of Digital Skills for the Youth",
                "start": "2024-01-05", "end": "2026-01-04",
                "focus_areas": ["1. SRGBV Prevention & Response", "4. Life Skills / SRH"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Tonkolili", "Kailahun", "Bombali", "Moyamba", "Pujehun", "Bonthe", "Falaba", "Kambia", "Karene", "Kenema", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Cambridge Education/SSEIP2",
        "org_type": "CSO",
        "focal_person": "Mathilde Nicolai",
        "email": "mathilde.nicolai@camb-ed.com",
        "phone": None,
        "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kailahun", "Bombali", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "SSEIP2 – Secondary School Education Improvement Programme Phase 2",
                "start": "2023-01-01", "end": "2027-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Port Loko", "Kailahun", "Bombali", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Voluntary Service Overseas",
        "org_type": "CSO",
        "focal_person": "Isha Bangura",
        "email": "isha.bangura@vsoint.org",
        "phone": "+23276648774",
        "districts": ["Western Area Rural", "Western Area Urban", "Kailahun", "Pujehun"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Active Citizenship",
                "start": "2022-04-04", "end": "2025-03-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Kailahun", "Pujehun"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "FAWE Sierra Leone",
        "org_type": "CSO",
        "focal_person": "Joseph Alpha Kamara",
        "email": "jakfawesierraleone.org@outlook.com",
        "phone": "+23276465613",
        "districts": ["Port Loko", "Kambia", "Karene"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Helping Young Women to Become Teachers in Rural Communities / Girls Access to Education (GATE)",
                "start": "2023-03-23", "end": "2026-02-26",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Port Loko", "Kambia", "Karene"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Institute for Development Sierra Leone (IfDSL)",
        "org_type": "CSO",
        "focal_person": "Augustus Osborne",
        "email": "a.osborne@ifdsl.org",
        "phone": "+23279196837",
        "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Kailahun", "Moyamba", "Pujehun"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Radical Inclusion in Education / Rural Girls' Education Initiative / Disability Inclusion for Schools",
                "start": None, "end": None,
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Rural", "Western Area Urban", "Koinadugu", "Port Loko", "Kailahun", "Moyamba", "Pujehun"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "World Vision SL",
        "org_type": "CSO",
        "focal_person": "David Pyne",
        "email": "david_pyne@wvi.org",
        "phone": "+232 78 977 419",
        "districts": ["Koinadugu", "Pujehun", "Bonthe", "Falaba", "Kono", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Unlock Literacy",
                "start": "2006-01-02", "end": "2030-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Koinadugu", "Pujehun", "Bonthe", "Falaba", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "Learning Roots",
                "start": "2022-03-01", "end": "2030-04-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Koinadugu", "Pujehun", "Bonthe", "Falaba", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
            {
                "title": "ProFuturo",
                "start": "2022-09-01", "end": "2025-12-31",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Pujehun", "Bonthe", "Kono", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
    {
        "org_name": "Program for Children",
        "org_type": "CSO",
        "focal_person": "George Fawundu",
        "email": "mannahfawundu@yahoo.com",
        "phone": "076977150",
        "districts": ["Western Area Urban", "Tonkolili", "Moyamba", "Bonthe", "Bo"],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "Working with Children and Families in Need of Education and Social Support",
                "start": "2021-01-01", "end": "2026-04-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": ["Western Area Urban", "Tonkolili", "Moyamba", "Bonthe", "Bo"],
                "budget_usd": None, "gov_counterpart": [], "status": "Active",
            },
        ],
    },
    {
        "org_name": "Education.org",
        "org_type": "CSO",
        "focal_person": "Giulia Di Filippantonio",
        "email": "giulia@education.org",
        "phone": "+23278885136",
        "districts": [],
        "objectives": ["Obj 1"],
        "focus_areas": ["1. SRGBV Prevention & Response"],
        "projects": [
            {
                "title": "LEARRN",
                "start": "2022-10-03", "end": "2025-09-30",
                "focus_areas": ["1. SRGBV Prevention & Response"],
                "districts": [],
                "budget_usd": None, "gov_counterpart": [], "status": "Closed",
            },
        ],
    },
]


# ── Database seeding ──────────────────────────────────────────────────────────

async def seed_districts(conn):
    DISTRICTS = [
        ("East",          "Kailahun"),
        ("East",          "Kenema"),
        ("East",          "Kono"),
        ("North",         "Bombali"),
        ("North",         "Falaba"),
        ("North",         "Koinadugu"),
        ("North",         "Tonkolili"),
        ("North West",    "Kambia"),
        ("North West",    "Karene"),
        ("North West",    "Port Loko"),
        ("South",         "Bo"),
        ("South",         "Bonthe"),
        ("South",         "Moyamba"),
        ("South",         "Pujehun"),
        ("Western Area",  "Western Area Rural"),
        ("Western Area",  "Western Area Urban"),
    ]
    for region, name in DISTRICTS:
        await conn.execute(
            """INSERT INTO districts (region_name, district_name)
               VALUES ($1, $2) ON CONFLICT (district_name) DO NOTHING""",
            region, name,
        )
    print(f"  ✓  Districts seeded ({len(DISTRICTS)} districts)")


async def seed_reporting_period(conn):
    existing = await conn.fetchval("SELECT id FROM reporting_periods WHERE is_active = true")
    if not existing:
        pid = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO reporting_periods (id, label, start_date, end_date, deadline, is_active)
               VALUES ($1, $2, $3, $4, $5, true)""",
            pid, "Jan–Feb 2026",
            date.fromisoformat("2026-01-01"),
            date.fromisoformat("2026-02-28"),
            date.fromisoformat("2026-03-15"),
        )
        print("  ✓  Reporting period Jan–Feb 2026 created")
    else:
        print("  –  Active reporting period already exists")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database\n")

    await seed_districts(conn)
    await seed_reporting_period(conn)

    print(f"\nSeeding {len(PARTNERS)} partner organisations...")
    inserted = 0
    skipped = 0

    for p in PARTNERS:
        existing = await conn.fetchval(
            "SELECT org_id FROM organisations WHERE org_name = $1", p["org_name"]
        )
        if existing:
            print(f"  skip  {p['org_name']} (already exists)")
            skipped += 1
            continue

        org_id = str(uuid.uuid4())
        status     = _org_status(p["projects"])
        sla_signed = _sla_signed(p["projects"])

        await conn.execute(
            """
            INSERT INTO organisations
              (org_id, org_name, org_type, focal_person, email, phone,
               sla_signed, status, districts)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            org_id,
            p["org_name"],
            p["org_type"],
            p.get("focal_person"),
            p.get("email"),
            p.get("phone"),
            sla_signed,
            status,
            p.get("districts", []),
        )

        for proj in p["projects"]:
            proj_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO projects
                  (project_id, org_id, project_title, project_start, project_end,
                   objective, tactic, focus_area,
                   activity_summary, funding_source, budget_usd, budget_currency,
                   gov_counterpart, project_status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                """,
                proj_id, org_id,
                proj["title"],
                _dt(proj.get("start")),
                _dt(proj.get("end")),
                _obj(p.get("objectives", [])),
                [],                               # tactic – not in source data
                _fa(proj.get("focus_areas", [])),
                proj["title"],                    # activity_summary defaults to title
                None,                             # funding_source – not in source data
                proj.get("budget_usd"),
                "USD",
                proj.get("gov_counterpart", []),
                proj.get("status", "Active"),
            )

        n = len(p["projects"])
        print(f"  ✓  {p['org_name']} ({n} project{'s' if n != 1 else ''})")
        inserted += 1

    await conn.close()
    print(f"\nDone — {inserted} organisations inserted, {skipped} skipped.")


if __name__ == "__main__":
    asyncio.run(main())
