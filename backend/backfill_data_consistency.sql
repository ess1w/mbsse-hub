-- ============================================================================
-- One-time data-consistency backfill for existing rows
-- ============================================================================
-- Run ONCE against the Render Postgres database (psql or the Render shell):
--     psql "$DATABASE_URL" -f backfill_data_consistency.sql
--
-- It is idempotent — safe to run more than once. It fixes rows that were
-- created before the reporting form started saving canonical values:
--   1. focus_areas stored with a leading "N. " number prefix
--   2. objectives stored as full text instead of obj1/obj2/obj3 codes
--   3. activities / output_indicators / submission_locations missing a district
--      (these chart as "(unknown)") — backfilled from the activity title suffix
--
-- Review the SELECT counts printed at the end to confirm the result.
-- ============================================================================

BEGIN;

-- 1. Strip the "N. " number prefix from each focus area ----------------------
UPDATE activities
SET    focus_areas = ARRAY(
           SELECT regexp_replace(x, '^\s*\d+\.\s*', '')
           FROM   unnest(focus_areas) AS x
       )
WHERE  focus_areas IS NOT NULL
  AND  EXISTS (SELECT 1 FROM unnest(focus_areas) AS x WHERE x ~ '^\s*\d+\.\s*');

-- 2. Map full objective text -> obj1/obj2/obj3 codes -------------------------
UPDATE activities
SET    objectives = ARRAY(
           SELECT CASE
                    WHEN x LIKE '1.%' THEN 'obj1'
                    WHEN x LIKE '2.%' THEN 'obj2'
                    WHEN x LIKE '3.%' THEN 'obj3'
                    ELSE x
                  END
           FROM   unnest(objectives) AS x
       )
WHERE  objectives IS NOT NULL
  AND  EXISTS (SELECT 1 FROM unnest(objectives) AS x WHERE x LIKE '_.%');

-- 3a. Backfill activities.districts from the "… — <District>" title suffix ---
--     (only when the suffix matches a real Sierra Leone district)
UPDATE activities a
SET    districts = ARRAY[trim(split_part(a.activity_title, '—', 2))]
WHERE  (a.districts IS NULL OR cardinality(a.districts) = 0)
  AND  position('—' IN a.activity_title) > 0
  AND  trim(split_part(a.activity_title, '—', 2)) IN (
        'Bo','Bombali','Bonthe','Falaba','Kailahun','Kambia','Karene','Kenema',
        'Koinadugu','Kono','Moyamba','Port Loko','Pujehun','Tonkolili',
        'Western Area Rural','Western Area Urban'
       );

-- 3b. Point each output_indicators row at its activity's district ------------
UPDATE output_indicators oi
SET    district_name = a.districts[1]
FROM   activities a
WHERE  oi.activity_id = a.activity_id
  AND  (oi.district_name IS NULL OR oi.district_name = '')
  AND  a.districts IS NOT NULL
  AND  cardinality(a.districts) >= 1;

-- 3c. Create submission_locations for submissions that have none -------------
INSERT INTO submission_locations (location_id, submission_id, district_name)
SELECT gen_random_uuid(), a.submission_id, d
FROM   (SELECT DISTINCT submission_id, unnest(districts) AS d
        FROM activities
        WHERE districts IS NOT NULL AND cardinality(districts) >= 1) a
WHERE  NOT EXISTS (
           SELECT 1 FROM submission_locations sl
           WHERE sl.submission_id = a.submission_id
       );

-- Verification -------------------------------------------------------------
SELECT 'activities still prefixed'      AS check, count(*) AS rows
FROM   activities WHERE EXISTS (SELECT 1 FROM unnest(focus_areas) x WHERE x ~ '^\s*\d+\.')
UNION ALL
SELECT 'objectives still full-text',    count(*)
FROM   activities WHERE EXISTS (SELECT 1 FROM unnest(objectives) x WHERE x LIKE '_.%')
UNION ALL
SELECT 'output_indicators no district', count(*)
FROM   output_indicators WHERE district_name IS NULL OR district_name = '';

COMMIT;
