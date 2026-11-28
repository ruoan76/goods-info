-- 合成样本：有价、待补、未分类、同名多码、一条别名、一条隔离记录。
\set ON_ERROR_STOP on

INSERT INTO public.sys_user (account, display_name, role, status, password_hash)
VALUES
  ('viewer', '合成查看者', 'Viewer', 'ACTIVE', 'SEED'),
  ('operator', '合成录入员', 'Operator', 'ACTIVE', 'SEED'),
  ('steward', '合成管理员', 'Steward', 'ACTIVE', 'SEED');

INSERT INTO public.sys_unit (code, name, sort_order) VALUES ('EA', '个', 1);

INSERT INTO public.mdm_category
  (category_id, parent_id, category_level, category_name, is_leaf, sort_order, status)
VALUES
  ('C00', NULL, 1, '未分类', true, 0, 'ACTIVE'),
  ('C01', NULL, 1, '食品', false, 1, 'ACTIVE'),
  ('C0101', 'C01', 2, '饮料', true, 1, 'ACTIVE');

INSERT INTO public.mdm_goods
  (barcode, goods_name, category_id, unit_id, inprice, outprice, quality_grade,
   status, version, governance_batch, created_at, updated_at)
VALUES
  ('6900000000001', '已定价商品', 'C0101', 'EA', 10, 20, 'C', 'ACTIVE', 1, 'SYNTH', '2026-11-28', '2026-11-28'),
  ('6900000000002', '待补售价', 'C0101', 'EA', 10, 0, 'C', 'ACTIVE', 1, 'SYNTH', '2026-11-28', '2026-11-28'),
  ('6900000000003', '未分类商品', 'C00', 'EA', NULL, NULL, 'C', 'ACTIVE', 1, 'SYNTH', '2026-11-28', '2026-11-28'),
  ('6900000000004', '同名商品', 'C0101', 'EA', 3, 4, 'C', 'ACTIVE', 1, 'SYNTH', '2026-11-28', '2026-11-28'),
  ('6900000000005', '同名商品', 'C01', 'EA', 5, 6, 'C', 'ACTIVE', 1, 'SYNTH', '2026-11-28', '2026-11-28');

INSERT INTO public.mdm_barcode_alias (alias_barcode, master_barcode, alias_type, created_at)
VALUES ('6900000000011', '6900000000001', 'BIG_PACK', '2026-11-28');

INSERT INTO public.sys_attr_template (category_id, template, updated_by)
VALUES ('C0101', '{"required":["color"],"fields":{"color":{"type":"string","enum":["红","蓝"]}}}', 'steward');

INSERT INTO public.dq_quarantine (batch_id, barcode, issue_type, conflict_field, value_a, value_b, status)
VALUES
  ('SYNTH', '6900000000004', 'NAME', 'goods_name', '同名商品', '同名商品', 'OPEN'),
  ('SYNTH', '6900000000005', 'NAME', 'goods_name', '同名商品', '其他', 'CLOSED');
