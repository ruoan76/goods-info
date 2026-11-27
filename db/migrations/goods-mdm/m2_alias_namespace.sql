-- 别名命名空间约束。默认拒绝执行。
-- 同一会话先执行：SELECT set_config('goods.apply_alias_constraints', 'on', false);
-- 若盘点发现主码被登记成别名，或其他类型超出枚举，脚本会中止且不改约束。
\set ON_ERROR_STOP on

DO $$
BEGIN
  IF current_setting('goods.apply_alias_constraints', true) IS DISTINCT FROM 'on' THEN
    RAISE EXCEPTION '未设置 goods.apply_alias_constraints=on，拒绝修改别名约束';
  END IF;
END $$;

DO $$
DECLARE
  bad_types text;
  main_as_alias bigint;
BEGIN
  SELECT string_agg(DISTINCT alias_type, ', ' ORDER BY alias_type)
    INTO bad_types
  FROM public.mdm_barcode_alias
  WHERE alias_type NOT IN ('BIG_PACK', 'OLD_CODE', 'DIFF_PACK', 'VOIDED_BAN');
  IF bad_types IS NOT NULL THEN
    RAISE EXCEPTION '存在未纳入枚举的别名类型: %', bad_types;
  END IF;

  SELECT count(*) INTO main_as_alias
  FROM public.mdm_barcode_alias a
  JOIN public.mdm_goods g ON g.barcode = a.alias_barcode
  WHERE a.alias_type <> 'VOIDED_BAN';
  IF main_as_alias > 0 THEN
    RAISE EXCEPTION '有 % 条主码被登记成别名，先清理后再加约束', main_as_alias;
  END IF;
END $$;

ALTER TABLE public.mdm_barcode_alias
  DROP CONSTRAINT IF EXISTS ck_alias_type;
ALTER TABLE public.mdm_barcode_alias
  ADD CONSTRAINT ck_alias_type
  CHECK (alias_type IN ('BIG_PACK', 'OLD_CODE', 'DIFF_PACK', 'VOIDED_BAN'));

CREATE OR REPLACE FUNCTION public.mdm_alias_namespace_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.alias_type <> 'VOIDED_BAN' AND NEW.alias_barcode = NEW.master_barcode THEN
    RAISE EXCEPTION '别名不能与主码相同';
  END IF;
  IF NEW.alias_type = 'VOIDED_BAN' AND NEW.alias_barcode <> NEW.master_barcode THEN
    RAISE EXCEPTION '禁复用登记必须指向自身';
  END IF;
  IF NEW.alias_type <> 'VOIDED_BAN' AND EXISTS (
    SELECT 1 FROM public.mdm_goods WHERE barcode = NEW.alias_barcode
  ) THEN
    RAISE EXCEPTION '已有商品主码不能登记为别名';
  END IF;
  IF NEW.alias_type <> 'VOIDED_BAN' AND TG_OP = 'INSERT' AND EXISTS (
    SELECT 1 FROM public.mdm_barcode_alias AS existing
    WHERE existing.alias_barcode = NEW.alias_barcode
      AND existing.alias_type <> 'VOIDED_BAN'
      AND existing.master_barcode <> NEW.master_barcode
  ) THEN
    RAISE EXCEPTION '该别名已指向其他主码';
  END IF;
  IF NEW.alias_type <> 'VOIDED_BAN' AND TG_OP = 'UPDATE' AND EXISTS (
    SELECT 1 FROM public.mdm_barcode_alias AS existing
    WHERE existing.alias_barcode = NEW.alias_barcode
      AND existing.alias_type <> 'VOIDED_BAN'
      AND existing.master_barcode <> NEW.master_barcode
      AND (existing.alias_type IS DISTINCT FROM OLD.alias_type
           OR existing.alias_barcode IS DISTINCT FROM OLD.alias_barcode)
  ) THEN
    RAISE EXCEPTION '该别名已指向其他主码';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_alias_namespace ON public.mdm_barcode_alias;
CREATE TRIGGER trg_alias_namespace
  BEFORE INSERT OR UPDATE ON public.mdm_barcode_alias
  FOR EACH ROW
  EXECUTE FUNCTION public.mdm_alias_namespace_guard();
