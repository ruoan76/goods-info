"""商品属性的统一写入。建档、单条更新和 CSV 回填都走这里。"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ..core.errors import CODE_ATTR_REQUIRED, BizError
from ..daos import catalog as dc

MAX_ATTR_KEYS = 80
MAX_TEXT_LENGTH = 2000


def validate_attr_document(attrs: dict, template: dict | None) -> None:
    """按模板校验整份属性。无模板时只限制规模和嵌套。"""
    if not isinstance(attrs, dict):
        raise BizError(CODE_ATTR_REQUIRED, "属性必须是对象")
    if len(attrs) > MAX_ATTR_KEYS:
        raise BizError(CODE_ATTR_REQUIRED, "属性字段过多")
    for key, value in attrs.items():
        if not isinstance(key, str) or not key.strip() or len(key) > 64:
            raise BizError(CODE_ATTR_REQUIRED, "属性名非法")
        _assert_shape(key, value)
    spec = _template_spec(template)
    if spec is None:
        return
    missing = [
        key for key in spec.get("required") or []
        if key not in attrs or attrs[key] is None or attrs[key] == ""
    ]
    if missing:
        raise BizError(CODE_ATTR_REQUIRED, f"缺少必填属性: {missing}")
    fields = spec.get("fields") or {}
    for key, rule in fields.items():
        if key not in attrs or attrs[key] is None or attrs[key] == "":
            continue
        if isinstance(rule, dict):
            _check_rule(key, attrs[key], rule)


def write_goods_attrs(cur, barcode: str, attrs: dict, *, merge: bool = False) -> dict | None:
    """锁定商品行后校验并覆盖写入。商品不存在时返回 None。

    merge 为真时把 attrs 合并进已有 JSON，供 CSV 单字段回填使用。
    """
    cur.execute("SELECT category_id FROM mdm_goods WHERE barcode=%s FOR UPDATE", (barcode,))
    row = cur.fetchone()
    if row is None:
        return None
    template = dc.get_template(cur, row[0] or "")
    old = dc.get_goods_attrs(cur, barcode)
    new_attrs = dict(old)
    if merge:
        new_attrs.update(attrs)
    else:
        new_attrs = dict(attrs)
    validate_attr_document(new_attrs, template)
    dc.put_goods_attrs(cur, barcode, new_attrs)
    return {"old": old, "new": new_attrs}


def _template_spec(template: dict | None) -> dict | None:
    if not template or template.get("enabled") is False:
        return None
    inner = template.get("template", template)
    if not isinstance(inner, dict):
        return None
    if "required" not in inner and "fields" not in inner:
        return None
    return inner


def _assert_shape(key: str, value) -> None:
    if isinstance(value, dict):
        raise BizError(CODE_ATTR_REQUIRED, f"属性 {key} 不能是对象")
    if isinstance(value, list):
        if any(isinstance(item, (dict, list)) for item in value):
            raise BizError(CODE_ATTR_REQUIRED, f"属性 {key} 嵌套过深")
        return
    if isinstance(value, str) and len(value) > MAX_TEXT_LENGTH:
        raise BizError(CODE_ATTR_REQUIRED, f"属性 {key} 过长")


def _check_rule(key: str, value, rule: dict) -> None:
    expected = rule.get("type")
    if expected and not _matches_type(value, expected):
        raise BizError(CODE_ATTR_REQUIRED, f"属性 {key} 类型必须是 {expected}")
    allowed = rule.get("enum")
    if isinstance(allowed, list) and value not in allowed:
        raise BizError(CODE_ATTR_REQUIRED, f"属性 {key} 不在允许值内")


def _matches_type(value, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float, Decimal)):
            return True
        if isinstance(value, str):
            try:
                Decimal(value)
            except InvalidOperation:
                return False
            return value.strip() != ""
        return False
    if expected == "integer":
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return True
        return False
    if expected == "boolean":
        return isinstance(value, bool) or value in ("true", "false")
    return True
