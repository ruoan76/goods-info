"""列表筛选、分页边界和 CSV 文本编码。"""
from __future__ import annotations

_PRICED = frozenset({"priced", "HAS"})
_UNPRICED = frozenset({"unpriced", "PENDING"})
_FORMULA_LEAD = frozenset("=+-@")
_LEAD_SPACE = frozenset(" \t\r\n")


class ContractError(ValueError):
    """请求契约不成立，路由层转换为 HTTP 422。"""


def normalize_price_state(value: str | None) -> str | None:
    """把页面用的 HAS/PENDING 收成 priced/unpriced。空值表示不筛选。"""
    if value is None or value == "":
        return None
    if value in _PRICED:
        return "priced"
    if value in _UNPRICED:
        return "unpriced"
    raise ContractError("price_state 只能是 priced、unpriced、HAS 或 PENDING")


def assert_page(page: int, page_size: int, *, max_size: int = 200) -> None:
    if page < 1 or page_size < 1 or page_size > max_size:
        raise ContractError("page 必须大于等于 1，page_size 必须在 1 到 200 之间")


def csv_text(value: object) -> str:
    """文本单元格若以公式字符开头，加前导单引号，避免表格软件执行。"""
    if value is None:
        return ""
    text = str(value)
    index = 0
    while index < len(text) and text[index] in _LEAD_SPACE:
        index += 1
    if index < len(text) and text[index] in _FORMULA_LEAD:
        return "'" + text
    return text


def encode_csv_fields(values, text_indexes: set[int]) -> list[str]:
    encoded: list[str] = []
    for index, value in enumerate(values):
        if index in text_indexes:
            encoded.append(csv_text(value))
        elif value is None:
            encoded.append("")
        else:
            encoded.append(str(value))
    return encoded
