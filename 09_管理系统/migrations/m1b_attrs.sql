-- m1b：补商品属性实例表（D4 执行时发现 m1 遗漏）
-- GET/PUT /goods/{barcode}/attrs 依赖；属性模板在 sys_attr_template，实例在此表
\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS public.mdm_goods_attrs (
  barcode    TEXT PRIMARY KEY,
  attrs_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  source     TEXT NOT NULL DEFAULT 'MANUAL',
  updated_by TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.mdm_goods_attrs IS '商品属性实例（按类目模板填报）；与 sys_attr_template 配套';

GRANT SELECT, INSERT, UPDATE, DELETE ON public.mdm_goods_attrs TO goods_app;
GRANT SELECT ON public.mdm_goods_attrs TO goods_ro;

\echo '=== m1b 验收 ==='
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name='mdm_goods_attrs';
\echo '=== m1b DONE ==='
