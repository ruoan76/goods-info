"""统一留痕 audit()。

铁律④：任何改动都记录"谁、何时、改了什么"。
- batch_id 规则 MAN-YYYYMMDDHHMMSS-<operator>：mdm_goods_history.batch_id NOT NULL 无默认值，
  不生成则所有人工变更写历史失败（接口 v1.1 P1 已确认）。
- sys_change_log 与业务表写在同一事务（由调用方传入 cursor）。
- goods_app 对 sys_change_log 仅 INSERT 权限（m1 已授权），审计不可篡改。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .config import API_PREFIX  # noqa: F401  (保留导入以便配置统一)


def gen_batch_id(operator: str) -> str:
    """MAN-YYYYMMDDHHMMSS-<operator>"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"MAN-{ts}-{operator}"


def audit(
    cur,
    *,
    entity_type: str,
    entity_key: str,
    action: str,
    operator: str,
    before: Any = None,
    after: Any = None,
    batch_id: str | None = None,
) -> tuple[str, int]:
    """写一条审计记录并回传 (batch_id, log_id)。

    调用方必须在同一 cursor/事务里先/后完成业务写入，任一失败整体回滚。
    before/after 传 dict 或 None，内部以 JSONB 写入。
    """
    import json

    bid = batch_id or gen_batch_id(operator)
    # default=str：兼容 Decimal/datetime 等 pydantic 字段类型（金额 NUMERIC 常见）
    before_json = json.dumps(before, ensure_ascii=False, default=str) if before is not None else None
    after_json = json.dumps(after, ensure_ascii=False, default=str) if after is not None else None
    cur.execute(
        "INSERT INTO sys_change_log "
        "(batch_id, entity_type, entity_key, action, operator, before_data, after_data) "
        "VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb) RETURNING log_id",
        (bid, entity_type, entity_key, action, operator, before_json, after_json),
    )
    log_id = cur.fetchone()[0]
    return bid, log_id


def audit_goods_history(
    cur,
    *,
    barcode: str,
    field_name: str,
    old_value: str | None,
    new_value: str | None,
    operator: str,
    rule_code: str | None = None,
    batch_id: str | None = None,
) -> str:
    """写 mdm_goods_history（batch_id 必填，MAN 规则）。"""
    bid = batch_id or gen_batch_id(operator)
    # mdm_goods_history.batch_id 有 FK → sys_gov_batch(batch_id)，
    # 人工变更的 MAN 批次必须先登记（batch_type=MANUAL），否则 FK 违反。
    from datetime import datetime
    cur.execute(
        """INSERT INTO sys_gov_batch
           (batch_id, batch_type, rule_version, started_at, status, remark)
           VALUES (%s,'MANUAL','MANUAL-1.0',%s,'SUCCESS',%s)
           ON CONFLICT (batch_id) DO NOTHING""",
        (bid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"人工变更 by {operator}"),
    )
    cur.execute(
        "INSERT INTO mdm_goods_history "
        "(barcode, field_name, old_value, new_value, rule_code, batch_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (barcode, field_name, old_value, new_value, rule_code, bid),
    )
    return bid
