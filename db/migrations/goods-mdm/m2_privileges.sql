-- 运行账号、只读账号和备份账号分离。默认拒绝执行。
-- 同一会话先执行：SELECT set_config('goods.apply_privileges', 'on', false);
-- 本文件不创建口令，不读取业务行。备份脚本在设置 PG_DSN_BACKUP 之前仍使用原账号。
\set ON_ERROR_STOP on

DO $$
BEGIN
  IF current_setting('goods.apply_privileges', true) IS DISTINCT FROM 'on' THEN
    RAISE EXCEPTION '未设置 goods.apply_privileges=on，拒绝调整权限';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'goods_backup') THEN
    CREATE ROLE goods_backup LOGIN;
  END IF;
END $$;

REVOKE SELECT ON TABLE public.sys_user FROM goods_ro;

CREATE OR REPLACE VIEW public.sys_user_directory AS
  SELECT id, account, display_name, role, status, phone, dept, last_login, created_at
  FROM public.sys_user;
REVOKE ALL ON TABLE public.sys_user_directory FROM PUBLIC;
GRANT SELECT ON TABLE public.sys_user_directory TO goods_ro;

DO $$
DECLARE
  rel regclass;
BEGIN
  FOR rel IN
    SELECT c.oid::regclass
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE n.nspname = 'public'
      AND r.rolname = 'goods_app'
      AND c.relkind IN ('r', 'p')
      AND (c.relname = 'dq_quarantine' OR c.relname LIKE 'dq\_quarantine\_%' ESCAPE '\')
  LOOP
    EXECUTE format('ALTER TABLE %s OWNER TO CURRENT_USER', rel);
    EXECUTE format('REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE %s FROM goods_app', rel);
    EXECUTE format('GRANT SELECT ON TABLE %s TO goods_app, goods_ro', rel);
  END LOOP;
END $$;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO goods_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO goods_backup;
