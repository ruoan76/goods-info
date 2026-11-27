"""条码域 3 端点。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from psycopg2 import IntegrityError
from pydantic import BaseModel, Field
from typing import Literal

from ..core import auth as A
from ..core.audit import audit, gen_batch_id
from ..core.db import conn_app
from ..core.errors import CODE_DUP_BARCODE, BizError, ok
from ..services import ironrules as ir
from ..services.aliases import register_public_alias

router = APIRouter(prefix="/barcodes", tags=["条码"])


class ValidateBody(BaseModel):
    barcode: str


class AliasBody(BaseModel):
    alias_barcode: str = Field(min_length=8, max_length=13)
    master_barcode: str = Field(min_length=8, max_length=13)
    alias_type: Literal["BIG_PACK", "OLD_CODE", "DIFF_PACK"]


class ReassignBody(BaseModel):
    old_barcode: str
    new_barcode: str
    reason: str


@router.post("/validate", summary="准入校验")
def validate(body: ValidateBody, _: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    bc = body.barcode
    checks = {
        "format_ok": ir.valid_barcode_format(bc),
        "is_isbn": ir.is_isbn(bc),
    }
    with conn_app() as c, c.cursor() as cur:
        cur.execute("SELECT 1 FROM mdm_goods WHERE barcode=%s", (bc,))
        checks["barcode_exist"] = cur.fetchone() is not None
        cur.execute("SELECT 1 FROM mdm_barcode_alias WHERE alias_barcode=%s", (bc,))
        checks["alias_reverse"] = cur.fetchone() is not None
        # 禁复用判定
        try:
            ir.assert_barcode_reusable(cur, bc)
            checks["in_ban_period"] = False
        except Exception:
            checks["in_ban_period"] = True
    allowed = (checks["format_ok"] and not checks["is_isbn"]
               and not checks["barcode_exist"] and not checks["alias_reverse"]
               and not checks["in_ban_period"])
    return ok({**checks, "allowed": allowed})


@router.post("/alias", summary="多包装别名归并")
def alias(body: AliasBody, user: dict = Depends(A.require_role(A.STEWARD))):
    batch = gen_batch_id(user["account"])
    try:
        with conn_app() as c, c.cursor() as cur:
            decision = register_public_alias(
                cur, body.alias_barcode, body.master_barcode, body.alias_type,
            )
            if decision == "create":
                audit(cur, entity_type="BARCODE_ALIAS", entity_key=body.alias_barcode,
                      action="ALIAS_CREATE", operator=user["account"], after=body.model_dump(),
                      batch_id=batch)
    except IntegrityError as exc:
        raise BizError(CODE_DUP_BARCODE, "别名与已有登记冲突") from exc
    return ok({"alias_barcode": body.alias_barcode, "master_barcode": body.master_barcode,
               "idempotent": decision == "idempotent"})


@router.post("/reassign", summary="换码登记（旧码 90 天禁复用）")
def reassign(body: ReassignBody, user: dict = Depends(A.require_role(A.STEWARD))):
    if not ir.valid_barcode_format(body.new_barcode):
        return ok(None, message="新条码格式非法")
    batch = gen_batch_id(user["account"])
    with conn_app() as c, c.cursor() as cur:
        # 旧码登记为别名并写禁用到期
        banned = ir.register_voided_ban(cur, body.old_barcode, user["account"], batch)
        cur.execute(
            """UPDATE mdm_goods SET barcode=%s, version=version+1, updated_at=now()::text
               WHERE barcode=%s""",
            (body.new_barcode, body.old_barcode),
        )
        audit(cur, entity_type="BARCODE", entity_key=body.old_barcode, action="REASSIGN",
              operator=user["account"],
              before={"barcode": body.old_barcode},
              after={"barcode": body.new_barcode, "banned_until": str(banned),
                     "reason": body.reason}, batch_id=batch)
    return ok({"old_barcode": body.old_barcode, "new_barcode": body.new_barcode,
               "banned_until": str(banned)})
