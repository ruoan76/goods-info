"""属性域 3 端点。"""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from psycopg2 import Error as DbError

from ..core import auth as A
from ..core.audit import audit, gen_batch_id
from ..core.db import conn_app
from ..core.errors import BizError, ok
from ..services.attrs import write_goods_attrs

router = APIRouter(prefix="/attributes", tags=["属性"])
_ATTR_LIMIT = 50 * 1024 * 1024
_ATTR_ROW_LIMIT = 20000


@router.get("", summary="属性定义批量查询")
def list_attrs(table: str | None = None, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    from ..daos.catalog import list_attributes
    with conn_app() as c, c.cursor() as cur:
        return ok(list_attributes(cur, table))


@router.get("/{aid}", summary="属性定义明细")
def get_attr(aid: int, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    from ..daos.catalog import get_attribute
    with conn_app() as c, c.cursor() as cur:
        return ok(get_attribute(cur, aid))


@router.post("/import", summary="CSV 属性批量回填")
def import_attrs(
    file: UploadFile = File(...), user: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))
):
    data = file.file.read(_ATTR_LIMIT + 1)
    if len(data) > _ATTR_LIMIT:
        raise HTTPException(status_code=413, detail="CSV 文件超过 50 MiB")
    try:
        content = data.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(content, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise HTTPException(status_code=422, detail="CSV 格式无效，需使用 UTF-8 编码") from exc
    if len(rows) > _ATTR_ROW_LIMIT:
        raise HTTPException(status_code=422, detail="CSV 超过 20000 行")

    batch = gen_batch_id(user["account"])
    success = 0
    failures: list[dict] = []
    with conn_app() as c, c.cursor() as cur:
        for idx, row in enumerate(rows, start=2):
            cur.execute("SAVEPOINT attr_row")
            try:
                barcode = (row.get("条码") or row.get("barcode") or "").strip()
                key = (row.get("属性名") or row.get("key") or "").strip()
                if not barcode or not key:
                    raise BizError(3006, "缺条码或属性名")
                value = row.get("属性值") if "属性值" in row else row.get("value")
                written = write_goods_attrs(cur, barcode, {key: value}, merge=True)
                if written is None:
                    raise BizError(3006, "商品不存在")
                audit(cur, entity_type="GOODS_ATTRS", entity_key=barcode, action="ATTRS_IMPORT",
                      operator=user["account"], before=written["old"], after=written["new"],
                      batch_id=batch)
                success += 1
            except (BizError, DbError) as exc:
                cur.execute("ROLLBACK TO SAVEPOINT attr_row")
                if len(failures) < 50:
                    reason = exc.message if isinstance(exc, BizError) else "属性或数据库约束校验失败"
                    failures.append({"row": idx, "reason": reason})
            cur.execute("RELEASE SAVEPOINT attr_row")
        audit(cur, entity_type="ATTRS", entity_key="BATCH", action="ATTRS_IMPORT",
              operator=user["account"],
              after={"total": len(rows), "success": success, "failed": len(rows) - success},
              batch_id=batch)
    failed = len(rows) - success
    return ok({"total": len(rows), "success": success, "failed": failed,
               "fail_detail": failures, "failures": failures})
