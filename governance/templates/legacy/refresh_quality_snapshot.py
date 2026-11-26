#!/usr/bin/env python3
"""刷新 sys_quality_snapshot：把 52s 级的全表聚合计一次，写成快照供看板读取。

看板每次刷新都跑全表 GROUP BY 会让 dashboard 从 2.7s 变成 55s，
故把这些慢指标挪到离线，按 cron 每日刷新一次。
"""
from __future__ import annotations

import os
import sys
import time

import psycopg2

DSN = (
    os.environ.get("GOODS_MDM_PG_DSN")
    or os.environ.get("PG_DSN_APP")
    or "host=127.0.0.1 port=5432 dbname=goods_mdm user=goods_app"
)

METRICS = [
    (
        "cross_bucket_names",
        """SELECT count(*) FROM (
               SELECT goods_name FROM mdm_goods
               GROUP BY goods_name
               HAVING count(DISTINCT category_id) >= 10
           ) t""",
        "精确名跨>=10桶的名称数",
    ),
    (
        "cross_bucket_rows",
        """SELECT coalesce(sum(n), 0) FROM (
               SELECT count(*) AS n FROM mdm_goods
               GROUP BY goods_name
               HAVING count(DISTINCT category_id) >= 10
           ) t""",
        "上述名称覆盖的行数",
    ),
]


def main() -> int:
    pg = psycopg2.connect(DSN)
    cur = pg.cursor()
    rc = 0
    for metric, sql, note in METRICS:
        t0 = time.time()
        try:
            cur.execute(sql)
            value = cur.fetchone()[0]
        except Exception as exc:  # noqa: BLE001 - 单项失败不应阻断其余指标
            print(f"  [FAIL] {metric}: {exc}")
            pg.rollback()
            rc = 1
            continue
        cur.execute(
            "INSERT INTO sys_quality_snapshot(metric, value_int, note) "
            "VALUES(%s, %s, %s) ON CONFLICT DO NOTHING",
            (metric, value, note),
        )
        pg.commit()
        print(f"  [ OK ] {metric} = {value:,}  ({time.time() - t0:.1f}s)")
    pg.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
