"""商品编辑和导入的 PostgreSQL 回归。"""
from uuid import uuid4

import pytest

from app.core.db import conn_app
from test_contracts import client, hdr

pytestmark = pytest.mark.usefixtures("contract_users")


def free_barcodes(count):
    with conn_app() as conn, conn.cursor() as cur:
        while True:
            base = 2000000000000 + uuid4().int % 700000000000
            candidates = [str(base + index) for index in range(count)]
            cur.execute("SELECT 1 FROM mdm_goods WHERE barcode = ANY(%s) "
                        "UNION ALL SELECT 1 FROM mdm_barcode_alias WHERE alias_barcode = ANY(%s)",
                        (candidates, candidates))
            if cur.fetchone() is None:
                return candidates


def test_goods_patch_uses_client_version_and_only_editable_fields():
    barcode, = free_barcodes(1)
    operator = hdr("Operator")
    created = client.post("/api/v1/goods", headers=operator,
                          json={"barcode": barcode, "goods_name": "回归校验", "quality_grade": "C"})
    assert created.json()["code"] == 0, created.text
    url = f"/api/v1/goods/{barcode}"
    for field in ("status", "category_id", "version"):
        response = client.patch(url, headers=operator,
                                json={"field": field, "new_value": "ACTIVE", "version": 1})
        assert response.status_code == 422
    assert client.patch(url, headers=operator, json={"field": "goods_name", "new_value": "缺少版本"}).status_code == 422
    for name, expected in (("已保存", 0), ("过期页面", 3009)):
        response = client.patch(url, headers=operator,
                                json={"field": "goods_name", "new_value": name, "version": 1})
        assert response.json()["code"] == expected, response.text
    assert client.get(url, headers=operator).json()["data"]["goods_name"] == "已保存"


def test_csv_database_rejection_does_not_abort_following_batch(monkeypatch):
    # Production prices are unbounded numeric, so huge positive values do not
    # reliably trigger a DB rejection. Inject a real database DataError instead.
    from app.routers import goods
    original = goods._import_goods_row
    def insert_row(cur, row, batch, operator):
        if row.get("unit_id") == "invalid_unit":
            cur.execute("SELECT 'invalid_unit'::integer")
        original(cur, row, batch, operator)
    monkeypatch.setattr(goods, "_import_goods_row", insert_row)
    before, invalid, after = free_barcodes(3)
    csv_rows = ["barcode,goods_name,outprice,unit_id", f"{before},首条,1", f"{invalid},单位违反数据库约束,1,invalid_unit"]
    csv_rows += ["invalid,非法条码,1"] * 498
    csv_rows += [f"{after},下一批,2"]
    response = client.post("/api/v1/goods/import", headers=hdr("Operator"),
                           files={"file": ("goods.csv", "\n".join(csv_rows).encode(), "text/csv")})
    payload = response.json()
    assert payload["code"] == 0, response.text
    data = payload["data"]
    assert (data["total"], data["success"], data["failed"]) == (501, 2, 499), data
    assert len(data["fail_detail"]) == 50
    with conn_app() as conn, conn.cursor() as cur:
        cur.execute("SELECT barcode FROM mdm_goods WHERE barcode = ANY(%s) ORDER BY barcode",
                    ([before, invalid, after],))
        assert [row[0] for row in cur.fetchall()] == [before, after]
        cur.execute("SELECT status, success_rows, fail_rows FROM sys_import_job WHERE id = %s", (data["job_id"],))
        assert cur.fetchone() == ("PARTIAL", 2, 499)
