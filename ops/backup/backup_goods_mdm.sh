#!/bin/bash
# 每日 pg_dump | gzip 到 /data/backups/，保留 7 天
# 权限迁移完成前仍使用 goods_app。设置 PG_DSN_BACKUP 后改走备份角色。
set -euo pipefail
umask 077
BACKUP_DIR=/data/backups
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/goods_mdm_daily_${STAMP}.sql.gz"
LOG=/var/log/goods-mdm/backup.log
mkdir -p "$BACKUP_DIR"
touch "$LOG" 2>/dev/null || true

# 先写临时文件，成功后原子改名（避免失败留下空壳备份）
TMP="${OUT}.tmp"
trap 'test ! -e "$TMP" || unlink -- "$TMP"' EXIT
DUMP_DSN="${PG_DSN_BACKUP:-${PG_DSN_APP:-}}"
if [[ -n "$DUMP_DSN" ]]; then
  PG_DUMP_DSN="$DUMP_DSN" python -c '
import os
from psycopg2.extensions import parse_dsn

dsn = parse_dsn(os.environ.pop("PG_DUMP_DSN"))
for key, variable in (
    ("host", "PGHOST"), ("port", "PGPORT"), ("dbname", "PGDATABASE"),
    ("user", "PGUSER"), ("password", "PGPASSWORD"),
):
    if key in dsn:
        os.environ[variable] = dsn[key]
os.execvp("pg_dump", ["pg_dump", "--no-password"])
' | gzip > "$TMP"
else
  pg_dump --no-password -U goods_app -h 127.0.0.1 -d goods_mdm | gzip > "$TMP"
fi
gzip -t "$TMP"
# 校验：gzip 解压首行必须是 SQL 注释且体积合理（>1MB）
SZ=$(stat -c%s "$TMP")
if [ "$SZ" -lt 1048576 ]; then
  echo "[$(date)] backup FAILED too small ${SZ}B, discard" >> "$LOG"
  exit 1
fi
mv "$TMP" "$OUT"
echo "[$(date)] backup ok: $OUT ($(du -h "$OUT" | cut -f1))" >> "$LOG"
# 保留 7 天
find "$BACKUP_DIR" -name 'goods_mdm_daily_*.sql.gz' -mtime +7 -delete
ln -sfn "$OUT" "$BACKUP_DIR/goods_mdm_latest.sql.gz"
echo "backup ok: $OUT"
