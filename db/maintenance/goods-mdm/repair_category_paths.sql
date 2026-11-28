-- Opt-in maintenance. Default is a zero-target preview and ROLLBACK.
-- Supply psql -v barcodes='["...","..."]' for a reviewed explicit scope.
-- Applying additionally requires -v apply=true -v batch=UNIQUE_BATCH -v operator=NAME.
-- Back up and obtain release/data-maintenance authorization before applying.
\set ON_ERROR_STOP on
\if :{?barcodes}
\else
  \set barcodes '[]'
\endif
\if :{?apply}
\else
  \set apply false
\endif
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
LOCK TABLE mdm_category IN SHARE MODE;
CREATE TEMP TABLE proposed_category_paths ON COMMIT DROP AS
WITH RECURSIVE paths AS (
    SELECT category_id, ARRAY[category_id] AS chain,
           '/' || category_id || '/' AS path
    FROM mdm_category WHERE parent_id IS NULL
    UNION ALL
    SELECT child.category_id, parent.chain || child.category_id,
           parent.path || child.category_id || '/'
    FROM mdm_category child JOIN paths parent ON child.parent_id = parent.category_id
    WHERE NOT child.category_id = ANY(parent.chain)
)
SELECT g.barcode, g.category_id, g.category_path AS old_path, p.path AS new_path
FROM mdm_goods g JOIN paths p USING (category_id)
WHERE g.barcode IN (SELECT jsonb_array_elements_text(:'barcodes'::jsonb))
  AND g.category_path IS DISTINCT FROM p.path;
-- Missing-parent/cyclic nodes are excluded; nothing infers a new category.
SELECT * FROM proposed_category_paths ORDER BY barcode;
\if :apply
  -- Deliberately fail on missing batch/operator instead of inventing provenance.
  INSERT INTO sys_gov_batch(batch_id,batch_type,rule_version,started_at,status,remark)
  VALUES (:'batch','MANUAL','CATEGORY_PATH_FIX-1',now()::text,'SUCCESS',:'operator');
  CREATE TEMP TABLE repaired_category_paths ON COMMIT DROP AS
  WITH changed AS (
    UPDATE mdm_goods g SET category_path=p.new_path,
        version=g.version+1, updated_at=now()::text
    FROM proposed_category_paths p
    WHERE g.barcode=p.barcode AND g.category_id=p.category_id AND g.category_path IS NOT DISTINCT FROM p.old_path
    RETURNING g.barcode,p.old_path,p.new_path
  ) SELECT * FROM changed;
  INSERT INTO mdm_goods_history(barcode,field_name,old_value,new_value,rule_code,batch_id)
  SELECT barcode,'category_path',old_path,new_path,'CATEGORY_PATH_FIX',:'batch'
  FROM repaired_category_paths;
  INSERT INTO sys_change_log(batch_id,entity_type,entity_key,action,operator,before_data,after_data)
  SELECT :'batch','GOODS',barcode,'CATEGORY_PATH_FIX',:'operator',
         jsonb_build_object('category_path',old_path),jsonb_build_object('category_path',new_path)
  FROM repaired_category_paths;
  COMMIT;
\else
  ROLLBACK;
\endif
