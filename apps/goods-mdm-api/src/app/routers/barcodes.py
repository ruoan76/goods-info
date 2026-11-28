"""条码域 3 端点。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import auth as A
from ..core.audit import audit, audit_goods_history, gen_batch_id
from ..core.db import conn_app
from ..core.errors import BizError, CODE_DUP_BARCODE, CODE_STATUS_ILLEGAL, ok
from ..services import ironrules as ir

router = APIRouter(prefix="/barcodes", tags=["条码"])


class ValidateBody(BaseModel):
    barcode: str


class AliasBody(BaseModel):
    alias_barcode: str
    master_barcode: str
    alias_type: str = Field(description="BIG_PACK/OLD_CODE/DIFF_PACK")


class ReassignBody(BaseModel):
    old_barcode: str
    new_barcode: str
    reason: str


@router.post("/validate", summary="准入校验")
def validate(body: ValidateBody, _: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    bc = body.barcode
    checks = ir.barcode_admission_checks(bc)
    with conn_app() as c, c.cursor() as cur:
        cur.execute("SELECT 1 FROM mdm_goods WHERE barcode=%s", (bc,))
        checks["barcode_exist"] = cur.fetchone() is not None
        cur.execute("SELECT 1 FROM mdm_barcode_alias WHERE alias_barcode=%s", (bc,))
        checks["alias_reverse"] = cur.fetchone() is not None
        # 禁复用判定
        try:
            ir.assert_barcode_reusable(cur, bc)
            checks["in_ban_period"] = False
        except BizError:
            checks["in_ban_period"] = True
    allowed = (checks["format_ok"] and not checks["is_isbn"]
               and not checks["barcode_exist"] and not checks["alias_reverse"]
               and not checks["in_ban_period"])
    return ok({**checks, "allowed": allowed})


@router.post("/alias", summary="多包装别名归并")
def alias(body: AliasBody, user: dict = Depends(A.require_role(A.STEWARD))):
    batch = gen_batch_id(user["account"])
    with conn_app() as c, c.cursor() as cur:
        cur.execute("LOCK TABLE mdm_goods, mdm_barcode_alias IN ROW EXCLUSIVE MODE")
        cur.execute("SELECT 1 FROM mdm_goods WHERE barcode=%s FOR KEY SHARE", (body.master_barcode,))
        if not cur.fetchone():
            raise BizError(CODE_DUP_BARCODE, "主条码不存在或已换码")

        cur.execute(
            """INSERT INTO mdm_barcode_alias (alias_barcode, master_barcode, alias_type, created_at)
               VALUES (%s,%s,%s,now()::text)
               ON CONFLICT (alias_barcode, alias_type) DO UPDATE SET master_barcode=EXCLUDED.master_barcode""",
            (body.alias_barcode, body.master_barcode, body.alias_type),
        )
        audit(cur, entity_type="BARCODE_ALIAS", entity_key=body.alias_barcode,
              action="ALIAS_CREATE", operator=user["account"], after=body.model_dump(),
              batch_id=batch)
    return ok({"alias_barcode": body.alias_barcode, "master_barcode": body.master_barcode})


@router.post("/reassign", summary="换码登记（旧码 90 天禁复用）")
def reassign(body: ReassignBody, user: dict = Depends(A.require_role(A.STEWARD))):
    ir.assert_barcode_admissible(body.new_barcode)
    if body.old_barcode == body.new_barcode:
        raise BizError(CODE_DUP_BARCODE, "新旧条码不能相同")
    batch = gen_batch_id(user["account"])
    with conn_app() as c, c.cursor() as cur:
        # Rare administrative operation: table locks serialize migration with
        # all database writers, including those outside this API. No CASCADE
        # assumptions: the deployed schema has no FK to mdm_goods.
        cur.execute("SET LOCAL lock_timeout = '5s'")
        cur.execute("LOCK TABLE mdm_goods, mdm_goods_attrs, mdm_goods_history, "
                    "mdm_barcode_alias IN SHARE ROW EXCLUSIVE MODE")
        cur.execute("SELECT status FROM mdm_goods WHERE barcode=%s FOR UPDATE", (body.old_barcode,))
        source = cur.fetchone()
        if not source:
            raise BizError(CODE_DUP_BARCODE, "原条码不存在")
        if source[0] == "VOIDED":
            raise BizError(CODE_STATUS_ILLEGAL, "作废商品不可换码")
        ir.assert_barcode_reusable(cur, body.new_barcode)
        cur.execute("SELECT 1 FROM mdm_goods WHERE barcode=%s", (body.new_barcode,))
        if cur.fetchone():
            raise BizError(CODE_DUP_BARCODE)
        cur.execute(
            "SELECT 1 FROM mdm_barcode_alias WHERE alias_barcode=%s OR master_barcode=%s LIMIT 1",
            (body.new_barcode, body.new_barcode),
        )
        if cur.fetchone():
            raise BizError(CODE_DUP_BARCODE, "新条码已在别名或主条码范围内")
        cur.execute("SELECT 1 FROM mdm_goods_attrs WHERE barcode=%s "
                    "UNION ALL SELECT 1 FROM mdm_goods_history WHERE barcode=%s LIMIT 1",
                    (body.new_barcode, body.new_barcode))
        if cur.fetchone():
            raise BizError(CODE_DUP_BARCODE, "新条码存在历史或属性记录，需先核查")

        # Preserve identity-linked data before changing the primary key.  The
        # alias row created below is also the 90-day old-code ban.
        cur.execute("UPDATE mdm_goods_attrs SET barcode=%s WHERE barcode=%s", (body.new_barcode, body.old_barcode))
        cur.execute("UPDATE mdm_goods_history SET barcode=%s WHERE barcode=%s", (body.new_barcode, body.old_barcode))
        cur.execute("UPDATE mdm_barcode_alias SET master_barcode=%s WHERE master_barcode=%s", (body.new_barcode, body.old_barcode))
        banned = ir.register_voided_ban(cur, body.old_barcode, user["account"], batch)
        cur.execute(
            "UPDATE mdm_barcode_alias SET master_barcode=%s WHERE alias_barcode=%s AND alias_type='VOIDED_BAN'",
            (body.new_barcode, body.old_barcode),
        )
        cur.execute(
            """UPDATE mdm_goods SET barcode=%s, version=version+1, updated_at=now()::text
               WHERE barcode=%s""",
            (body.new_barcode, body.old_barcode),
        )
        audit_goods_history(cur, barcode=body.new_barcode, field_name="barcode",
                            old_value=body.old_barcode, new_value=body.new_barcode,
                            operator=user["account"], rule_code="REASSIGN", batch_id=batch)
        audit(cur, entity_type="BARCODE", entity_key=body.old_barcode, action="REASSIGN",
              operator=user["account"],
              before={"barcode": body.old_barcode},
              after={"barcode": body.new_barcode, "banned_until": str(banned),
                     "reason": body.reason}, batch_id=batch)
    return ok({"old_barcode": body.old_barcode, "new_barcode": body.new_barcode,
               "banned_until": str(banned)})
