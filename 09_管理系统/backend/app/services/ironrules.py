"""四条铁律守卫（第二道防线，pydantic 为第一道、DB CHECK 为第三道）。

铁律① 新增必查重：verdict=BLOCK 直接拒；WARN 需人工确认；40.6% 同名多码基数不自动合并
铁律② 条码建档后不可改：PATCH 白名单不含 barcode；唯一变更通道 Steward /barcodes/reassign
铁律③ VOIDED 联动写别名表 90 天禁复用期，不可逆
铁律④ 所有改动留痕（由 core/audit.py audit() 统一实现，本模块提供 VOIDED 联动入口）

设计原则：全部为纯函数/参数化 SQL，便于单元测试；不依赖 FastAPI Request。
"""
from __future__ import annotations

from datetime import date, timedelta

from ..core.errors import (
    CODE_ATTR_REQUIRED,
    CODE_BANNED_BARCODE,
    CODE_DUP_BARCODE,
    CODE_STATUS_ILLEGAL,
    CODE_VERSION_CONFLICT,
    BizError,
)


# ---------------- 通用：条码格式（8/13 位 + 书号识别） ----------------
def is_isbn(barcode: str) -> bool:
    """978/979 开头视为书号，非商品条码（业务码 3004 由端点层按此判定）。"""
    return barcode.startswith(("978", "979"))


def valid_barcode_format(barcode: str) -> bool:
    """8 或 13 位纯数字。"""
    return barcode.isdigit() and len(barcode) in (8, 13)


# ---------------- 铁律①：查重三态 ----------------
def check_duplicate(cur, barcode: str, goods_name: str) -> dict:
    """三路查重：条码命中 / 同名命中 / 别名反向命中。

    返回 verdict ∈ {PASS, WARN, BLOCK}：
      BLOCK = 条码命中 或 别名反向命中（禁止建档）
      WARN  = 仅同名命中（提示人工核对）
      PASS  = 无命中
    """
    # 路 1：条码命中主档
    cur.execute("SELECT 1 FROM mdm_goods WHERE barcode=%s LIMIT 1", (barcode,))
    barcode_hit = cur.fetchone() is not None

    # 路 2：同名命中（只判存在，不自动合并——40.6% 同名多码基数）
    cur.execute(
        "SELECT 1 FROM mdm_goods WHERE goods_name=%s AND barcode<>%s LIMIT 1",
        (goods_name, barcode),
    )
    same_name_hit = cur.fetchone() is not None

    # 路 3：别名反向命中（该条码曾作为别名登记）
    cur.execute(
        "SELECT 1 FROM mdm_barcode_alias WHERE alias_barcode=%s LIMIT 1", (barcode,)
    )
    alias_reverse_hit = cur.fetchone() is not None

    if barcode_hit or alias_reverse_hit:
        verdict = "BLOCK"
    elif same_name_hit:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return {
        "barcode_exist": {"hit": barcode_hit},
        "same_name": {"hit": same_name_hit},
        "alias_reverse": {"hit": alias_reverse_hit},
        "verdict": verdict,
    }


def assert_can_create(cur, barcode: str, goods_name: str) -> dict:
    """写端点硬守卫：BLOCK 直接抛 3001，WARN 放行（由端点提示人工确认）。"""
    result = check_duplicate(cur, barcode, goods_name)
    if result["verdict"] == "BLOCK":
        raise BizError(CODE_DUP_BARCODE)
    return result


# ---------------- 铁律②：条码不可改 ----------------
PATCHABLE_FIELDS = frozenset(
    {"goods_name", "category_id", "unit_id", "inprice", "outprice",
     "quality_grade", "status", "version"}
)


def assert_patch_whitelist(patch: dict) -> None:
    """PATCH 字段白名单：barcode 永不在列；越界字段抛 422（由端点转）。"""
    illegal = set(patch.keys()) - PATCHABLE_FIELDS
    if "barcode" in patch or illegal:
        raise ValueError(f"字段不可更新: {sorted(illegal | ({'barcode'} if 'barcode' in patch else set()))}")


# ---------------- 铁律③：VOIDED 禁复用（90 天） ----------------
BAN_DAYS = 90


def can_transition(cur_old_status: str, new_status: str) -> bool:
    """状态合法性表：ACTIVE↔INACTIVE 可恢复；→VOIDED 不可逆。"""
    legal = {
        ("ACTIVE", "INACTIVE"),
        ("INACTIVE", "ACTIVE"),
        ("ACTIVE", "VOIDED"),
        ("INACTIVE", "VOIDED"),
    }
    return (cur_old_status, new_status) in legal


def assert_status_transition(cur, barcode: str, new_status: str) -> str:
    """校验并返回旧状态；非法流转抛 3007。"""
    cur.execute("SELECT status FROM mdm_goods WHERE barcode=%s", (barcode,))
    row = cur.fetchone()
    if row is None:
        raise BizError(CODE_STATUS_ILLEGAL, "商品不存在")
    old = row[0]
    if old == "VOIDED" or not can_transition(old, new_status):
        raise BizError(CODE_STATUS_ILLEGAL)
    return old


def register_voided_ban(cur, barcode: str, operator: str, batch_id: str) -> date:
    """转 VOIDED 时写别名表登记 90 天禁复用；返回禁用到期日。

    使用 mdm_barcode_alias(alias_barcode, master_barcode, alias_type, banned_until)。
    master_barcode 记自身，alias_type='VOIDED_BAN'。
    """
    banned_until = date.today() + timedelta(days=BAN_DAYS)
    cur.execute(
        "INSERT INTO mdm_barcode_alias "
        "(alias_barcode, master_barcode, alias_type, banned_until) "
        "VALUES (%s,%s,'VOIDED_BAN',%s) "
        "ON CONFLICT (alias_barcode, alias_type) DO UPDATE SET banned_until=EXCLUDED.banned_until",
        (barcode, barcode, banned_until),
    )
    return banned_until


def assert_barcode_reusable(cur, barcode: str) -> None:
    """建档准入：命中未过期禁复用登记抛 3003。"""
    cur.execute(
        "SELECT banned_until FROM mdm_barcode_alias "
        "WHERE alias_barcode=%s AND alias_type='VOIDED_BAN'",
        (barcode,),
    )
    row = cur.fetchone()
    if row and row[0] and row[0] >= date.today():
        raise BizError(CODE_BANNED_BARCODE)


# ---------------- 乐观锁 CAS ----------------
def assert_version(cur, barcode: str, expected_version: int) -> int:
    """乐观锁：期望版本与库中不一致抛 3009。返回当前版本。"""
    cur.execute("SELECT version FROM mdm_goods WHERE barcode=%s", (barcode,))
    row = cur.fetchone()
    if row is None:
        raise BizError(CODE_VERSION_CONFLICT, "商品不存在")
    if row[0] != expected_version:
        raise BizError(CODE_VERSION_CONFLICT)
    return row[0]
