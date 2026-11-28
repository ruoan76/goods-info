"""合成库上的筛选和别名准入。"""
import pytest

from app.core.errors import BizError
from app.daos.goods import list_goods
from app.services.aliases import register_public_alias

pytestmark = pytest.mark.usefixtures("test_db")


def test_pending_filter_excludes_priced_goods(cur):
    data = list_goods(cur, {"price_state": "PENDING", "page": 1, "page_size": 20})
    barcodes = {item["barcode"] for item in data["items"]}
    assert "6900000000002" in barcodes
    assert "6900000000003" in barcodes
    assert "6900000000001" not in barcodes


def test_existing_main_barcode_cannot_become_alias(cur):
    with pytest.raises(BizError, match="已有商品主码不能登记为别名"):
        register_public_alias(cur, "6900000000001", "6900000000002", "BIG_PACK")
