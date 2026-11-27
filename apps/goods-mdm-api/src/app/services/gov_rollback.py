"""治理回滚判定。只生成补偿动作，不删除历史，也不把版本倒退。"""
from __future__ import annotations


def plan_compensating_rollback(records: list[dict]) -> dict:
    """records 每项包含 barcode、version_before、version_now、restore。

    只有当前版本仍等于快照后的下一个版本时才恢复。其后又被修改的行进入冲突清单。
    """
    apply: list[dict] = []
    conflicts: list[dict] = []
    for row in records:
        barcode = row["barcode"]
        version_before = row["version_before"]
        version_now = row.get("version_now")
        if row.get("deleted") or version_now is None:
            conflicts.append({"barcode": barcode, "reason": "商品已不存在"})
            continue
        if version_now != version_before + 1:
            conflicts.append({"barcode": barcode, "reason": "版本已前进，不能覆盖后续修改"})
            continue
        apply.append({
            "barcode": barcode,
            "restore": dict(row.get("restore") or {}),
            "expected_version": version_now,
            "next_version": version_now + 1,
        })
    return {"apply": apply, "conflicts": conflicts, "delete_history": False}
