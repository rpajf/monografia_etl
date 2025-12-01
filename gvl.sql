-- Update files from DocLib with metadata from .csv files 
-- Step 1: Instantiate object and leave identified asset tags in "SysTagsFound" for step 2
--

with map as (
SELECT
  DISTINCT
  site_display_name,
  site_acronym,
  site_code,
  state
FROM `db_common_lookup_mpc`.`tbl_site_mappings`
),
syslocation_ref_mappings as (
  SELECT * from `db_common_lookup_mpc`.`tbl_ref_syslocation_mappings`
  where Maintenance_Plant_Code = 'R090'
),
tbl_dl_files_timestamps_ref as (
SELECT *,
is_new('tbl_dl_files_timestamps_gvl_v1',lastUpdatedTime) AS isNewFlag
FROM
`db_dl_files_gvl`.`tbl_dl_files_timestamps_gvl`
),
dl as (
  select 
  key,
  lib_no,
  doc_no,
  extension,
  doc_id_no,
  alt_doc_id_no,
  primary_class,
  secondary_class,
  sort_field,
  doc_title,
  created_by,
  modified_by,
  lib_name,
  unit_no,
  create_date,
  modified_date,
  CONCAT(
    CAST(lib_no AS STRING),
    ".",
    CAST(doc_no AS STRING),
    ".",
    CASE
      WHEN LOWER(extension) = 'dwg' THEN 'dwg.pdf'
      ELSE LOWER(extension)
    END
  ) as sourceId,

  CASE
  -- Special cases → treat as unit 0
  WHEN UPPER(TRIM(unit_no)) IN ('SD','SK') THEN '0000'
  WHEN TRIM(unit_no) = '00'                    THEN '0000'
 
  -- unit_no is numeric (allow optional minus); pad to 4
  WHEN unit_no IS NOT NULL
   AND TRIM(unit_no) <> ''
   AND TRIM(unit_no) RLIKE '^-?[0-9]+$'
    THEN
      CASE
        -- Keep minus sign if it ever appears; pad digits (rare in practice)
        WHEN TRIM(unit_no) LIKE '-%'
          THEN CONCAT('-', LPAD(CAST(ABS(CAST(TRIM(unit_no) AS INT)) AS STRING), 3, '0'))
        ELSE LPAD(CAST(CAST(TRIM(unit_no) AS INT) AS STRING), 4, '0')
      END
 
  -- From sort_field: {zeros}{1–3 digits}{letters?}-  → pad to 4
  WHEN sort_field RLIKE '(?:0+)?([0-9]{1,3})(?:[a-zA-Z]+)?-'
    THEN LPAD(
           CAST(
             CAST(REGEXP_EXTRACT(sort_field, '(?:0+)?([0-9]{1,3})(?:[a-zA-Z]+)?-', 1) AS INT)
             AS STRING
           ),
           4, '0'
         )
 
  -- From doc_title leading digits → pad to 4
  WHEN doc_title RLIKE '^[0-9]+'
    THEN LPAD(
           CAST(CAST(REGEXP_EXTRACT(doc_title, '^([0-9]+)') AS INT) AS STRING),
           4, '0'
         )
 
  -- From alt_doc_id_no leading digits → pad to 4
  WHEN alt_doc_id_no RLIKE '^[0-9]+'
    THEN LPAD(
           CAST(CAST(REGEXP_EXTRACT(alt_doc_id_no, '^([0-9]+)') AS INT) AS STRING),
           4, '0'
         )
 
  -- From doc_id_no leading digits → pad to 4
  WHEN doc_id_no RLIKE '^[0-9]+'
    THEN LPAD(
           CAST(CAST(REGEXP_EXTRACT(doc_id_no, '^([0-9]+)') AS INT) AS STRING),
           4, '0'
         )
 
  ELSE 'N/A'
END AS sysUnit,
  is_new('upsert_dl_files_gvl_businesslogic', lastUpdatedTime) as isNewFlag
  FROM `db_dl_files_gvl`.`tbl_gvlrs253_doclib_gvl`
),
dm_file AS (
  SELECT 
  mpcFile.externalId, 
  mpcFile.space,
  mpcFile.sourceId,
  mpcFile.tags, 
  map.site_display_name,
  map.state,
  tbl_dl_files_timestamps_ref.isNewFlag
  FROM cdf_data_models("sp_mdm_mpc","mpc_datamodel","{{data_model_version}}","mpcFile") mpcFile
  INNER JOIN map
  ON map.site_acronym = split_part(mpcFile.space,'_',5)
  INNER JOIN tbl_dl_files_timestamps_ref
  ON mpcFile.externalId = tbl_dl_files_timestamps_ref.key
  WHERE mpcFile.space = 'sp_dat_dl_files_gvl'
)

SELECT
  CAST(dm_file.`externalId` AS STRING) AS externalId,
array_distinct(
  array_union(
    coalesce(dm_file.tags, array()),
    CASE 
      WHEN dl.`primary_class` IN ('PID', 'PLOT PLAN', 'ISO') THEN
        array_distinct(
          array_union(
            ARRAY('ToAnnotate', 'DetectInDiagrams'),
            CASE 
              WHEN sitewide.sourceId IS NOT NULL THEN ARRAY('SiteWideDetect') 
              ELSE ARRAY() 
            END
          )
        )
      ELSE ARRAY()
    END
  )
) AS tags,
  -- Assign "Garyville" to site
  'Garyville' AS sysSite,
  -- The isolated sysUnit calculation logic
  -- Note: Casting integer results back to STRING for consistent data type within the CASE statement
  dl.sysUnit as sysUnit,
  syslocation_ref_mappings.sysLocation as sysLocation,
  CASE -- Updated the pi tag logic so that it get converted to SAP form (Jack)
    WHEN LENGTH(dl.sort_field) > 0 THEN ARRAY_DISTINCT(
      ARRAY_UNION(
        -- Start: Union of all extracted tags from doc_title patterns
        ARRAY_UNION(
          ARRAY_UNION(
            -- P1: Apply REGEX to find asset tags that start with only numbers (10-1513-01, 56-EI-0123-A, 25-MCC-B14)
            REGEXP_EXTRACT_ALL(
              COALESCE(dl.doc_title, ''),
              '(?<!-)(\\b\\d{2,3}-(?:(?:\\d{3,10})|(?:[a-zA-Z]+))-?(?:(?:\\d+[a-zA-Z]*\\d?)|(?:[a-zA-Z]*\\d+[a-zA-Z]?))(?:-[0-9a-zA-Z]+)*)(?!\\s*service|\\s*SERVICE)',
              1
            ),
            -- P2: Apply REGEX to find asset tags that start with numbers and letters (005PM-SUB05IR-R002, 005PM-PTRANS0005)
            REGEXP_EXTRACT_ALL(
              COALESCE(dl.doc_title, ''),
              '(?<!-)(\\b(?:(?:\\d+[a-zA-Z]{2,6})|(?:[a-zA-Z]{2,6}\\d+))-[a-zA-Z0-9]+-?[a-zA-Z0-9]+(?:-[0-9a-zA-Z]+)?)',
              1
            )
          ),
          -- P3: Apply REGEX to match pi tags and transform them to asset tags (10TI8300 -> 10-T8300)
          TRANSFORM
            (
              REGEXP_EXTRACT_ALL(
                COALESCE(dl.doc_title, ''),
                '(\\d{2,3})([a-zA-Z])[a-zA-Z](\\d+)',
                0
              ),
              x -> REGEXP_REPLACE(x, '(\\d{2,3})([a-zA-Z])[a-zA-Z](\\d+)', '$1-$2$3')
            )
        ),
        -- End: Union of extracted tags from doc_title
        -- Union with processed sort_field tags
        TRANSFORM
          (SPLIT(dl.sort_field, ','), x -> TRIM(x))
      )
    )
    ELSE -- Only use tags extracted from doc_title if sort_field is empty
    ARRAY_DISTINCT(
      ARRAY_UNION(
        ARRAY_UNION(
          -- P1: Apply REGEX to find asset tags that start with only numbers (10-1513-01, 56-EI-0123-A, 25-MCC-B14)
          REGEXP_EXTRACT_ALL(
            COALESCE(dl.doc_title, ''),
            '(?<!-)(\\b\\d{2,3}-(?:(?:\\d{3,10})|(?:[a-zA-Z]+))-?(?:(?:\\d+[a-zA-Z]*\\d?)|(?:[a-zA-Z]*\\d+[a-zA-Z]?))(?:-[0-9a-zA-Z]+)*)(?!\\s*service|\\s*SERVICE)',
            1
          ),
          -- P2: Apply REGEX to find asset tags that start with numbers and letters (005PM-SUB05IR-R002, 005PM-PTRANS0005)
          REGEXP_EXTRACT_ALL(
            COALESCE(dl.doc_title, ''),
            '(?<!-)(\\b(?:(?:\\d+[a-zA-Z]{2,6})|(?:[a-zA-Z]{2,6}\\d+))-[a-zA-Z0-9]+-?[a-zA-Z0-9]+(?:-[0-9a-zA-Z]+)?)',
            1
          )
        ),
        -- P3: Apply REGEX to match pi tags and transform them to asset tags (10TI8300 -> 10-T8300)
        TRANSFORM
          (
            REGEXP_EXTRACT_ALL(
              COALESCE(dl.doc_title, ''),
              '(\\d{2,3})([a-zA-Z])[a-zA-Z](\\d+)',
              0
            ),
            x -> REGEXP_REPLACE(x, '(\\d{2,3})([a-zA-Z])[a-zA-Z](\\d+)', '$1-$2$3')
          )
      )
    )
  END AS sysTagsFound, 
  ARRAY_DISTINCT(
    FILTER(
      ARRAY_UNION(
        ARRAY_UNION(
          -- Existing identifiers
          ARRAY(
            IF(dl.`doc_id_no` IS NOT NULL, CAST(dl.`doc_id_no` AS STRING), NULL),
            IF(dl.`alt_doc_id_no` IS NOT NULL, CAST(dl.`alt_doc_id_no` AS STRING), NULL)
          ),
          -- Extracted from ISO doc_title
          IF(
            dl.`primary_class` = 'ISO' AND dl.`doc_title` IS NOT NULL,
            REGEXP_EXTRACT_ALL(
              REPLACE(REPLACE(dl.`doc_title`, '``', '"'), '" -', '"-'),
              '(\\b(?:\\d+ \\d+/\\d+|\\d+/\\d+|\\d+)"-[^-\\s]+-[^-\\s]+-[^-\\s]+\\b)',
              1
            ),
            ARRAY()
          )
        ),
        -- Add iso.Line No if present
        ARRAY(
          IF(
            iso.`Line No` IS NOT NULL AND LENGTH(iso.`Line No`) - LENGTH(REPLACE(iso.`Line No`, '-', '')) >= 3,
            CAST(iso.`Line No` AS STRING),
            NULL
          )
        )
      ),
      x -> x IS NOT NULL
    )
  ) AS aliases
FROM dl
  JOIN `db_common_lookup_mpc`.`tbl_site_mappings` map
    ON 'R090' = map.`site_code`
  JOIN dm_file
  ON dm_file.space = 'sp_dat_dl_files_gvl' AND dm_file.sourceId = dl.`key`
  LEFT JOIN syslocation_ref_mappings
ON syslocation_ref_mappings.Maintenance_Plant_Code = 'R090' and syslocation_ref_mappings.Location_Code = dl.sysUnit
  LEFT JOIN `db_dl_files_gvl`.`iso_summary` iso
    ON CONCAT(CAST(dl.`lib_no` AS STRING), ".", CAST(dl.`doc_no` AS STRING)) = iso.`key`
LEFT JOIN db_refining_files_annotation.annotation_sitewide_objects AS sitewide
ON dl.sourceId = sitewide.sourceId AND sitewide.dmView = 'mpcFile' AND sitewide.sysSite = map.site_display_name 
WHERE dm_file.state = 'full' 
   OR (dm_file.state = 'incremental' AND (dm_file.isNewFlag OR dl.isNewFlag) = True)