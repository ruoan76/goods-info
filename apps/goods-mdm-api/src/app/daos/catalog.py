"""分类 / 属性 / 条码 / 管理后台 DAO。"""
from __future__ import annotations

from typing import Any


# ---------------- 分类 ----------------
def category_tree(cur) -> dict:
    cur.execute(
        """SELECT category_id, parent_id, category_level, category_name, is_leaf,
                  sort_order, status, version
           FROM mdm_category ORDER BY category_level, sort_order, category_id"""
    )
    rows = cur.fetchall()
    # 商品数按分类聚合（一次性 group by，避免 N+1）；category_id 为 NULL 的归入未分类 C00，
    # 与工作台 unclassified 口径一致
    cur.execute(
        "SELECT coalesce(category_id,'C00') AS cid, count(*) FROM mdm_goods GROUP BY 1"
    )
    counts = dict(cur.fetchall())

    nodes: dict[str, dict] = {}
    for r in rows:
        cid, pid, level, name, is_leaf, sort, status, ver = r
        nodes[cid] = {
            "category_id": cid, "parent_id": pid, "name": name, "level": level,
            "count": counts.get(cid, 0), "is_leaf": is_leaf,
            "is_placeholder": cid == "C00", "status": status, "version": ver,
            "children": [],
        }
    tree = []
    for cid, node in nodes.items():
        if node["parent_id"] in nodes:
            nodes[node["parent_id"]]["children"].append(node)
        elif node["parent_id"] is None or node["level"] == 1:
            tree.append(node)
    # 计数逐级向上汇总：rows 按 level 升序插入，倒序遍历即自深层向浅层滚加，
    # 父级 count = 直挂商品 + 全部子孙合计（含未分类 C00 的 197059 挂在根可见）
    for cid in reversed(list(nodes.keys())):
        pid = nodes[cid]["parent_id"]
        if pid in nodes:
            nodes[pid]["count"] += nodes[cid]["count"]
    active = sum(1 for n in nodes.values() if n["status"] == "ACTIVE")
    return {"tree": tree, "total_nodes": len(nodes), "active_nodes": active}


def category_node(cur, cid: str) -> dict | None:
    cur.execute(
        """SELECT category_id, parent_id, category_level, category_name,
                  is_leaf, status, version FROM mdm_category WHERE category_id=%s""",
        (cid,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {"category_id": r[0], "parent_id": r[1], "level": r[2], "name": r[3],
            "is_leaf": r[4], "status": r[5], "version": r[6]}


def category_impact(cur, cid: str) -> dict:
    cur.execute("SELECT count(*) FROM mdm_goods WHERE category_id=%s", (cid,))
    goods = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mdm_category WHERE parent_id=%s", (cid,))
    children = cur.fetchone()[0]
    return {"category_id": cid, "goods_count": goods, "child_count": children,
            "can_delete": goods == 0 and children == 0}


def update_category(cur, cid: str, updates: dict) -> None:
    allowed = {"category_name": "name", "sort_order": "sort_order", "status": "status"}
    sets, args = [], []
    for col, key in allowed.items():
        if key in updates:
            sets.append(f"{col}=%s")
            args.append(updates[key])
    if sets:
        sets.append("version=version+1")
        args.append(cid)
        cur.execute(f"UPDATE mdm_category SET {','.join(sets)} WHERE category_id=%s", args)


def get_template(cur, cid: str) -> dict | None:
    cur.execute(
        "SELECT template, enabled, updated_by, updated_at FROM sys_attr_template WHERE category_id=%s",
        (cid,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {"category_id": cid, "template": r[0], "enabled": r[1],
            "updated_by": r[2], "updated_at": str(r[3])}


def put_template(cur, cid: str, template: dict, operator: str) -> None:
    cur.execute(
        """INSERT INTO sys_attr_template (category_id, template, updated_by)
           VALUES (%s,%s::jsonb,%s)
           ON CONFLICT (category_id) DO UPDATE
           SET template=EXCLUDED.template, updated_by=EXCLUDED.updated_by, updated_at=now()""",
        (cid, __import__("json").dumps(template, ensure_ascii=False), operator),
    )


def external_map(cur, cid: str) -> dict:
    cur.execute(
        """SELECT source_system, source_code, source_name, map_type, confidence,
                  row_count, status FROM mdm_category_map WHERE target_category_id=%s""",
        (cid,),
    )
    rows = cur.fetchall()
    cur.execute(
        "SELECT category_name FROM mdm_category WHERE category_id=%s", (cid,)
    )
    nr = cur.fetchone()
    return {
        "category_id": cid, "category_name": nr[0] if nr else None,
        "mappings": [
            {"source_system": r[0], "source_code": r[1], "source_name": r[2],
             "map_type": r[3], "confidence": str(r[4]) if r[4] is not None else None,
             "row_count": r[5], "status": r[6]} for r in rows
        ],
        "total": len(rows),
    }


def put_external_map(cur, cid: str, mappings: list[dict]) -> int:
    n = 0
    for m in mappings:
        # confidence 不接受前端传入，维持原值或默认
        cur.execute(
            """INSERT INTO mdm_category_map
               (source_system, source_code, source_name, target_category_id, map_type, status)
               VALUES (%s,%s,%s,%s,%s,'ACTIVE')
               ON CONFLICT DO NOTHING""",
            (m.get("source_system"), m.get("source_code"), m.get("source_name"),
             cid, m.get("map_type", "DIRECT")),
        )
        n += cur.rowcount
    return n


# ---------------- 属性 ----------------
def list_attributes(cur, table: str | None = None) -> list[dict]:
    sql = ("SELECT dict_id, table_name, column_name, cn_name, data_type, value_domain "
           "FROM sys_field_dict")
    args: list = []
    if table:
        sql += " WHERE table_name=%s"
        args.append(table)
    sql += " ORDER BY dict_id LIMIT 200"
    cur.execute(sql, args)
    return [{"id": r[0], "table": r[1], "column": r[2], "cn_name": r[3],
             "data_type": r[4], "value_domain": r[5]} for r in cur.fetchall()]


def get_attribute(cur, aid: int) -> dict | None:
    cur.execute(
        "SELECT dict_id, table_name, column_name, cn_name, description, data_type, value_domain "
        "FROM sys_field_dict WHERE dict_id=%s", (aid,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {"id": r[0], "table": r[1], "column": r[2], "cn_name": r[3],
            "description": r[4], "data_type": r[5], "value_domain": r[6]}


def get_goods_attrs(cur, barcode: str) -> dict:
    cur.execute("SELECT attrs_json FROM mdm_goods_attrs WHERE barcode=%s", (barcode,))
    r = cur.fetchone()
    return r[0] if r else {}


def put_goods_attrs(cur, barcode: str, attrs: dict) -> None:
    import json
    cur.execute(
        """INSERT INTO mdm_goods_attrs (barcode, attrs_json, updated_at)
           VALUES (%s,%s::jsonb,now())
           ON CONFLICT (barcode) DO UPDATE
           SET attrs_json=EXCLUDED.attrs_json, updated_at=now()""",
        (barcode, json.dumps(attrs, ensure_ascii=False)),
    )


# ---------------- 来源 ----------------
def list_sources(cur) -> list[dict]:
    cur.execute(
        "SELECT source_code, source_name, enabled FROM sys_source_trust WHERE enabled=1 ORDER BY source_code"
    )
    # 不返回 trust_weight 数字，只给"更可靠/次可靠"展示
    return [{"source_code": r[0], "source_name": r[1],
             "reliability": "更可靠" if r[0] == "MAPPING" else "次可靠"}
            for r in cur.fetchall()]


# ---------------- 隔离区（goods_ro 强制） ----------------
def list_quarantine(cur, params: dict) -> dict:
    where, args = [], []
    if params.get("issue_type"):
        where.append("issue_type=%s"); args.append(params["issue_type"])
    if params.get("batch_id"):
        where.append("batch_id=%s"); args.append(params["batch_id"])
    if params.get("status"):
        where.append("status=%s"); args.append(params["status"])
    wc = ("WHERE " + " AND ".join(where)) if where else ""
    page, size = params.get("page", 1), params.get("page_size", 20)
    cur.execute(f"SELECT count(*) FROM dq_quarantine {wc}", args)
    total = cur.fetchone()[0]
    cur.execute(
        f"""SELECT quarantine_id, batch_id, barcode, issue_type, conflict_field,
                   value_a, value_b, status, created_at FROM dq_quarantine {wc}
            ORDER BY quarantine_id LIMIT %s OFFSET %s""",
        args + [size, (page - 1) * size],
    )
    rows = cur.fetchall()
    return {"items": [{"id": r[0], "batch_id": r[1], "barcode": r[2],
                       "issue_type": r[3], "conflict_field": r[4],
                       "value_a": r[5], "value_b": r[6], "status": r[7],
                       "created_at": str(r[8])} for r in rows],
            "total": total, "page": page, "page_size": size,
            "has_more": page * size < total}


def quarantine_export(cur, params: dict, limit: int = 200000):
    where, args = [], []
    if params.get("issue_type"):
        where.append("issue_type=%s"); args.append(params["issue_type"])
    if params.get("batch_id"):
        where.append("batch_id=%s"); args.append(params["batch_id"])
    wc = ("WHERE " + " AND ".join(where)) if where else ""
    cur.execute(
        f"""SELECT barcode, issue_type, conflict_field, status, created_at
            FROM dq_quarantine {wc} LIMIT %s""", args + [limit]
    )
    return cur.fetchall()
