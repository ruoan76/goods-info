"""属性、别名和治理回滚的无数据库契约。"""
import json
from pathlib import Path

import pytest

from app.core.errors import BizError
from app.services.aliases import assess_alias
from app.services.attrs import validate_attr_document, write_goods_attrs
from app.services.gov_rollback import plan_compensating_rollback


TEMPLATE = {
    "enabled": True,
    "template": {
        "required": ["color"],
        "fields": {
            "color": {"type": "string", "enum": ["红", "蓝"]},
            "volume": {"type": "number"},
        },
    },
}


class AttrCursor:
    def __init__(self, category_id="C01", template=None, stored=None):
        self.category_id = category_id
        self.template_row = None if template is None else (template["template"], True, "steward", "t")
        self.stored = stored
        self.mode = ""
        self.writes = []

    def execute(self, sql, args=None):
        self.mode = sql
        if "INSERT INTO mdm_goods_attrs" in sql:
            self.stored = json.loads(args[1])
            self.writes.append(self.stored)

    def fetchone(self):
        if "FOR UPDATE" in self.mode and "mdm_goods " in self.mode:
            if self.category_id is None:
                return None
            return (self.category_id,)
        if "sys_attr_template" in self.mode:
            return self.template_row
        if "attrs_json FROM" in self.mode:
            if self.stored is None:
                return None
            return (self.stored,)
        return None


def test_three_attribute_shapes_share_validation():
    with pytest.raises(BizError, match="缺少必填属性"):
        validate_attr_document({"volume": "1"}, TEMPLATE)
    with pytest.raises(BizError, match="缺少必填属性"):
        validate_attr_document({"color": ""}, TEMPLATE)
    with pytest.raises(BizError, match="不在允许值内"):
        validate_attr_document({"color": "绿"}, TEMPLATE)
    with pytest.raises(BizError, match="类型必须是 number"):
        validate_attr_document({"color": "红", "volume": "很大"}, TEMPLATE)
    validate_attr_document({"color": "红", "volume": "12.5"}, TEMPLATE)


def test_attribute_merge_keeps_both_updates():
    cur = AttrCursor(template=TEMPLATE, stored={"color": "红"})
    first = write_goods_attrs(cur, "6901234567890", {"volume": "1"}, merge=True)
    second = write_goods_attrs(cur, "6901234567890", {"color": "蓝"}, merge=True)
    assert first["new"]["color"] == "红"
    assert second["new"] == {"color": "蓝", "volume": "1"}
    assert "FOR UPDATE" in cur.mode or cur.writes


def test_missing_goods_does_not_write_attributes():
    cur = AttrCursor(category_id=None)
    assert write_goods_attrs(cur, "6901234567890", {"color": "红"}) is None
    assert cur.writes == []


def test_alias_rejects_main_code_reserved_type_and_retarget():
    with pytest.raises(BizError, match="已有商品主码不能登记为别名"):
        assess_alias("11111111", "22222222", "BIG_PACK",
                     master_exists=True, alias_is_main=True, links=[])
    with pytest.raises(BizError, match="仅允许"):
        assess_alias("11111111", "22222222", "VOIDED_BAN",
                     master_exists=True, alias_is_main=False, links=[])
    with pytest.raises(BizError, match="已指向其他主码"):
        assess_alias("11111111", "33333333", "OLD_CODE",
                     master_exists=True, alias_is_main=False,
                     links=[("BIG_PACK", "22222222")])
    assert assess_alias(
        "11111111", "22222222", "BIG_PACK",
        master_exists=True, alias_is_main=False, links=[("BIG_PACK", "22222222")],
    ) == "idempotent"


def test_rollback_keeps_history_and_skips_later_edits():
    plan = plan_compensating_rollback([
        {"barcode": "11111111", "version_before": 4, "version_now": 5,
         "restore": {"goods_name": "旧名称"}},
        {"barcode": "22222222", "version_before": 4, "version_now": 6,
         "restore": {"goods_name": "旧名称"}},
        {"barcode": "33333333", "version_before": 1, "version_now": None, "deleted": True,
         "restore": {}},
    ])
    assert plan["delete_history"] is False
    assert plan["apply"] == [{
        "barcode": "11111111",
        "restore": {"goods_name": "旧名称"},
        "expected_version": 5,
        "next_version": 6,
    }]
    assert [row["barcode"] for row in plan["conflicts"]] == ["22222222", "33333333"]


def test_guard_script_compiles():
    path = Path(__file__).resolve().parents[3] / "governance" / "templates" / "guard_batch.py"
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    tree = compile(source, str(path), "exec")
    assert tree is not None
    assert "import os\n#!/" not in source
    assert "pg_advisory_xact_lock" in source
    assert "version_before" in source
