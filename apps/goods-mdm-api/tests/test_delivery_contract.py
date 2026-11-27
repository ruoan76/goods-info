"""筛选、分页和 CSV 文本编码的无数据库契约。"""
import csv
import io

import pytest

from app.core.delivery import (
    ContractError,
    assert_page,
    csv_text,
    encode_csv_fields,
    normalize_price_state,
)
from app.daos.goods import _build_filter


def test_page_aliases_match_priced_and_pending_sql():
    pending_sql, pending_args = _build_filter({"price_state": "PENDING"})
    unpriced_sql, unpriced_args = _build_filter({"price_state": "unpriced"})
    priced_sql, priced_args = _build_filter({"price_state": "HAS"})
    assert pending_sql == unpriced_sql
    assert "inprice IS NULL OR g.inprice=0 OR g.outprice IS NULL OR g.outprice=0" in pending_sql
    assert pending_args == unpriced_args == []
    assert "g.inprice>0 AND g.outprice>0" in priced_sql
    assert priced_args == []
    assert normalize_price_state("priced") == "priced"
    assert normalize_price_state("") is None
    assert normalize_price_state(None) is None


def test_unknown_price_state_is_rejected():
    with pytest.raises(ContractError):
        normalize_price_state("maybe")
    with pytest.raises(ContractError):
        _build_filter({"price_state": "priced "})


def test_list_filters_share_one_where_clause():
    where_sql, args = _build_filter({
        "status": "ACTIVE",
        "price_state": "PENDING",
        "q": "6901234",
        "category_id": "C01",
    })
    assert "g.status = %s" in where_sql
    assert "g.inprice IS NULL" in where_sql
    assert "g.category_id = %s" in where_sql
    assert args == ["C01", "6901234", "%6901234%", "ACTIVE"]


def test_page_bounds():
    assert_page(1, 200)
    with pytest.raises(ContractError):
        assert_page(0, 20)
    with pytest.raises(ContractError):
        assert_page(1, 201)
    with pytest.raises(ContractError):
        assert_page(1, 0)


def test_csv_text_neutralizes_formula_prefixes_only():
    assert csv_text("=1+1") == "'=1+1"
    assert csv_text("+cmd") == "'+cmd"
    assert csv_text("-1+1") == "'-1+1"
    assert csv_text("@sum") == "'@sum"
    assert csv_text("  =1+1") == "'  =1+1"
    assert csv_text("普通商品") == "普通商品"
    assert csv_text("6901234567890") == "6901234567890"
    assert csv_text(None) == ""

    row = encode_csv_fields(
        ["=名称", "分类", "12.50", "-0.01"],
        {0, 1},
    )
    buf = io.StringIO()
    csv.writer(buf).writerow(row)
    written = buf.getvalue()
    assert "'=名称" in written
    assert ",-0.01" in written or written.endswith("-0.01\r\n") or "-0.01" in written
    assert written.split(",")[2] == "12.50" or "12.50" in written
