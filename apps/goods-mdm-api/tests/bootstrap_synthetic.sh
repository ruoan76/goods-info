#!/usr/bin/env bash
# 在临时目录启动独立 PostgreSQL，加载合成结构。不连接 5432 上的正式实例。
set -euo pipefail

PORT="${GOODS_MDM_TEST_PORT:-55432}"
DATA="${GOODS_MDM_TEST_DATA:-/tmp/goods-mdm-test-pg}"
SOCKET="${GOODS_MDM_TEST_SOCKET:-/tmp/gmdm-sock}"
DATABASE="${GOODS_MDM_TEST_DATABASE:-goods_mdm_test}"

if [[ "$PORT" == "5432" || "$DATABASE" != goods_mdm_test* ]]; then
  echo "拒绝使用正式端口或非测试库名" >&2
  exit 1
fi
case "$DATA" in
  /tmp/goods-mdm-test-pg) ;;
  *) echo "测试数据目录必须是 /tmp/goods-mdm-test-pg" >&2; exit 1 ;;
esac

if ! command -v initdb >/dev/null 2>&1; then
  found=$(ls /usr/lib/postgresql/*/bin/initdb 2>/dev/null | sort | tail -1 || true)
  if [[ -z "$found" ]]; then
    echo "找不到 initdb" >&2
    exit 1
  fi
  export PATH="$(dirname "$found"):$PATH"
fi

mkdir -p "$SOCKET"
if [[ -f "$DATA/postmaster.pid" ]]; then
  pg_ctl -D "$DATA" -m fast stop || true
fi
rm -rf "$DATA"
if locale -a | grep -qx 'C.utf8'; then
  TEST_LOCALE=C.utf8
elif locale -a | grep -qx 'C.UTF-8'; then
  TEST_LOCALE=C.UTF-8
else
  echo "需要 C.UTF-8 locale 才能保存中文样本" >&2
  exit 1
fi
initdb -D "$DATA" --username=postgres --auth=trust --locale="$TEST_LOCALE" --encoding=UTF8 >/dev/null
cat >> "$DATA/postgresql.conf" <<EOF
listen_addresses = ''
port = ${PORT}
unix_socket_directories = '${SOCKET}'
EOF
pg_ctl -D "$DATA" -l "$DATA/server.log" -w start

psql -h "$SOCKET" -p "$PORT" -U postgres -d postgres -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'goods_test_app') THEN
    CREATE ROLE goods_test_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'goods_test_ro') THEN
    CREATE ROLE goods_test_ro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
  END IF;
END
\$\$;
DROP DATABASE IF EXISTS ${DATABASE};
CREATE DATABASE ${DATABASE} OWNER postgres;
SQL

script_dir=$(cd "$(dirname "$0")" && pwd)
psql -h "$SOCKET" -p "$PORT" -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f "$script_dir/synthetic/schema.sql"
psql -h "$SOCKET" -p "$PORT" -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f "$script_dir/synthetic/seed.sql"
psql -h "$SOCKET" -p "$PORT" -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 <<SQL
GRANT CONNECT ON DATABASE ${DATABASE} TO goods_test_app, goods_test_ro;
GRANT USAGE ON SCHEMA public TO goods_test_app, goods_test_ro;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO goods_test_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO goods_test_app;
GRANT SELECT ON TABLE public.dq_quarantine TO goods_test_ro;
SQL

echo "GOODS_MDM_TEST_SOCKET=$SOCKET"
echo "GOODS_MDM_TEST_PORT=$PORT"
echo "GOODS_MDM_TEST_DATABASE=$DATABASE"
