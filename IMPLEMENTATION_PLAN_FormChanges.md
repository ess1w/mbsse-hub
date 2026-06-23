# Partner Reporting Form — Implementation Plan

**Date:** 23 June 2026
**Scope:** 9 client-requested amendments to the Partner Reporting Form (frontend + backend + DB migration), with full persistence wired up.
**Branch:** `master` (commits will land here directly).

---

## 0. Current state (what the code does today)

- **Frontend form** (`prototype/src/components/form/ReportingForm.jsx`, ~1,140 lines) is a single 3-page component.
  - Section A–D live on page 1, E–H on page 2, I–M on page 3.
  - Section B uses a **single** `district` dropdown plus `school` + `emisCode` text fields.
  - Sections C/D are a **per-activity repeater** (`activities[]` state) — focus areas, objectives, tactics, type, intervention levels, title, dates.
  - Section E captures ~40 output-indicator numbers **per activity** (`act[key]`).
  - Sections F–M are submission-level (`form` state).
- **Critical gap:** `handleSubmit` only sends *submission-level* fields (project title + Sections F–L + files). **The activities array and every Section E number are silently dropped — they never reach the backend.** The `/submissions/submit-report` endpoint likewise never creates `Activity`, `OutputIndicators`, or `SubmissionLocation` rows.
- **Models:** `Activity` has no district field; `OutputIndicators` is 1:1 per activity, has `teenage_mothers` but no `teenage_fathers`, and stores teachers/officials as flat `*_f`/`*_m` (not per focus area). `Organisation` has a `sla_signed` boolean. `UploadedFile.submission_id` is `NOT NULL`.

Because persistence was never wired up, **the DB tables for activities/indicators are effectively empty in production** — which makes the schema changes below low-risk to migrate.

---

## 1. Change-by-change plan

### #1 — Section B: multi-select District; remove School name + EMIS
- **Frontend:** replace the single `district` `<select>` with a multi-select chip control (same pattern as focus areas). Remove the **School name** and **EMIS code** fields and their state (`school`, `emisCode`). Keep Chiefdom / Community / GPS.
- **State:** `form.district` (string) → `form.districts` (array).
- **DB:** no new columns. Submission-level districts persist as multiple `submission_locations` rows (one per district). `school_name` / `emis_code` columns are left in place but no longer populated (dropping them is deferred — see Risks).
- **API:** add `districts: list[str]` to `SubmissionReportIn`; `submit-report` writes one `SubmissionLocation` per district.

### #2 — Section C: per-activity District (multi-select)
- **Frontend:** add `districts: []` to the `newActivity()` template; render a district multi-chip inside each activity card.
- **DB:** add `activities.districts ARRAY(String)`.
- **API/persistence:** activity payload carries `districts`; `submit-report` saves them.

### #3 — Section C: "Other" focus area → free-text box
- **Frontend:** when an activity's `focusAreas` includes `"8. Other"`, reveal a text input bound to `act.focusAreaOther`.
- **DB:** add `activities.focus_area_other TEXT`.
- **API/persistence:** include `focus_area_other`.

### #4 — Section E available per district (when an activity spans >1 district)
This is the largest change. Section E currently holds ~40 numbers **per activity**; it becomes **per activity × per district**.
- **Data model:** change `OutputIndicators` from 1:1 (PK `activity_id`) to **1:many** keyed by `(activity_id, district_name)`. Add `district_name` column; new composite primary key.
- **Frontend:** inside Section E, when an activity has ≥2 districts, render a district sub-selector (tabs/pills). Indicator inputs read/write `act.byDistrict[district][key]` instead of `act[key]`. With a single district, behaviour is unchanged (one implicit tab).
- **API/persistence:** activity payload sends an array of per-district indicator objects; `submit-report` writes one `OutputIndicators` row per district.
- **Read side:** `SubmissionDetail` / admin review and analytics roll-ups sum across district rows.

### #5 — Section E: add "Teenage fathers reached"
- **DB:** add `output_indicators.teenage_fathers INT DEFAULT 0`.
- **Frontend:** add a `numCard` next to "Teenage mothers reached" in the Disability & vulnerable groups grid.

### #6 — Section E: Teachers & Government officials trained, disaggregated by focus area
"Capture # of male and female teachers trained **in each focus area selected in Section C**" — and the same for Government officials.
- **Data model:** add a child table `training_by_focus_area`:
  `(id, activity_id FK, district_name, focus_area, cadre, female INT, male INT)`
  where `cadre ∈ {teacher, district_official, central_official}`. (Per-district to stay consistent with #4 — see open question Q-A.)
- **Frontend:** under "Teachers / school staff trained" and each Government-officials group, render a Female/Male input row **for each focus area selected for that activity** in Section C. The flat `teachers_f/m`, `district_officials_f/m`, `central_officials_f/m` cards are replaced by the per-focus-area rows (with an auto-summed total).
- **API/persistence:** payload carries the training rows; `submit-report` writes them.

### #7 — Section F title appends the Section A project title
- **Frontend only:** Section F header becomes `Outcome / result snapshot — {form.project}` (omits the dash when project is blank). Trivial.

### #8 — Partner uploads SLA (Word/PDF); Admin reviews & approves
SLA is **org-level**, and `uploaded_files` requires a `submission_id`, so SLA needs its own home.
- **DB:** new table `sla_documents`:
  `(id, org_id FK, uploaded_by, original_filename, stored_key, file_size_bytes, mime_type, storage_url, status ['pending'|'approved'|'rejected'], reviewed_by, reviewed_at, review_notes, created_at)`.
- **Backend:** new endpoints —
  - `POST /organisations/{org_id}/sla` (partner uploads; PDF/DOC/DOCX only),
  - `GET /organisations/{org_id}/sla` (list/download),
  - `PATCH /sla-documents/{id}` (admin approve/reject + notes). On **approve**, set `organisations.sla_signed = True`.
- **Frontend (partner):** SLA upload control on the Partner profile/home (org-level), reusing the existing drop-zone UI. *(Placement — see open question Q-B.)*
- **Frontend (admin):** SLA review with Approve/Reject in the Partner Directory drawer (`PartnerDrawer`/`EditPartnerModal`).

### #9 — Section E label text changes (display only)
Rename the 6 `numRow` labels under "School-level SRGBV prevention mechanisms"; **column names unchanged** (display strings only):
| Current | New |
|---|---|
| # schools with SRGBV reporting protocol | # of schools where we established a SRGBV reporting protocol |
| # schools with SRGBV referral pathway | # of schools where we established a SRGBV referral pathway |
| # schools with a trained SRGBV focal person | # of schools where a SRGBV focal person was trained |
| # schools that held a school-wide SRGBV awareness campaign | # of schools where we held a school-wide SRGBV awareness campaign |
| # schools that held a peer-led SRGBV awareness session | # of schools where we held a peer-led SRGBV awareness session |
| # schools with a designated, student-accessible safe space | # of schools we helped establish a designated, student-accessible safe space |

---

## 2. Database migration (new Alembic revision `0003`)

One revision performs:
1. `activities`: `+ districts ARRAY(String)`, `+ focus_area_other TEXT`.
2. `output_indicators`: `+ teenage_fathers INT DEFAULT 0`; `+ district_name VARCHAR`; drop old PK, add composite PK `(activity_id, district_name)`.
3. `+ training_by_focus_area` table (#6).
4. `+ sla_documents` table (#8).
5. *(Optional, deferred)* drop `submission_locations.school_name` / `emis_code`.

A `downgrade()` will reverse each step. **Applied to Render Postgres by you** (`alembic upgrade head`) after review — I will not run migrations against production.

---

## 3. Files I'll touch

**Backend**
- `app/models/submission.py` (Activity, OutputIndicators, new TrainingByFocusArea)
- `app/models/sla_document.py` (new), `app/models/__init__.py`
- `app/schemas/submission.py` (activity + per-district indicator + training payloads)
- `app/schemas/organisation.py` / new `sla.py`
- `app/api/routes/submissions.py` (wire full persistence in `submit-report`; enrich read views)
- `app/api/routes/organisations.py` (SLA endpoints) or new `sla.py` route
- `alembic/versions/0003_form_amendments.py` (new)

**Frontend**
- `prototype/src/components/form/ReportingForm.jsx` (Sections B, C, E, F)
- `prototype/src/data/formData.js` (if any option lists change)
- `prototype/src/api/client.js` (SLA upload/list/approve; send activities on submit)
- `prototype/src/components/submissions/Submissions.jsx` (display new per-district / per-focus data)
- `prototype/src/components/directory/PartnerDrawer.jsx` + `EditPartnerModal.jsx` (admin SLA review)
- A partner profile/home file for SLA upload (TBD by Q-B)

---

## 4. Open questions before build

- **Q-A (#6 granularity):** Should teacher/official training counts be captured **per district** (nested under each district in Section E, consistent with #4), or **once per activity** regardless of districts? Plan currently assumes per-district.
- **Q-B (#8 placement):** Where should partners upload the SLA — Partner **Profile/Settings**, the **Partner Home** page, or inside the **Reporting Form**? Plan currently assumes Profile/Home (org-level).
- **Q-C (Section B vs C districts):** With districts now also chosen per activity (#2), the submission-level Section B district list becomes partly redundant. Keep both (B = overall coverage, C = per-activity), or derive B automatically from the union of activity districts?

---

## 5. Risks / notes

- **Section E data-entry volume:** activity × district × (focus areas) can produce a lot of inputs. UI will use collapsible district tabs to keep it manageable.
- **Migration on production:** low data-loss risk because activity/indicator tables are currently unpopulated, but the `output_indicators` PK change is the most sensitive step — will be written defensively and reversible.
- **Analytics/exports** (`analytics.py`, `ExportData.jsx`) read indicator fields; will be checked so per-district rows are summed, not double-counted.
- **Demo mode** (`usesDemoData()`) short-circuits submit — new fields will be reflected in demo data shapes where relevant.
