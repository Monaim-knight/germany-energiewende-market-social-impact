-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 03: Load master_panel.csv into master_panel_staging (TEMPLATE)
--
-- Instructions:
-- 1. Replace <PATH_TO_REPO> with the local path to this repository
--    (use forward slashes '/' on Windows/macOS/Linux).
-- 2. Verify line endings: use '\r\n' on Windows-saved CSVs or '\n'
--    on Unix/LF-saved CSVs.
-- 3. Security note on local_infile:
--    MySQL disables LOAD DATA LOCAL INFILE by default to prevent
--    untrusted servers from requesting arbitrary client files.
--    Enable local_infile only for trusted local sessions (e.g.,
--    mysql --local-infile=1, or OPT_LOCAL_INFILE=1 in Workbench),
--    and disable it again when finished. Do NOT disable strict SQL mode.
-- 4. To re-run cleanly on a populated staging table, uncomment the
--    TRUNCATE safeguard below intentionally.
-- ============================================================

USE germany_energiewende;

-- Optional safeguard for re-loading staging (uncomment intentionally):
-- TRUNCATE TABLE germany_energiewende.master_panel_staging;

LOAD DATA LOCAL INFILE
    '<PATH_TO_REPO>/data/processed/master_panel.csv'
INTO TABLE germany_energiewende.master_panel_staging
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;

-- Quick staging row count check (expected: 396)
SELECT COUNT(*) AS staging_rows
FROM germany_energiewende.master_panel_staging;
