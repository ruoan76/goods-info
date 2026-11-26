"""管理后台 DAO：dashboard / change-log / users / units / import-jobs。"""
from __future__ import annotations

from typing import Any


def dashboard(cur) -> dict:
    # 精确总数（索引扫描 ~1s；reltuples 估算在批量治理期漂移达数百条，不可用）
    cur.execute("SELECT count(*) FROM mdm_goods")
    total = cur.fetchone()[0]
    # 精确待办（走索引/条件计数）
    cur.execute("SELECT count(*) FROM mdm_goods WHERE inprice IS NULL OR inprice=0 OR outprice IS NULL OR outprice=0")
    price_pending = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mdm_goods WHERE category_id='C00'")
    unclassified = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mdm_category WHERE category_level=1")
    l1 = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mdm_category WHERE category_level=2 AND status='ACTIVE'")
    l2_active = cur.fetchone()[0]
    return {
        "goods_total": total, "goods_total_approx": False,
        "category_l1": l1, "category_l2_active": l2_active,
        "price_pending": price_pending, "unclassified": unclassified,
        "updated_at": None,
    }


def dashboard_quarantine(cur_ro) -> int:
    """隔离区计数走 goods_ro 连接。"""
    cur_ro.execute("SELECT count(*) FROM dq_quarantine WHERE status='OPEN'")
    return cur_ro.fetchone()[0]


def quality_metrics(cur) -> dict:
    """分类治理质量指标（v10 环境评审要求的三项只读看板指标）。

    - c00_semantic: C00 中「有语义中文名」的行数，即真正待处理的部分；
      C00 里纯数字/符号名是合法驻留，不计入。
    - cross_bucket_names: 精确名散布 >=10 个不同分类的名称数，衡量分类一致性。
      全表 GROUP BY 约 52s，不适合放在每次刷新的看板上，改为按需触发的快照。
    - history_coverage: 近 30 天批次声称变更的行数中，有多少能在
      mdm_goods_history 里找到同条码记录。

    性能取舍：cross_bucket_names 走全表聚合（52s），dashboard 每次刷新都跑会拖垮
    接口。故只保留两个快指标（均 <1.5s），cross_bucket_names 由离线脚本写入
    sys_quality_snapshot，看板只读最后快照。
    """
    cur.execute(
        """SELECT count(*) FROM mdm_goods
           WHERE category_id='C00' AND goods_name ~ '[一-龥]' AND length(trim(goods_name))>=3"""
    )
    c00_semantic = cur.fetchone()[0]

    cur.execute(
        """SELECT coalesce(sum(b.input_rows), 0)
           FROM sys_gov_batch b
           WHERE b.started_at::timestamptz >= now() - interval '30 days'"""
    )
    claimed = cur.fetchone()[0] or 0
    cur.execute(
        """SELECT count(DISTINCT h.barcode) FROM mdm_goods_history h
           WHERE h.changed_at >= now() - interval '30 days'"""
    )
    traced = cur.fetchone()[0] or 0
    coverage = round(min(traced / claimed, 1.0), 4) if claimed else None

    # 快照表可能尚未建立，缺失时返回 None 而不是让看板整体失败
    cross_bucket_names = None
    cross_bucket_at = None
    try:
        cur.execute(
            """SELECT value_int, measured_at FROM sys_quality_snapshot
               WHERE metric='cross_bucket_names' ORDER BY measured_at DESC LIMIT 1"""
        )
        row = cur.fetchone()
        if row:
            cross_bucket_names, cross_bucket_at = row[0], row[1]
    except Exception:  # noqa: BLE001 - 快照表未建时看板仍需可用
        cur.connection.rollback()

    return {
        "c00_semantic": c00_semantic,
        "cross_bucket_names": cross_bucket_names,
        "cross_bucket_measured_at": cross_bucket_at,
        "history_coverage": coverage,
    }


def change_log(cur, limit: int = 10, operator: str | None = None) -> dict:
    limit = min(limit, 50)
    where, args = "", []
    if operator:
        where = "WHERE operator=%s"; args.append(operator)
    cur.execute(f"SELECT count(*) FROM sys_change_log {where}", args)
    total = cur.fetchone()[0]
    cur.execute(
        f"""SELECT log_id, operator, action, entity_key, before_data, after_data, changed_at
            FROM sys_change_log {where} ORDER BY changed_at DESC LIMIT %s""",
        args + [limit],
    )
    items = []
    for r in cur.fetchall():
        before = r[4] or {}
        after = r[5] or {}
        # 提取单字段前后值供时间轴展示
        field, old_v, new_v = None, None, None
        if isinstance(after, dict):
            for k, v in after.items():
                if k not in ("batch_id", "version"):
                    field = k; new_v = v; old_v = before.get(k) if isinstance(before, dict) else None
                    break
        items.append({
            "id": r[0], "operator": r[1], "action": r[2], "target": r[3],
            "field": field, "old_value": str(old_v) if old_v is not None else None,
            "new_value": str(new_v) if new_v is not None else None,
            "changed_at": str(r[6]),
        })
    return {"items": items, "total": total}


def list_users(cur, q: str | None, role: str | None, status: str | None) -> dict:
    where, args = [], []
    if q:
        where.append("(account ILIKE %s OR display_name ILIKE %s)")
        args.extend([f"%{q}%", f"%{q}%"])
    if role:
        where.append("role=%s"); args.append(role)
    if status:
        where.append("status=%s"); args.append(status)
    wc = ("WHERE " + " AND ".join(where)) if where else ""
    cur.execute(f"SELECT count(*) FROM sys_user {wc}", args)
    total = cur.fetchone()[0]
    cur.execute(
        f"""SELECT account, display_name, role, status, dept, phone, last_login
            FROM sys_user {wc} ORDER BY account LIMIT 200""", args
    )
    role_perms = {
        "Viewer": ["goods:read", "category:read", "export", "quarantine:read"],
        "Operator": ["goods:read", "goods:write", "goods:import", "attrs:write"],
        "Steward": ["*"],
    }
    items = [{
        "account": r[0], "name": r[1], "role": r[2], "status": r[3],
        "dept": r[4], "phone": r[5], "last_login": str(r[6]) if r[6] else None,
        "permission_codes": role_perms.get(r[2], []),
    } for r in cur.fetchall()]
    return {"items": items, "total": total}


def create_user(cur, account: str, name: str, role: str, pwd_hash: str,
                dept: str | None, phone: str | None) -> None:
    cur.execute(
        """INSERT INTO sys_user (account, display_name, role, status, password_hash, dept, phone)
           VALUES (%s,%s,%s,'ACTIVE',%s,%s,%s)""",
        (account, name, role, pwd_hash, dept, phone),
    )


def update_user(cur, account: str, updates: dict) -> None:
    mapping = {"name": "display_name", "role": "role", "status": "status",
               "dept": "dept", "phone": "phone"}
    sets, args = [], []
    for key, col in mapping.items():
        if key in updates and updates[key] is not None:
            sets.append(f"{col}=%s"); args.append(updates[key])
    if sets:
        args.append(account)
        cur.execute(f"UPDATE sys_user SET {','.join(sets)}, updated_at=now() WHERE account=%s", args)


def reset_password(cur, account: str, pwd_hash: str) -> None:
    cur.execute(
        "UPDATE sys_user SET password_hash=%s, token_version=token_version+1, updated_at=now() WHERE account=%s",
        (pwd_hash, account),
    )


def list_units(cur) -> list[dict]:
    cur.execute(
        "SELECT code, name, sort_order, enabled, goods_count FROM sys_unit ORDER BY sort_order, code"
    )
    return [{"code": r[0], "name": r[1], "sort_order": r[2],
             "enabled": r[3], "goods_count": r[4]} for r in cur.fetchall()]


def create_unit(cur, code: str, name: str, sort: int, enabled: bool) -> None:
    cur.execute(
        "INSERT INTO sys_unit (code, name, sort_order, enabled) VALUES (%s,%s,%s,%s)",
        (code, name, sort, enabled),
    )


def update_unit(cur, code: str, updates: dict) -> None:
    sets, args = [], []
    for key in ("name", "sort_order", "enabled"):
        if key in updates and updates[key] is not None:
            sets.append(f"{key}=%s"); args.append(updates[key])
    if sets:
        args.append(code)
        cur.execute(f"UPDATE sys_unit SET {','.join(sets)}, updated_at=now() WHERE code=%s", args)


def get_import_job(cur, job_id: int) -> dict | None:
    cur.execute(
        """SELECT id, batch_id, job_type, operator, total_rows, success_rows,
                  fail_rows, fail_detail, status, created_at, finished_at
           FROM sys_import_job WHERE id=%s""", (job_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {"id": r[0], "batch_id": r[1], "job_type": r[2], "operator": r[3],
            "total_rows": r[4], "success_rows": r[5], "fail_rows": r[6],
            "fail_detail": r[7], "status": r[8],
            "created_at": str(r[9]), "finished_at": str(r[10]) if r[10] else None}


def create_import_job(cur, batch_id: str, job_type: str, operator: str, total: int) -> int:
    cur.execute(
        """INSERT INTO sys_import_job (batch_id, job_type, operator, total_rows, status)
           VALUES (%s,%s,%s,%s,'RUNNING') RETURNING id""",
        (batch_id, job_type, operator, total),
    )
    return cur.fetchone()[0]


def update_import_job(cur, job_id: int, success: int, fail: int,
                      fail_detail: list, status: str) -> None:
    import json
    cur.execute(
        """UPDATE sys_import_job SET success_rows=%s, fail_rows=%s,
                  fail_detail=%s::jsonb, status=%s,
                  finished_at=CASE WHEN %s='RUNNING' THEN NULL ELSE now() END WHERE id=%s""",
        (success, fail, json.dumps(fail_detail, ensure_ascii=False), status, status, job_id),
    )


def mark_import_interrupted(cur, job_id: int) -> None:
    cur.execute(
        """UPDATE sys_import_job
           SET status = CASE WHEN success_rows > 0 THEN 'PARTIAL' ELSE 'FAILED' END,
               finished_at = now()
           WHERE id = %s AND status = 'RUNNING'""",
        (job_id,),
    )
