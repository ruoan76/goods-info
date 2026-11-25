#!/bin/bash
# 每日 pg_dump | gzip 到 /data/backups/，保留 7 天
# 使用 goods_app 通过 TCP 连接，凭据由 libpq 从 .pgpass 或运行环境读取。
set -euo pipefail
BACKUP_DIR=/data/backups
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/goods_mdm_daily_${STAMP}.sql.gz"
LOG=/var/log/goods-mdm/backup.log
mkdir -p "$BACKUP_DIR"
touch "$LOG" 2>/dev/null || true

# 先写临时文件，成功后原子改名（避免失败留下空壳备份）
TMP="${OUT}.tmp"
pg_dump --no-password -U goods_app -h 127.0.0.1 -d goods_mdm | gzip > "$TMP"
# 校验：gzip 解压首行必须是 SQL 注释且体积合理（>1MB）
SZ=$(stat -c%s "$TMP")
if [ "$SZ" -lt 1048576 ]; then
  echo "[$(date)] backup FAILED too small ${SZ}B, discard" >> "$LOG"
  rm -f "$TMP"
  exit 1
fi
mv "$TMP" "$OUT"
echo "[$(date)] backup ok: $OUT ($(du -h "$OUT" | cut -f1))" >> "$LOG"
# 保留 7 天
find "$BACKUP_DIR" -name 'goods_mdm_daily_*.sql.gz' -mtime +7 -delete
ln -sfn "$OUT" "$BACKUP_DIR/goods_mdm_latest.sql.gz"
echo "backup ok: $OUT"
