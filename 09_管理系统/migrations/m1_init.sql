-- ============================================================
-- m1_init.sql  商品主数据管理系统 初始化迁移
-- 基线：goods_mdm (PG14)  |  幂等可重复执行  |  2026-11-23
-- 目标：5 张新表 + goods_ro 只读账号 + 铁律③禁复用列 + status 值域 + 授权收权
-- ============================================================
\set ON_ERROR_STOP on

-- ------------------------------------------------------------
-- 0. 前置：以 DBA/postgres 执行（goods_app 无 CREATEDB，需建角色与收权）
--    执行方式：sudo -u postgres psql -d goods_mdm -f m1_init.sql
--    首次创建 goods_ro 后，在 psql 中执行 \password goods_ro 设置密码。
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- 1. 只读账号 goods_ro（隔离区 dq_quarantine 强制走此账号）
-- ------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'goods_ro') THEN
    CREATE ROLE goods_ro LOGIN;
    RAISE NOTICE 'created role goods_ro';
  ELSE
    RAISE NOTICE 'role goods_ro exists, skip';
  END IF;
END
$$;

-- ------------------------------------------------------------
-- 2. 五张业务表
-- ------------------------------------------------------------

-- 2.1 sys_user 用户表（角色用枚举，不建 sys_role 表）
CREATE TABLE IF NOT EXISTS public.sys_user (
  id              BIGSERIAL PRIMARY KEY,
  account         TEXT NOT NULL UNIQUE,
  display_name    TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('Viewer','Operator','Steward')),
  status          TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
  phone           TEXT,
  dept            TEXT,
  password_hash   TEXT NOT NULL,
  last_login      TIMESTAMPTZ,
  token_version   INTEGER NOT NULL DEFAULT 0,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON COLUMN public.sys_user.role IS 'Viewer/Operator/Steward，应用层配置，不建 sys_role 表';
COMMENT ON COLUMN public.sys_user.token_version IS '登出 +1，JWT claim.ver 与库不一致即拒（替代内存黑名单）';

-- 2.2 sys_unit 单位字典（goods_count 物化字段，禁实时 COUNT）
CREATE TABLE IF NOT EXISTS public.sys_unit (
  code        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  enabled     BOOLEAN NOT NULL DEFAULT TRUE,
  goods_count BIGINT NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON COLUMN public.sys_unit.goods_count IS '物化统计字段，由导入/治理任务结束刷新，禁实时 COUNT(432万)';

-- 2.3 sys_change_log 变更审计（goods_app 仅 INSERT，无 UPDATE/DELETE）
CREATE TABLE IF NOT EXISTS public.sys_change_log (
  log_id      BIGSERIAL PRIMARY KEY,
  batch_id    TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_key  TEXT NOT NULL,
  action      TEXT NOT NULL,
  operator    TEXT NOT NULL,
  before_data JSONB,
  after_data  JSONB,
  changed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON public.sys_change_log(entity_type, entity_key, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_change_log_operator ON public.sys_change_log(operator, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_change_log_batch ON public.sys_change_log(batch_id);
COMMENT ON TABLE public.sys_change_log IS '所有写端点留痕；goods_app 仅授 INSERT，REVOKE UPDATE/DELETE';

-- 2.4 sys_attr_template 类目属性模板
CREATE TABLE IF NOT EXISTS public.sys_attr_template (
  id          BIGSERIAL PRIMARY KEY,
  category_id TEXT NOT NULL,
  template    JSONB NOT NULL,
  enabled     BOOLEAN NOT NULL DEFAULT TRUE,
  updated_by  TEXT NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(category_id)
);
COMMENT ON COLUMN public.sys_attr_template.template IS 'JSONB：必填项、字段类型、校验规则';

-- 2.5 sys_import_job 导入任务
CREATE TABLE IF NOT EXISTS public.sys_import_job (
  id           BIGSERIAL PRIMARY KEY,
  batch_id     TEXT NOT NULL UNIQUE,
  job_type     TEXT NOT NULL,
  operator     TEXT NOT NULL,
  total_rows   INTEGER NOT NULL DEFAULT 0,
  success_rows INTEGER NOT NULL DEFAULT 0,
  fail_rows    INTEGER NOT NULL DEFAULT 0,
  fail_detail  JSONB,
  status       TEXT NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING','SUCCESS','PARTIAL','FAILED')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at  TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- 3. 铁律③支撑：条码 90 天禁复用登记表（禁用到期列）
--    现网 mdm_barcode_alias 仅 5 列无到期字段，补 banned_until
-- ------------------------------------------------------------
ALTER TABLE public.mdm_barcode_alias
  ADD COLUMN IF NOT EXISTS banned_until DATE;
COMMENT ON COLUMN public.mdm_barcode_alias.banned_until IS 'VOIDED 登记 90 天禁复用截止日；准入校验命中未过期即拒';
CREATE INDEX IF NOT EXISTS idx_alias_banned ON public.mdm_barcode_alias(banned_until) WHERE banned_until IS NOT NULL;

-- ------------------------------------------------------------
-- 4. mdm_goods.status 值域扩展（现全 ACTIVE 无 CHECK，加约束）
--    先清理异常值（本例无），再补 CHECK
-- ------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'ck_goods_status' AND conrelid = 'public.mdm_goods'::regclass
  ) THEN
    ALTER TABLE public.mdm_goods
      ADD CONSTRAINT ck_goods_status
      CHECK (status IN ('ACTIVE','INACTIVE','VOIDED'));
    RAISE NOTICE 'added ck_goods_status';
  ELSE
    RAISE NOTICE 'ck_goods_status exists, skip';
  END IF;
END
$$;

-- ------------------------------------------------------------
-- 5. 授权
-- ------------------------------------------------------------
-- 5.1 goods_app：业务表读写；审计表仅 INSERT
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sys_user, public.sys_unit,
  public.sys_attr_template, public.sys_import_job, public.mdm_barcode_alias TO goods_app;
GRANT USAGE, SELECT ON SEQUENCE public.sys_user_id_seq, public.sys_attr_template_id_seq,
  public.sys_import_job_id_seq TO goods_app;
GRANT INSERT, SELECT ON public.sys_change_log TO goods_app;
GRANT USAGE, SELECT ON SEQUENCE public.sys_change_log_log_id_seq TO goods_app;
REVOKE UPDATE, DELETE, TRUNCATE ON public.sys_change_log FROM goods_app;

-- 5.2 goods_ro：隔离区与全部业务只读（无写）
GRANT CONNECT ON DATABASE goods_mdm TO goods_ro;
GRANT USAGE ON SCHEMA public TO goods_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO goods_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO goods_ro;

-- 5.3 收权：goods_app 不得在 public schema 建表（业务表 DML 而已）
REVOKE CREATE ON SCHEMA public FROM goods_app;
-- PG14：public schema 的 CREATE 默认来自 PUBLIC 角色，必须一并收回才真正生效
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ------------------------------------------------------------
-- 6. 初始化种子（幂等）：内置三角色演示账号
--    PBKDF2 哈希占位，实际由 D2 auth 模块首次启动时重置
-- ------------------------------------------------------------
INSERT INTO public.sys_user (account, display_name, role, status, password_hash)
SELECT 'viewer',  '演示-查看者', 'Viewer',   'ACTIVE', 'SEED_PENDING_RESET'
WHERE NOT EXISTS (SELECT 1 FROM public.sys_user WHERE account='viewer');
INSERT INTO public.sys_user (account, display_name, role, status, password_hash)
SELECT 'operator','演示-录入员', 'Operator', 'ACTIVE', 'SEED_PENDING_RESET'
WHERE NOT EXISTS (SELECT 1 FROM public.sys_user WHERE account='operator');
INSERT INTO public.sys_user (account, display_name, role, status, password_hash)
SELECT 'steward', '演示-管理员', 'Steward',  'ACTIVE', 'SEED_PENDING_RESET'
WHERE NOT EXISTS (SELECT 1 FROM public.sys_user WHERE account='steward');

-- ------------------------------------------------------------
-- 7. 验收输出
-- ------------------------------------------------------------
\echo '=== m1 验收：5 张新表 ==='
SELECT tablename FROM pg_tables WHERE schemaname='public'
  AND tablename IN ('sys_user','sys_unit','sys_change_log','sys_attr_template','sys_import_job')
  ORDER BY tablename;
\echo '=== m1 验收：goods_ro 角色 ==='
SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname='goods_ro';
\echo '=== m1 验收：goods_app 审计表权限 ==='
SELECT privilege_type FROM information_schema.role_table_grants
  WHERE table_name='sys_change_log' AND grantee='goods_app' ORDER BY 1;
\echo '=== m1 验收：goods_app public CREATE 应为 f ==='
SELECT has_schema_privilege('goods_app','public','CREATE') AS app_can_create;
\echo '=== m1 DONE ==='
