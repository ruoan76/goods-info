"""合成库上的筛选和别名准入。"""
import pytest

from app.core.errors import BizError
from app.daos.goods import export_rows, list_goods
from app.services.aliases import register_public_alias

pytestmark = pytest.mark.usefixtures("test_db")


def test_pending_filter_excludes_priced_goods(cur):
    data = list_goods(cur, {"price_state": "PENDING", "page": 1, "page_size": 20})
    barcodes = {item["barcode"] for item in data["items"]}
    assert "6900000000002" in barcodes
    assert "6900000000003" in barcodes
    assert "6900000000001" not in barcodes


def test_export_includes_parent_category(cur):
    rows = {row[0]: row for row in export_rows(cur, {"q": "6900000000001"})}
    child = rows["6900000000001"]
    assert child[1] == "已定价商品"
    assert child[2] == "食品"
    assert child[3] == "饮料"
    top = {row[0]: row for row in export_rows(cur, {"q": "6900000000003"})}["6900000000003"]
    assert top[2] is None
    assert top[3] == "未分类"


def test_existing_main_barcode_cannot_become_alias(cur):
    with pytest.raises(BizError, match="已有商品主码不能登记为别名"):
        register_public_alias(cur, "6900000000001", "6900000000002", "BIG_PACK")
