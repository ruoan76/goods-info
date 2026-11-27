-- 结构迁移账本。只建账本表，不重放历史数据批次。
-- R39/R40 的导入与回滚仍在仓库外的一次性脚本中，不能靠本文件重建。
-- m1_init 依赖已经存在的 mdm_goods / mdm_barcode_alias，空库仍不能只靠当前迁移得到完整结构。
\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS public.schema_migration (
  version    text PRIMARY KEY,
  note       text NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.schema_migration IS
  '已应用的结构迁移。一次性治理写入不记入本表，也不要从这里重放。';
