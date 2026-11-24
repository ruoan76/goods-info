-- R16 分类修复：ISBN 图书归位 + 食品类纸品归位（用户 2026-11-24 确认执行）
-- 惯例：快照备份 → sys_gov_batch 登记 → 单事务批量 UPDATE（category_source/version/updated_at）
BEGIN;

-- 0. 快照（回滚能力）
CREATE TABLE gov_r16_snapshot AS
SELECT barcode, goods_name, category_id AS old_cat, category_source AS old_src,
       category_confidence AS old_conf, version AS old_ver, now()::text AS snap_at
FROM mdm_goods
WHERE ((barcode LIKE '978%' OR barcode LIKE '979%') AND substr(category_id,1,3) <> 'C06')
   OR (substr(category_id,1,3) = 'C01' AND
      (goods_name LIKE '%纸巾%' OR goods_name LIKE '%面巾%' OR goods_name LIKE '%抽纸%'
       OR goods_name LIKE '%卷纸%' OR goods_name LIKE '%湿巾%' OR goods_name LIKE '%餐巾%'
       OR goods_name LIKE '%卫生纸%'));
CREATE UNIQUE INDEX idx_r16_snap_bc ON gov_r16_snapshot(barcode);

-- 1. 新建图书报刊类目（C06 文具礼品下 L2）
INSERT INTO mdm_category (category_id, parent_id, category_level, category_path, category_name, is_leaf, sort_order, status)
VALUES ('C0604', 'C06', 2, '/C06/C0604/', '图书报刊', 1, 4, 'ACTIVE')
ON CONFLICT (category_id) DO NOTHING;

-- 2. 批次登记
INSERT INTO sys_gov_batch (batch_id, batch_type, rule_version, started_at, status,
                           input_rows, valid_rows, excluded_rows, output_rows, quarantined_rows,
                           recategorized_rows, auto_decided_rows, ai_decided_rows, remark)
VALUES ('R16_ISBN_FIX_20261124', 'CATEGORY_FIX', 'R16-1.0', now()::text, 'RUNNING',
        0,0,0,0,0,0,0,0, 'ISBN(978/979)条码商品归位图书报刊；快照表 gov_r16_snapshot 可回滚'),
       ('R16_PAPER_FIX_20261124', 'CATEGORY_FIX', 'R16-1.0', now()::text, 'RUNNING',
        0,0,0,0,0,0,0,0, '食品类中纸品关键词商品归位纸品湿巾C0402');

-- 3. ISBN 迁移（非 C06 的全部 978/979 条码，含 C00 未分类中的 ISBN）
--    category_source 值域受 ck_goods_source 约束，复用治理惯例 SEMANTIC_FIX；批次与置信度可区分来源
UPDATE mdm_goods
SET category_id = 'C0604', category_source = 'SEMANTIC_FIX', category_confidence = 1.0,
    updated_at = now()::text, version = version + 1
WHERE (barcode LIKE '978%' OR barcode LIKE '979%') AND substr(category_id,1,3) <> 'C06';

-- 4. 纸品迁移（C01 食品类 → C0402 纸品湿巾）
UPDATE mdm_goods
SET category_id = 'C0402', category_source = 'SEMANTIC_FIX', category_confidence = 0.95,
    updated_at = now()::text, version = version + 1
WHERE substr(category_id,1,3) = 'C01'
  AND (goods_name LIKE '%纸巾%' OR goods_name LIKE '%面巾%' OR goods_name LIKE '%抽纸%'
       OR goods_name LIKE '%卷纸%' OR goods_name LIKE '%湿巾%' OR goods_name LIKE '%餐巾%'
       OR goods_name LIKE '%卫生纸%');

-- 5. 关闭批次并回填计数
UPDATE sys_gov_batch SET finished_at = now()::text, status = 'SUCCESS',
       output_rows = (SELECT count(*) FROM mdm_goods WHERE category_id='C0604'),
       recategorized_rows = (SELECT count(*) FROM gov_r16_snapshot WHERE old_cat NOT LIKE 'C01%')
WHERE batch_id = 'R16_ISBN_FIX_20261124';
UPDATE sys_gov_batch SET finished_at = now()::text, status = 'SUCCESS',
       output_rows = (SELECT count(*) FROM mdm_goods WHERE category_source = 'SEMANTIC_FIX' AND category_id = 'C0402'),
       recategorized_rows = (SELECT count(*) FROM gov_r16_snapshot WHERE old_cat LIKE 'C01%')
WHERE batch_id = 'R16_PAPER_FIX_20261124';

COMMIT;

-- 6. 验证输出
SELECT 'C0604 图书报刊' AS item, count(*) FROM mdm_goods WHERE category_id='C0604'
UNION ALL SELECT 'ISBN 残留非C06', count(*) FROM mdm_goods WHERE (barcode LIKE '978%' OR barcode LIKE '979%') AND substr(category_id,1,3) <> 'C06'
UNION ALL SELECT 'C01 纸品关键词残留', count(*) FROM mdm_goods WHERE substr(category_id,1,3)='C01' AND (goods_name LIKE '%纸巾%' OR goods_name LIKE '%面巾%' OR goods_name LIKE '%抽纸%' OR goods_name LIKE '%卷纸%' OR goods_name LIKE '%湿巾%' OR goods_name LIKE '%餐巾%' OR goods_name LIKE '%卫生纸%')
UNION ALL SELECT '商品总数', count(*) FROM mdm_goods
UNION ALL SELECT '快照行数', count(*) FROM gov_r16_snapshot;
