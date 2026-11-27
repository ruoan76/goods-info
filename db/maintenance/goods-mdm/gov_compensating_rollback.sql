-- 补偿回滚模板。直接执行会失败，避免覆盖后续修改或删除历史。
-- 应用代码里的 plan_compensating_rollback 与下面的判定一致：
-- 仅当 version_now = version_before + 1 时恢复字段，并把 version 加 1。
-- 不删除 mdm_goods_history，不执行 version = version - 1。
-- 现有 R39/R40 回滚脚本不符合该判定，在补上 version_before 之前不要再跑。
\set ON_ERROR_STOP on

DO $$
BEGIN
  RAISE EXCEPTION '补偿回滚模板默认拒绝执行';
END $$;

-- 确认快照含 version_before，并在维护窗口手工执行类似语句：
-- SELECT pg_advisory_xact_lock(hashtext('gov-batch:' || :'batch_id'));
-- UPDATE mdm_goods g
--    SET goods_name = s.old_name,
--        usage_stats_date = s.old_usage_stats_date,
--        version = g.version + 1,
--        updated_at = now()::text
--   FROM gov_batch_snapshot s
--  WHERE g.barcode = s.barcode
--    AND g.version = s.version_before + 1;
-- INSERT INTO mdm_goods_history (barcode, field_name, old_value, new_value, rule_code, batch_id)
-- SELECT g.barcode, 'goods_name', g.goods_name, s.old_name, 'ROLLBACK_COMPENSATE', :'batch_id'
--   FROM mdm_goods g
--   JOIN gov_batch_snapshot s ON s.barcode = g.barcode
--  WHERE g.version = s.version_before + 1;
-- 版本已经前进的条码留在人工冲突清单，不更新。
