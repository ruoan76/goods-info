-- m1c: sys_unit 字典种子（幂等，可重放）
-- 单位编码来自实库 mdm_goods.unit_id 去重；名称按原型口径标注"待业务确认"；
-- goods_count 为预聚合快照（导入任务结束时刷新，不实时扫 432 万表）。
INSERT INTO public.sys_unit (code, name, sort_order, enabled, goods_count, created_at, updated_at)
SELECT u.unit_id,
       '（待确认）',
       ROW_NUMBER() OVER (ORDER BY u.c DESC)::int,
       TRUE,
       u.c,
       now(), now()
FROM (SELECT unit_id, count(*)::bigint c FROM public.mdm_goods WHERE unit_id IS NOT NULL GROUP BY unit_id) u
WHERE NOT EXISTS (SELECT 1 FROM public.sys_unit s WHERE s.code = u.unit_id);
