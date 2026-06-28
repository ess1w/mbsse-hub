# Controlled vocabulary & chart label mappings

This is the canonical reference for the coded/controlled values stored in the
database and the human-readable labels used in the Preset dashboards.

**Why codes vs. labels matter:** the Preset charts group directly on the raw
column values in Postgres. The Reporting Form (`prototype/src/components/form/
ReportingForm.jsx`, `handleSubmit`) and the seed scripts both normalise to the
values below so new and existing data chart as a single, clean category. If you
change a stored value here, update the form normalisation, the seeds
(`seed_submissions.py`, `seed_sample_data.py`), and any Preset calculated column
that maps it.

## Objectives — stored in `activities.objectives` (array)

Stored as codes. Preset's **Activities by objective** chart uses a calculated
column `objective_label` to display the descriptive text.

| Code   | Full objective text (form vocab)                                                                                                  | Preset display label (`objective_label`)                          |
|--------|-----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `obj1` | 1. Promote Gender Equitable and Non-Violent Behaviours by Raising Awareness and Addressing Harmful Social Norms Perpetuating SRGBV | Obj 1: Promote Gender Equitable and Non-Violent Behaviours         |
| `obj2` | 2. Strengthen Institutional and Community Capacity to Prevent and Respond to SRGBV                                                 | Obj 2: Strengthen Institutional and Community Capacity            |
| `obj3` | 3. Ensure Sustained Commitment to SRGBV Prevention Through Policy Enforcement and Stakeholder Engagement                           | Ensure Sustained Commitment to SRGBV Prevention                   |

Preset calculated-column SQL (on the dataset behind *Activities by objective*):

```sql
CASE objectives
  WHEN 'obj1' THEN 'Obj 1: Promote Gender Equitable and Non-Violent Behaviours'
  WHEN 'obj2' THEN 'Obj 2: Strengthen Institutional and Community Capacity'
  WHEN 'obj3' THEN 'Ensure Sustained Commitment to SRGBV Prevention'
  ELSE objectives
END
```

## Focus areas — stored in `activities.focus_areas` (array)

Stored as the **label without** the leading `N.` number prefix (matches the seed
data). The form strips the prefix on submit; "8. Other" becomes `Other` and the
free-text detail is stored separately in `activities.focus_area_other`.

| Form option                     | Stored value                  |
|---------------------------------|-------------------------------|
| 1. SRGBV Prevention & Response  | SRGBV Prevention & Response    |
| 2. MHPSS                        | MHPSS                          |
| 3. School Governance            | School Governance              |
| 4. Life Skills / SRH            | Life Skills / SRH              |
| 5. WASH                         | WASH                           |
| 6. Social Norms                 | Social Norms                   |
| 7. Social Protection            | Social Protection              |
| 8. Other                        | Other (+ `focus_area_other`)   |

## Tactics — stored in `activities.tactics` (array)

Stored as codes `tac1`–`tac9`.

| Code   | Tactic text                                          |
|--------|------------------------------------------------------|
| `tac1` | Carry Out Nationwide Media Campaigns                 |
| `tac2` | Strengthen Peer Education Programs                   |
| `tac3` | Conduct School-Based Awareness Campaigns            |
| `tac4` | Strengthen Capacity of School Personnel             |
| `tac5` | Establish Safe and Inclusive Learning Environments  |
| `tac6` | Implement Community-Based Monitoring and Engagement |
| `tac7` | Enforce Policy                                       |
| `tac8` | Strengthen Reporting and Referral Systems           |
| `tac9` | Engage Stakeholders for Sustainability              |

## Districts — stored as plain names

`activities.districts`, `output_indicators.district_name`, and
`submission_locations.district_name` all store the district name verbatim:

Bo, Bombali, Bonthe, Falaba, Kailahun, Kambia, Karene, Kenema, Koinadugu, Kono,
Moyamba, Port Loko, Pujehun, Tonkolili, Western Area Rural, Western Area Urban.

A NULL/empty district charts as **"(unknown)"** in Preset. The form requires a
district per activity (Section C); `backfill_data_consistency.sql` repairs any
legacy rows that predate this.

## Training cadres — stored in `training_by_focus_area.cadre`

`teacher`, `district_official`, `central_official`.
