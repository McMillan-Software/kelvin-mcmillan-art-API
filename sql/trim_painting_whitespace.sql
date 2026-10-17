-- One-time cleanup: strip trailing whitespace from painting text fields entered via the admin site.
-- New input is stripped by TrimmedStr in data_transfer_objects.py, so this only needs to run once. Safe to re-run.
-- Back up kelvin.db first:  cp kelvin.db kelvin-backup-$(date +%F).db
-- Run with:                 sqlite3 kelvin.db < sql/trim_painting_whitespace.sql
--
-- Trims space, tab, newline, carriage return and non-breaking space.
-- title is UNIQUE: if two titles only differ by trailing whitespace the UPDATE fails and nothing is changed.
-- The first SELECT lists any such clashes so they can be renamed by hand before re-running.

.headers on

SELECT 'title clash' AS problem, id, '[' || title || ']' AS title
FROM paintings
WHERE RTRIM(title, ' ' || char(9) || char(10) || char(13) || char(160)) IN (
    SELECT RTRIM(title, ' ' || char(9) || char(10) || char(13) || char(160))
    FROM paintings
    GROUP BY 1
    HAVING COUNT(*) > 1
);

BEGIN;

UPDATE paintings SET
    title        = RTRIM(title,        ' ' || char(9) || char(10) || char(13) || char(160)),
    location     = RTRIM(location,     ' ' || char(9) || char(10) || char(13) || char(160)),
    gallery_name = RTRIM(gallery_name, ' ' || char(9) || char(10) || char(13) || char(160)),
    gallery_link = RTRIM(gallery_link, ' ' || char(9) || char(10) || char(13) || char(160))
WHERE title        <> RTRIM(title,        ' ' || char(9) || char(10) || char(13) || char(160))
   OR location     <> RTRIM(location,     ' ' || char(9) || char(10) || char(13) || char(160))
   OR gallery_name <> RTRIM(gallery_name, ' ' || char(9) || char(10) || char(13) || char(160))
   OR gallery_link <> RTRIM(gallery_link, ' ' || char(9) || char(10) || char(13) || char(160));

SELECT changes() AS paintings_updated;

COMMIT;
