#!/usr/bin/env python3
"""治理批次守卫：执行前检查前置条件，执行后校验留痕完整性。

用法：
    ./guard_batch.py --batch-id R21_XXX_20261124 --phase pre
    ./guard_batch.py --batch-id R21_XXX_20261124 --phase post
    ./guard_batch.py --batch-id R21_XXX_20261124 --phase post --snapshot gov_r21_snapshot

存在意义：v3/v5 发现 R20A_B1_REFILL_A 改了 26,402 行却没有一条 history，
R20B_DETERMINISTIC 改了 14,395 行同样为 0，共 40,797 行永久无法追溯。
本脚本把「有快照、有留痕、行数对得上」变成执行前后的强制检查。

快照表命名历史上不统一（gov_r19_snapshot / gov_r20c3_snapshot / gov_r20b2_snapshot），
故不假设命名，而是按批次号推导候选名，推导失败时列出库中所有快照表供人确认。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import psycopg2

DSN = os.environ.get("GOODS_MDM_PG_DSN", "host=127.0.0.1 port=5432 dbname=goods_mdm user=goods_app")


def fail(msg):
    print(f"  [FAIL] {msg}")


def ok(msg):
    print(f"  [ OK ] {msg}")


def candidates(batch_id):
    """按批次号推导可能的快照表名，从具体到宽泛。"""
    b = batch_id.upper()
    names = []
    m = re.match(r"(R\d+[A-Z0-9]*?)_", b)
    if m:
        names.append(f"gov_{m.group(1).lower()}_snapshot")
        names.append(f"gov_{m.group(1).lower()}snapshot")
    base = re.sub(r"_\d{8}$", "", b).lower()
    names.append(f"gov_{base}_snapshot")
    names.append(f"{base}_snapshot")
    m2 = re.match(r"(R\d+)", b)
    if m2:
        names.append(f"gov_{m2.group(1).lower()}_snapshot")
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def find_snapshot(cur, batch_id, explicit):
    """返回 (表名, 行数) 或 (None, None)。"""
    if explicit:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{explicit}",))
        if cur.fetchone()[0]:
            cur.execute(f'SELECT count(*) FROM "{explicit}"')
            return explicit, cur.fetchone()[0]
        return None, None

    for name in candidates(batch_id):
        cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{name}",))
        if cur.fetchone()[0]:
            cur.execute(f'SELECT count(*) FROM "{name}"')
            return name, cur.fetchone()[0]
    return None, None


def list_snapshots(cur):
    cur.execute(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname='public' AND tablename LIKE '%%snapshot%%' "
        "ORDER BY tablename"
    )
    return [r[0] for r in cur.fetchall()]


def batch_lock_key(batch_id):
    return f"gov-batch:{batch_id}"


def check_pre(cur, batch_id, explicit_snap, require_version=False):
    """执行前：批次已登记、无并发批次、快照表存在且行数匹配。"""
    errors = 0
    cur.execute("SELECT status, input_rows FROM sys_gov_batch WHERE batch_id=%s", (batch_id,))
    row = cur.fetchone()
    if not row:
        fail(f"批次 {batch_id} 未在 sys_gov_batch 登记")
        return 1
    status, input_rows = row
    ok(f"批次已登记，status={status}，input_rows={input_rows}")

    cur.execute("SELECT batch_id FROM sys_gov_batch WHERE status='RUNNING' AND batch_id<>%s", (batch_id,))
    running = [r[0] for r in cur.fetchall()]
    if running:
        fail(f"存在并发运行中的批次：{running}")
        errors += 1
    else:
        ok("无并发运行中的批次")

    cur.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (batch_lock_key(batch_id),))
    if not cur.fetchone()[0]:
        fail("治理批次锁被占用。写入事务须持有 pg_advisory_xact_lock(hashtext('gov-batch:' || batch_id))")
        errors += 1
    else:
        cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (batch_lock_key(batch_id),))
        ok("批次锁当前可用。正式写入必须在同一事务内再次获取该锁")

    snap, n = find_snapshot(cur, batch_id, explicit_snap)
    if not snap:
        fail(f"找不到快照表；候选名 {candidates(batch_id)}")
        print(f"         库中现有快照表：{list_snapshots(cur)[:12]}")
        errors += 1
    elif input_rows and n != input_rows:
        fail(f"快照表 {snap} 行数 {n} != input_rows {input_rows}")
        errors += 1
    else:
        ok(f"快照表 {snap} 行数 {n} 匹配")

    # 回滚要还原的不只是 category_id。mdm_goods 的 governance_batch 是 NOT NULL，
    # 若快照漏存该列，回滚时无法写回原值，只能靠历史快照反推（R21 演练实证）。
    # 故要求快照至少包含 old_cat 与 governance_batch 两列。
    if snap:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s",
            (snap,),
        )
        cols = {r[0].lower() for r in cur.fetchall()}
        # 列名历史上不统一：旧快照用 old_cat，部分批次用 old_batch 而非 governance_batch。
        has_cat = "old_cat" in cols or "old_category" in cols
        has_batch = "governance_batch" in cols or "old_batch" in cols
        if not has_cat:
            fail(f"快照表 {snap} 缺少 old_cat 列，无法还原分类")
            errors += 1
        if not has_batch:
            fail(
                f"快照表 {snap} 缺少 governance_batch / old_batch 列，回滚无法还原批次归属；"
                "该列为 NOT NULL，缺失时须从历史快照反推"
            )
            errors += 1
        if has_cat and has_batch:
            ok("快照含分类与原批次列，可完整回滚")
        if require_version and "version_before" not in cols:
            fail(f"快照表 {snap} 缺少 version_before，不能做版本检查回滚")
            errors += 1
        elif "version_before" in cols:
            ok("快照含 version_before，可按版本做补偿回滚")
    return errors


def check_post(cur, batch_id, explicit_snap):
    """执行后：history 覆盖变更行、批次已收尾、快照仍在。"""
    errors = 0
    cur.execute(
        "SELECT status, recategorized_rows, finished_at, input_rows, output_rows "
        "FROM sys_gov_batch WHERE batch_id=%s",
        (batch_id,),
    )
    row = cur.fetchone()
    if not row:
        fail(f"批次 {batch_id} 不存在")
        return 1
    status, recat, finished_at, input_rows, output_rows = row
    if status == "RUNNING" or finished_at is None:
        fail(f"批次仍是 RUNNING 或无 finished_at（status={status}）")
        errors += 1
    else:
        ok(f"批次已收尾，status={status}")

    cur.execute("SELECT count(*) FROM mdm_goods_history WHERE batch_id=%s", (batch_id,))
    hist = cur.fetchone()[0]
    cur.execute("SELECT count(DISTINCT barcode) FROM mdm_goods_history WHERE batch_id=%s", (batch_id,))
    hist_bc = cur.fetchone()[0]

    # recategorized_rows 为 0 或 NULL 时不能当作「无变更」放过：历史上 R20A_B1_REFILL_A
    # 与 R20B_DETERMINISTIC 正是靠这个字段留空绕过检查，改了 4 万行却零留痕。
    # 故声称变更数取 recat / output_rows / input_rows 三者最大值，全部为 0 才算「确实无变更」。
    claimed = max(recat or 0, output_rows or 0, input_rows or 0)
    if claimed == 0 and hist == 0:
        fail("批次声称变更数与 output/input 均为 0 且无 history，无法核实是否真的未改动数据")
        errors += 1
    elif hist == 0:
        fail(f"声称变更 {claimed} 行但 history 为 0（不可追溯）")
        errors += 1
    elif hist_bc < claimed:
        fail(f"history 覆盖 {hist_bc} 个条码 < 声称变更 {claimed} 行")
        errors += 1
    else:
        ok(f"history {hist} 条 / {hist_bc} 个条码，覆盖声称变更 {claimed} 行")

    snap, n = find_snapshot(cur, batch_id, explicit_snap)
    if snap:
        ok(f"快照表 {snap}（{n} 行）仍存在，可回滚")
    else:
        fail(f"找不到快照表，无法回滚；候选名 {candidates(batch_id)}")
        errors += 1
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    ap.add_argument("--phase", choices=["pre", "post"], required=True)
    ap.add_argument("--snapshot", help="显式指定快照表名，跳过自动推导")
    ap.add_argument("--require-version", action="store_true",
                    help="要求快照含 version_before，否则禁止继续")
    args = ap.parse_args()

    pg = psycopg2.connect(DSN)
    cur = pg.cursor()
    print(f"=== 批次守卫 {args.batch_id} / {args.phase} ===")
    if args.phase == "pre":
        errors = check_pre(cur, args.batch_id, args.snapshot, args.require_version)
    else:
        errors = check_post(cur, args.batch_id, args.snapshot)
    pg.close()
    if errors:
        print(f"\n结论：{errors} 项未通过，禁止继续")
        return 1
    print("\n结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())