"""公开别名准入。VOIDED_BAN 只由作废流程写入。"""
from __future__ import annotations

from ..core.errors import CODE_BANNED_BARCODE, CODE_DUP_BARCODE, BizError
from .ironrules import is_isbn, valid_barcode_format

PUBLIC_ALIAS_TYPES = frozenset({"BIG_PACK", "OLD_CODE", "DIFF_PACK"})


def assess_alias(
    alias_barcode: str,
    master_barcode: str,
    alias_type: str,
    *,
    master_exists: bool,
    alias_is_main: bool,
    links: list[tuple[str, str]],
) -> str:
    """返回 create 或 idempotent。links 是该别名已有的 (alias_type, master_barcode)。"""
    if alias_type not in PUBLIC_ALIAS_TYPES:
        raise BizError(CODE_DUP_BARCODE, "别名类型仅允许 BIG_PACK、OLD_CODE、DIFF_PACK")
    if not valid_barcode_format(alias_barcode) or not valid_barcode_format(master_barcode):
        raise BizError(3004, "条码格式非法")
    if is_isbn(alias_barcode) or is_isbn(master_barcode):
        raise BizError(3004, "书号非商品条码")
    if alias_barcode == master_barcode:
        raise BizError(CODE_DUP_BARCODE, "别名不能与主码相同")
    if not master_exists:
        raise BizError(CODE_DUP_BARCODE, "主码不存在")
    if alias_is_main:
        raise BizError(CODE_DUP_BARCODE, "已有商品主码不能登记为别名")
    for existing_type, existing_master in links:
        if existing_type == "VOIDED_BAN":
            raise BizError(CODE_BANNED_BARCODE, "该条码已有禁复用登记，不能改作包装别名")
        if existing_master != master_barcode:
            raise BizError(CODE_DUP_BARCODE, "该别名已指向其他主码")
        if existing_type == alias_type:
            return "idempotent"
    return "create"


def register_public_alias(cur, alias_barcode: str, master_barcode: str, alias_type: str) -> str:
    """同一别名串行准入。已有相同登记视为幂等，不改指向。"""
    cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"alias:{alias_barcode}",))
    cur.execute(
        "SELECT barcode FROM mdm_goods WHERE barcode = ANY(%s) ORDER BY barcode FOR UPDATE",
        (sorted({alias_barcode, master_barcode}),),
    )
    found = {row[0] for row in cur.fetchall()}
    cur.execute(
        "SELECT alias_type, master_barcode FROM mdm_barcode_alias WHERE alias_barcode=%s FOR UPDATE",
        (alias_barcode,),
    )
    links = [(row[0], row[1]) for row in cur.fetchall()]
    decision = assess_alias(
        alias_barcode,
        master_barcode,
        alias_type,
        master_exists=master_barcode in found,
        alias_is_main=alias_barcode in found,
        links=links,
    )
    if decision == "idempotent":
        return decision
    cur.execute(
        """INSERT INTO mdm_barcode_alias (alias_barcode, master_barcode, alias_type, created_at)
           VALUES (%s,%s,%s,now()::text)""",
        (alias_barcode, master_barcode, alias_type),
    )
    return decision
