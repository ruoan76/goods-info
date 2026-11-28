"""商品域 11 端点（含真实 CSV 导入）。"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from psycopg2 import DataError, IntegrityError
from pydantic import ValidationError

from ..core import auth as A
from ..core.audit import audit, audit_goods_history, gen_batch_id
from ..core.db import conn_app
from ..core.streaming import ClosingStreamingResponse
from ..core.errors import CODE_ATTR_REQUIRED, CODE_VERSION_CONFLICT, BizError, ok
from ..daos import catalog as dc
from ..daos import goods as dg
from ..daos import admin as da
from ..schemas.goods import (
    AttrsWriteBody, CategoryChangeBody, GoodsCheckBody, GoodsCreate,
    PatchBody, StatusChangeBody,
)
from ..services import ironrules as ir

router = APIRouter(prefix="/goods", tags=["商品"])
_log = logging.getLogger(__name__)


def _q(
    category_id: str | None = None, q: str | None = None, source: str | None = None,
    grade: str | None = None, status: str | None = None,
    price_state: str | None = None, page: int = 1, page_size: int = 20,
    sort_by: str = "updated_at", order: str = "desc",
) -> dict:
    return dict(category_id=category_id, q=q, source=source, grade=grade,
                status=status, price_state=price_state, page=page,
                page_size=page_size, sort_by=sort_by, order=order)


# ---------- 1. 分页查询 ----------
@router.get("", summary="商品分页查询")
def list_goods(params: dict = Depends(_q), _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dg.list_goods(cur, params))


# ---------- 2. 导出（必须在 /{barcode} 之前注册） ----------
@router.get("/export", summary="流式 CSV 导出")
def export_goods(params: dict = Depends(_q), user: dict = Depends(A.require_role(*A.ALL_ROLES))):
    limit, batch_size = 200000, 2000
    batch = gen_batch_id(user["account"])
    # Fail audit permission/availability before starting an HTTP response.
    with conn_app() as c, c.cursor() as cur:
        audit(cur, entity_type="EXPORT", entity_key="goods", action="EXPORT",
              operator=user["account"], after={"filters": params, "limit": limit,
                                              "state": "STARTED"}, batch_id=batch)

    def gen():
        emitted, truncated, state = 0, False, "INTERRUPTED"
        try:
            with conn_app() as c, c.cursor(name="goods_export") as cur:
                sql, args = dg.export_query(params, limit + 1)
                cur.itersize = batch_size
                cur.execute(sql, args)
                buf = io.StringIO()
                w = csv.writer(buf)
                columns = ["条码", "商品名称", "上级分类", "分类", "单位",
                           "进价", "售价", "等级", "状态", "更新时间"]
                w.writerow(columns)
                yield "\ufeff" + buf.getvalue()
                buf.seek(0); buf.truncate(0)
                while emitted < limit:
                    rows = cur.fetchmany(min(batch_size, limit - emitted))
                    if not rows:
                        break
                    for r in rows:
                        barcode, name, parent, category, unit, inprice, outprice, grade, status, updated_at = r
                        w.writerow([barcode, name, parent or "", category or "", unit or "",
                                    inprice, outprice, grade, status, updated_at])
                    emitted += len(rows)
                    yield buf.getvalue()
                    buf.seek(0); buf.truncate(0)
                truncated = emitted == limit and bool(cur.fetchmany(1))
                if truncated:
                    w.writerow(["#", "已达到导出上限 200000 行，结果已截断，请缩小筛选范围"]
                               + [""] * (len(columns) - 2))
                    yield buf.getvalue()
                state = "COMPLETED"
        finally:
            # The producer's DB connection is released before opening the audit
            # transaction. Preserve partial-export evidence on errors/disconnect.
            with conn_app() as c, c.cursor() as cur:
                audit(cur, entity_type="EXPORT", entity_key="goods", action="EXPORT_RESULT",
                      operator=user["account"], after={"filters": params, "rows": emitted,
                          "limit": limit, "truncated": truncated, "state": state}, batch_id=batch)

    return ClosingStreamingResponse(
        gen(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="goods_export.csv"',
                 "X-Export-Limit": str(limit)},
    )


# ---------- 3. 查重（必须在 /{barcode} 之前） ----------
@router.post("/check", summary="两段式查重")
def check(body: GoodsCheckBody, _: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        r = ir.check_duplicate(cur, body.barcode, body.goods_name)
        name_hit = dg.name_hits(cur, body.goods_name)
    if r["verdict"] == "BLOCK":
        reason = "条码已被占用，不能重复建档" if r["barcode_exist"]["hit"] else "条码曾作为别名登记，禁止复用"
    elif r["verdict"] == "WARN":
        reason = "疑似同名商品，请人工核对"
    else:
        reason = "未发现重复，可建档"
    return ok({
        "barcode_hit": {"hit": r["barcode_exist"]["hit"], "barcode": body.barcode},
        "name_hit": name_hit,
        "alias_reverse": {"hit": r["alias_reverse"]["hit"]},
        "verdict": r["verdict"], "reason": reason,
    })


# ---------- 4. 导入（必须在 /{barcode} 之前） ----------
@router.post("/import", summary="CSV 新品批量导入（500 行/批事务）")
def import_goods(
    file: UploadFile = File(..., description="CSV 文件：条码,商品名称,分类ID,单位,进价,售价,等级"),
    user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD)),
):
    limit = 50 * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail="CSV 文件超过 50 MiB")
    try:
        content = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
        columns = set(reader.fieldnames or ())
        if not columns.intersection({"条码", "barcode"}) or not columns.intersection({"商品名称", "goods_name"}):
            raise HTTPException(status_code=422, detail="CSV 缺少条码或商品名称列")
        rows = [(reader.line_num, row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as exc:
        raise HTTPException(status_code=422, detail="CSV 格式无效，需使用 UTF-8 编码") from exc

    operator = user["account"]
    batch = gen_batch_id(operator)
    with conn_app() as c, c.cursor() as cur:
        job_id = da.create_import_job(cur, batch, "GOODS_IMPORT", operator, len(rows))

    success = failed = 0
    failures = []
    try:
        for offset in range(0, len(rows), 500):
            batch_success = batch_failed = 0
            batch_failures = []
            with conn_app() as c, c.cursor() as cur:
                for line, row in rows[offset:offset + 500]:
                    cur.execute("SAVEPOINT goods_import_row")
                    try:
                        _import_goods_row(cur, row, batch, operator)
                    except (BizError, ValidationError, DataError, IntegrityError) as exc:
                        cur.execute("ROLLBACK TO SAVEPOINT goods_import_row")
                        batch_failed += 1
                        if len(failures) + len(batch_failures) < 50:
                            reason = exc.message if isinstance(exc, BizError) else "商品字段或数据库约束校验失败"
                            batch_failures.append({"row": line, "reason": reason})
                    else:
                        batch_success += 1
                    cur.execute("RELEASE SAVEPOINT goods_import_row")

                complete = offset + 500 >= len(rows)
                next_success = success + batch_success
                next_failed = failed + batch_failed
                status = "RUNNING"
                if complete:
                    status = "PARTIAL" if next_success and next_failed else "FAILED" if next_failed else "SUCCESS"
                da.update_import_job(cur, job_id, next_success, next_failed, failures + batch_failures, status)
            success, failed = next_success, next_failed
            failures.extend(batch_failures)
        if not rows:
            with conn_app() as c, c.cursor() as cur:
                da.update_import_job(cur, job_id, 0, 0, [], "SUCCESS")
    except Exception:
        try:
            with conn_app() as c, c.cursor() as cur:
                da.mark_import_interrupted(cur, job_id)
        except Exception:
            _log.exception("Unable to close interrupted goods import job %s", job_id)
        raise

    return ok({"job_id": job_id, "batch_id": batch, "total": len(rows),
               "success": success, "failed": failed, "fail_detail": failures})


def _import_goods_row(cur, row, batch: str, operator: str) -> None:
    barcode = (row.get("条码") or row.get("barcode") or "").strip()
    name = (row.get("商品名称") or row.get("goods_name") or "").strip()
    ir.assert_barcode_admissible(barcode)
    goods = GoodsCreate(
        barcode=barcode, goods_name=name,
        category_id=row.get("分类ID") or row.get("category_id") or None,
        unit_id=row.get("单位") or row.get("unit_id") or None,
        inprice=row.get("进价") or row.get("inprice") or None,
        outprice=row.get("售价") or row.get("outprice") or None,
        quality_grade=(row.get("等级") or row.get("quality_grade") or "C").strip() or "C",
    )
    ir.assert_can_create(cur, barcode, name)
    dg.create_goods(cur, goods.model_dump(exclude={"attrs"}), batch, operator)
    audit_goods_history(cur, barcode=barcode, field_name="CREATE",
                        old_value=None, new_value=name, operator=operator,
                        rule_code="IMPORT", batch_id=batch)


# ---------- 5. 详情（/{barcode} 系列） ----------
@router.get("/{barcode}", summary="商品详情")
def goods_detail(barcode: str, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        goods = dg.get_goods(cur, barcode)
        if not goods:
            return ok(None)
        goods["history"] = dg.get_history(cur, barcode)
        tpl = dc.get_template(cur, goods.get("category_id") or "")
        goods["required_attrs"] = (tpl or {}).get("template", {}).get("required", [])
        return ok(goods)


@router.post("", summary="建档（铁律①②生效点）")
def create(body: GoodsCreate, user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    ir.assert_barcode_admissible(body.barcode)
    with conn_app() as c, c.cursor() as cur:
        ir.assert_can_create(cur, body.barcode, body.goods_name)
        batch = gen_batch_id(user["account"])
        data = body.model_dump(exclude={"attrs"})
        dg.create_goods(cur, data, batch, user["account"])
        if body.attrs:
            dc.put_goods_attrs(cur, body.barcode, body.attrs)
        audit_goods_history(cur, barcode=body.barcode, field_name="CREATE",
                            old_value=None, new_value=body.goods_name,
                            operator=user["account"], rule_code="CREATE", batch_id=batch)
        audit(cur, entity_type="GOODS", entity_key=body.barcode, action="CREATE",
              operator=user["account"], after=data, batch_id=batch)
    return ok({"barcode": body.barcode, "version": 1, "status": "ACTIVE"})


@router.patch("/{barcode}", summary="字段即点即改")
def patch(barcode: str, body: PatchBody, user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        result = dg.patch_field(cur, barcode, body.field, body.new_value, body.version)
        if not result:
            return ok(None)
        if result.get("conflict"):
            raise BizError(CODE_VERSION_CONFLICT)
        batch = gen_batch_id(user["account"])
        audit_goods_history(cur, barcode=barcode, field_name=body.field,
                            old_value=result["old_value"], new_value=result["new_value"],
                            operator=user["account"], rule_code="FIELD_EDIT", batch_id=batch)
        audit(cur, entity_type="GOODS", entity_key=barcode, action="FIELD_EDIT",
              operator=user["account"], before={body.field: result["old_value"]},
              after={body.field: result["new_value"]}, batch_id=batch)
    return ok({"barcode": barcode, "field": body.field,
               "old_value": result["old_value"], "new_value": result["new_value"],
               "version": result["version"]})


@router.post("/{barcode}/category", summary="调整分类")
def change_category(barcode: str, body: CategoryChangeBody,
                    user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        cur.execute("SELECT category_id FROM mdm_goods WHERE barcode=%s FOR UPDATE", (barcode,))
        row = cur.fetchone()
        if not row:
            return ok(None)
        old = row[0]
        dg.set_category(cur, barcode, body.category_id)
        batch = gen_batch_id(user["account"])
        audit_goods_history(cur, barcode=barcode, field_name="category_id",
                            old_value=old, new_value=body.category_id,
                            operator=user["account"], rule_code="CATEGORY_CHANGE", batch_id=batch)
        audit(cur, entity_type="GOODS", entity_key=barcode, action="CATEGORY_CHANGE",
              operator=user["account"], before={"category_id": old},
              after={"category_id": body.category_id}, batch_id=batch)
    return ok({"barcode": barcode, "category_id": body.category_id})


@router.post("/{barcode}/status", summary="状态流转")
def change_status(barcode: str, body: StatusChangeBody,
                  user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        old = ir.assert_status_transition(cur, barcode, body.to_status)
        dg.set_status(cur, barcode, body.to_status)
        batch = gen_batch_id(user["account"])
        if body.to_status == "VOIDED":
            ir.register_voided_ban(cur, barcode, user["account"], batch)
        audit_goods_history(cur, barcode=barcode, field_name="status",
                            old_value=old, new_value=body.to_status,
                            operator=user["account"], rule_code="STATUS_CHANGE", batch_id=batch)
        audit(cur, entity_type="GOODS", entity_key=barcode, action="STATUS_CHANGE",
              operator=user["account"], before={"status": old},
              after={"status": body.to_status, "reason": body.reason}, batch_id=batch)
    return ok({"barcode": barcode, "from": old, "to": body.to_status})


@router.get("/{barcode}/attrs", summary="属性读取")
def get_attrs(barcode: str, _: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.get_goods_attrs(cur, barcode))


@router.put("/{barcode}/attrs", summary="属性写入")
def put_attrs(barcode: str, body: AttrsWriteBody,
              user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        cur.execute("SELECT category_id FROM mdm_goods WHERE barcode=%s", (barcode,))
        r = cur.fetchone()
        if not r:
            return ok(None)
        tpl = dc.get_template(cur, r[0] or "")
        required = (tpl or {}).get("template", {}).get("required", [])
        missing = [k for k in required if k not in body.attrs]
        if missing:
            raise BizError(CODE_ATTR_REQUIRED, f"缺少必填属性: {missing}")
        old = dc.get_goods_attrs(cur, barcode)
        dc.put_goods_attrs(cur, barcode, body.attrs)
        batch = gen_batch_id(user["account"])
        audit(cur, entity_type="GOODS_ATTRS", entity_key=barcode, action="ATTRS_WRITE",
              operator=user["account"], before=old, after=body.attrs, batch_id=batch)
    return ok({"barcode": barcode, "attrs": body.attrs})
