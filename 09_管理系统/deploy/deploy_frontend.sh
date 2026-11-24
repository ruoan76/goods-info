#!/bin/bash
# 前端 dist 按日期目录发布 + 秒级回滚
# 用法: deploy_frontend.sh [回滚日期目录名]
set -e
ROOT=/data/projects/goods-info/09_管理系统/frontend
PUBLISH=$ROOT/dist
ARCHIVE=$ROOT/releases
mkdir -p "$ARCHIVE" /var/log/goods-mdm

cd "$ROOT"
if [ -n "$1" ]; then
  # 回滚到指定历史版本
  TARGET="$ARCHIVE/$1"
  [ -d "$TARGET" ] || { echo "版本不存在: $1"; exit 1; }
  echo "回滚到 $1"
else
  TAG=$(date +%Y%m%d_%H%M%S)
  TARGET="$ARCHIVE/$TAG"
  mkdir -p "$TARGET"
  cp -a dist-new/. "$TARGET/"
  echo "发布新版本 $TAG"
fi

# 原子切换：先写临时软链再 rename
rm -f "$PUBLISH.tmp"
ln -s "$TARGET" "$PUBLISH.tmp"
mv -Tf "$PUBLISH.tmp" "$PUBLISH"
echo "当前版本: $(readlink -f "$PUBLISH")"
ls -1t "$ARCHIVE" | head -10
