"""属性域 3 端点。"""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, UploadFile

from ..core import auth as A
from ..core.audit import audit, gen_batch_id
from ..core.db import conn_app
from ..core.errors import ok
from ..daos import catalog as dc

router = APIRouter(prefix="/attributes", tags=["属性"])


@router.get("", summary="属性定义批量查询")
def list_attrs(table: str | None = None, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.list_attributes(cur, table))


@router.get("/{aid}", summary="属性定义明细")
def get_attr(aid: int, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.get_attribute(cur, aid))


@router.post("/import", summary="CSV 属性批量回填")
async def import_attrs(
    file: UploadFile = File(...), user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))
):
    content = (await file.read()).decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(content)))
    batch = gen_batch_id(user["account"])
    success, failures = 0, []
    with conn_app() as c, c.cursor() as cur:
        for idx, row in enumerate(rows, start=2):
            barcode = (row.get("条码") or row.get("barcode") or "").strip()
            key = row.get("属性名") or row.get("key")
            value = row.get("属性值") or row.get("value")
            if not barcode or not key:
                failures.append({"row": idx, "reason": "缺条码或属性名"}); continue
            try:
                old = dc.get_goods_attrs(cur, barcode)
                old[key] = value
                dc.put_goods_attrs(cur, barcode, old)
                success += 1
            except Exception as e:
                failures.append({"row": idx, "reason": str(e)[:120]})
        audit(cur, entity_type="ATTRS", entity_key="BATCH", action="ATTRS_IMPORT",
              operator=user["account"], after={"total": len(rows), "success": success},
              batch_id=batch)
    return ok({"total": len(rows), "success": success,
               "failed": len(failures), "fail_detail": failures[:50]})
