"""商品 DAO：分页查询 / 详情 / 历史 / 写库。所有 SQL 参数化。"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core.errors import CODE_DEEP_PAGE, BizError

SORT_WHITELIST = {"updated_at", "goods_name", "outprice"}


def _build_filter(params: dict) -> tuple[str, list]:
    where: list[str] = []
    args: list[Any] = []
    if params.get("category_id"):
        where.append("g.category_id = %s")
        args.append(params["category_id"])
    if params.get("q"):
        where.append("(g.barcode = %s OR g.goods_name ILIKE %s)")
        args.extend([params["q"], f"%{params['q']}%"])
    if params.get("source"):
        where.append("g.category_source = %s")
        args.append(params["source"])
    if params.get("grade"):
        where.append("g.quality_grade = %s")
        args.append(params["grade"])
    if params.get("status"):
        where.append("g.status = %s")
        args.append(params["status"])
    if params.get("price_state") in ("priced", "unpriced"):
        if params["price_state"] == "unpriced":
            where.append("(g.inprice IS NULL OR g.inprice=0 OR g.outprice IS NULL OR g.outprice=0)")
        else:
            where.append("(g.inprice>0 AND g.outprice>0)")
    return (" AND ".join(where) if where else ""), args


def list_goods(cur, params: dict) -> dict:
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    if page * page_size > 100000:
        raise BizError(CODE_DEEP_PAGE)
    sort_by = params.get("sort_by", "updated_at")
    if sort_by not in SORT_WHITELIST:
        sort_by = "updated_at"
    order = "ASC" if params.get("order", "desc").lower() == "asc" else "DESC"

    where_sql, args = _build_filter(params)
    where_clause = ("WHERE " + where_sql) if where_sql else ""

    # total：当前筛选精确计数（带条件）
    cur.execute(f"SELECT count(*) FROM mdm_goods g {where_clause}", args)
    total = cur.fetchone()[0]
    # total_approx：全表近似（pg_class.reltuples）
    cur.execute("SELECT reltuples::bigint FROM pg_class WHERE relname='mdm_goods'")
    approx = cur.fetchone()[0]

    offset = (page - 1) * page_size
    cur.execute(
        f"""SELECT g.barcode, g.goods_name, g.category_id, g.category_path,
                   g.unit_id, u.name, g.inprice, g.outprice, g.quality_grade,
                   g.status, g.version, g.updated_at,
                   c.category_name
            FROM mdm_goods g
            LEFT JOIN sys_unit u ON u.code = g.unit_id
            LEFT JOIN mdm_category c ON c.category_id = g.category_id
            {where_clause}
            ORDER BY g.{sort_by} {order}
            LIMIT %s OFFSET %s""",
        args + [page_size, offset],
    )
    rows = cur.fetchall()
    items = []
    for r in rows:
        items.append({
            "barcode": r[0], "goods_name": r[1], "category_id": r[2],
            "category_code_path": r[3], "category_path": r[12] or r[3],
            "unit_id": r[4], "unit_name": r[5],
            "inprice": str(r[6]) if r[6] is not None else None,
            "outprice": str(r[7]) if r[7] is not None else None,
            "quality_grade": r[8], "status": r[9], "version": r[10],
            "updated_at": str(r[11]),
        })
    return {
        "items": items, "total": total, "total_approx": int(approx or 0),
        "page": page, "page_size": page_size,
        "has_more": offset + len(items) < total,
    }


def get_goods(cur, barcode: str) -> dict | None:
    cur.execute(
        """SELECT g.barcode, g.goods_name, g.category_id, g.category_path,
                  g.category_source, g.unit_id, u.name, g.inprice, g.outprice,
                  g.quality_grade, g.quality_score, g.status, g.version, g.updated_at,
                  c.category_name, c.category_level
           FROM mdm_goods g
           LEFT JOIN sys_unit u ON u.code=g.unit_id
           LEFT JOIN mdm_category c ON c.category_id=g.category_id
           WHERE g.barcode=%s""",
        (barcode,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {
        "barcode": r[0], "goods_name": r[1], "category_id": r[2],
        "category_code_path": r[3], "category_source": r[4],
        "category_path": r[14] or r[3], "category_level": r[15],
        "unit_id": r[5], "unit_name": r[6],
        "inprice": str(r[7]) if r[7] is not None else None,
        "outprice": str(r[8]) if r[8] is not None else None,
        "quality_grade": r[9], "quality_score": str(r[10]) if r[10] is not None else None,
        "status": r[11], "version": r[12], "updated_at": str(r[13]),
    }


def get_history(cur, barcode: str) -> list[dict]:
    cur.execute(
        """SELECT field_name, old_value, new_value, rule_code, batch_id, changed_at
           FROM mdm_goods_history WHERE barcode=%s ORDER BY changed_at DESC LIMIT 100""",
        (barcode,),
    )
    return [
        {"field": r[0], "old_value": r[1], "new_value": r[2], "rule_code": r[3],
         "batch_id": r[4], "changed_at": str(r[5])}
        for r in cur.fetchall()
    ]


def name_hits(cur, goods_name: str, exclude_barcode: str | None = None) -> dict:
    args: list = [f"%{goods_name}%"]
    sql = "SELECT barcode, goods_name FROM mdm_goods WHERE goods_name ILIKE %s"
    if exclude_barcode:
        sql += " AND barcode<>%s"
        args.append(exclude_barcode)
    sql += " LIMIT 6"
    cur.execute(sql, args)
    rows = cur.fetchall()
    # similar_count 用带条件的 count（ILIKE 相似度，40.6% 同名基数下不自动合并）
    cur.execute(
        "SELECT count(*) FROM mdm_goods WHERE goods_name ILIKE %s"
        + (" AND barcode<>%s" if exclude_barcode else ""),
        args[:-1] if exclude_barcode else args,
    )
    return {"hit": len(rows) > 0, "similar_count": cur.fetchone()[0],
            "sample": [r[1] for r in rows]}


def create_goods(cur, data: dict, batch_id: str, operator: str) -> None:
    cur.execute(
        """INSERT INTO mdm_goods
           (barcode, goods_name, category_id, unit_id, inprice, outprice,
            quality_grade, status, version, governance_batch, created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',1,%s,now()::text,now()::text)""",
        (data["barcode"], data["goods_name"], data.get("category_id"),
         data.get("unit_id"), data.get("inprice"), data.get("outprice"),
         data.get("quality_grade", "C"), batch_id),
    )


def patch_field(cur, barcode: str, field: str, new_value: Any, expected_version: int) -> dict:
    # 金额字段转 Decimal；白名单外的字段已被 schema 拦截
    val = Decimal(new_value) if field in ("inprice", "outprice") else new_value
    cur.execute(
        f"SELECT {field}, version FROM mdm_goods WHERE barcode=%s FOR UPDATE", (barcode,)
    )
    row = cur.fetchone()
    if not row:
        return {}
    old, ver = row
    cur.execute(
        f"""UPDATE mdm_goods SET {field}=%s, version=version+1, updated_at=now()::text
            WHERE barcode=%s AND version=%s""",
        (val, barcode, expected_version),
    )
    if cur.rowcount == 0:
        return {"conflict": True}
    return {"old_value": str(old) if old is not None else None,
            "new_value": str(val), "version": ver + 1}


def set_status(cur, barcode: str, to_status: str) -> None:
    cur.execute(
        "UPDATE mdm_goods SET status=%s, version=version+1, updated_at=now()::text WHERE barcode=%s",
        (to_status, barcode),
    )


def set_category(cur, barcode: str, category_id: str) -> None:
    cur.execute(
        "UPDATE mdm_goods SET category_id=%s, version=version+1, updated_at=now()::text WHERE barcode=%s",
        (category_id, barcode),
    )


def export_rows(cur, params: dict, limit: int = 200000):
    where_sql, args = _build_filter(params)
    where_clause = ("WHERE " + where_sql) if where_sql else ""
    cur.execute(
        f"""SELECT g.barcode, g.goods_name, p.category_name, c.category_name, u.name,
                   g.inprice, g.outprice, g.quality_grade, g.status, g.updated_at
            FROM mdm_goods g
            LEFT JOIN mdm_category c ON c.category_id=g.category_id
            LEFT JOIN mdm_category p ON p.category_id=c.parent_id
            LEFT JOIN sys_unit u ON u.code=g.unit_id
            {where_clause} LIMIT %s""",
        args + [limit],
    )
    return cur.fetchall()
