"""40 端点契约测试：端点覆盖 / 方法分布 / 三角色权限 / 响应包结构 / 字段对齐。"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from app.core.auth import issue_token
from app.core.config import PG_DSN_APP
from app.main import app

client = TestClient(app)


def hdr(role: str) -> dict:
    account = {"Viewer": "ct_viewer", "Operator": "ct_operator", "Steward": "ct_steward"}[role]
    return {"Authorization": f"Bearer {issue_token(account, role, 0)}"}


# ---------- 1. 端点覆盖与方法分布（从 OpenAPI 反推，不手填） ----------
def test_openapi_40_endpoints_method_distribution():
    s = app.openapi()
    paths = s["paths"]
    methods = {}
    for p, ops in paths.items():
        for m in ops:
            if m in ("get", "post", "put", "patch", "delete"):
                methods[m] = methods.get(m, 0) + 1
    # 契约 40：GET18/POST15/PUT6/PATCH1（+ /health 不在契约内）
    total = sum(methods.values())
    assert total == 41, f"端点总数应 41（40 API + health），实际 {total}"
    assert methods["get"] == 19, methods      # 18 API + health
    assert methods["post"] == 15, methods
    assert methods["put"] + methods["patch"] == 7, methods


def test_all_contract_paths_present():
    paths = set(app.openapi()["paths"].keys())
    expected = [
        "/api/v1/auth/token", "/api/v1/auth/logout",
        "/api/v1/goods", "/api/v1/goods/check", "/api/v1/goods/export",
        "/api/v1/goods/import", "/api/v1/goods/{barcode}",
        "/api/v1/goods/{barcode}/category", "/api/v1/goods/{barcode}/status",
        "/api/v1/goods/{barcode}/attrs",
        "/api/v1/categories/tree", "/api/v1/categories/{cid}",
        "/api/v1/categories/{cid}/impact", "/api/v1/categories/{cid}/template",
        "/api/v1/categories/{cid}/external-map",
        "/api/v1/attributes", "/api/v1/attributes/{aid}", "/api/v1/attributes/import",
        "/api/v1/barcodes/validate", "/api/v1/barcodes/alias", "/api/v1/barcodes/reassign",
        "/api/v1/admin/dashboard", "/api/v1/admin/change-log", "/api/v1/admin/units",
        "/api/v1/admin/units/{code}", "/api/v1/admin/sources", "/api/v1/admin/quarantine",
        "/api/v1/admin/quarantine/export", "/api/v1/admin/users",
        "/api/v1/admin/users/{account}", "/api/v1/admin/users/{account}/reset-password",
        "/api/v1/admin/users/{account}/activity", "/api/v1/admin/import-jobs/{job_id}",
    ]
    missing = [p for p in expected if p not in paths]
    assert not missing, f"缺失端点: {missing}"


# ---------- 2. 响应包结构 {code,message,data} ----------
def test_health_shape():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_unauth_rejected():
    r = client.get("/api/v1/goods")
    assert r.status_code == 401
    assert r.json()["code"] == 2001


# ---------- 3. 角色权限（Viewer 只读 / Operator 可写 / Steward 全权） ----------
@pytest.mark.usefixtures("contract_users")
def test_viewer_can_read():
    r = client.get("/api/v1/goods?page_size=1", headers=hdr("Viewer"))
    assert r.status_code == 200
    assert r.json()["code"] == 0
    d = r.json()["data"]
    assert "items" in d and "total" in d and "total_approx" in d and "has_more" in d


@pytest.mark.usefixtures("contract_users")
def test_viewer_cannot_create():
    body = {"barcode": "12345678", "goods_name": "测试", "quality_grade": "C"}
    r = client.post("/api/v1/goods", json=body, headers=hdr("Viewer"))
    assert r.status_code == 403 and r.json()["code"] == 2002


@pytest.mark.usefixtures("contract_users")
def test_operator_cannot_status():
    r = client.post("/api/v1/goods/6901035623162/status",
                    json={"to_status": "VOIDED", "reason": "test"},
                    headers=hdr("Operator"))
    assert r.status_code == 403 and r.json()["code"] == 2002


@pytest.mark.usefixtures("contract_users")
def test_steward_can_dashboard():
    r = client.get("/api/v1/admin/dashboard", headers=hdr("Steward"))
    assert r.status_code == 200 and r.json()["code"] == 0
    d = r.json()["data"]
    # 已改精确计数：goods_total 必须与 count(*) 一致（治理期估算漂移不可接受）
    import psycopg2
    conn = psycopg2.connect(PG_DSN_APP)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM mdm_goods")
    assert d["goods_total"] == cur.fetchone()[0]
    cur.close(); conn.close()
    assert d["goods_total_approx"] is False
    assert d["quarantine_conflict"] == 138083


@pytest.mark.usefixtures("contract_users")
def test_viewer_cannot_users():
    r = client.get("/api/v1/admin/users", headers=hdr("Viewer"))
    assert r.status_code == 403 and r.json()["code"] == 2002


# ---------- 4. 关键字段对齐 ----------
@pytest.mark.usefixtures("contract_users")
def test_goods_list_fields():
    r = client.get("/api/v1/goods?page_size=1", headers=hdr("Viewer"))
    item = r.json()["data"]["items"][0]
    for k in ("barcode", "goods_name", "category_id", "category_code_path",
              "category_path", "unit_id", "inprice", "outprice",
              "quality_grade", "status", "version", "updated_at"):
        assert k in item, f"商品列表缺字段 {k}"


@pytest.mark.usefixtures("contract_users")
def test_tree_shape():
    r = client.get("/api/v1/categories/tree", headers=hdr("Viewer"))
    d = r.json()["data"]
    assert "tree" in d and d["total_nodes"] >= 171  # R16 新增 C0604 图书报刊后为 172，治理可再加
    assert d["active_nodes"] > 0


@pytest.mark.usefixtures("contract_users")
def test_dashboard_pending_exact():
    """待办数必须与实库逐项对账（接口 v1.2 文档的 53574 是过期快照，以实库为准）。"""
    import psycopg2
    conn = psycopg2.connect(PG_DSN_APP)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM mdm_goods WHERE inprice IS NULL OR inprice=0 OR outprice IS NULL OR outprice=0")
    expect_pending = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mdm_goods WHERE category_id='C00'")
    expect_unclassified = cur.fetchone()[0]
    cur.close(); conn.close()

    r = client.get("/api/v1/admin/dashboard", headers=hdr("Viewer"))
    d = r.json()["data"]
    assert d["price_pending"] == expect_pending
    # 不硬编码快照值：C00 受并行治理会话（r13/r15）持续归类影响是活数据，只做动态对账
    assert d["unclassified"] == expect_unclassified
    assert d["category_l1"] == 13


@pytest.mark.usefixtures("contract_users")
def test_quarantine_readonly_via_ro():
    r = client.get("/api/v1/admin/quarantine?page_size=2", headers=hdr("Viewer"))
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 138083


@pytest.mark.usefixtures("contract_users")
def test_change_log_readonly():
    r = client.get("/api/v1/admin/change-log?limit=5", headers=hdr("Viewer"))
    assert r.status_code == 200
    assert "items" in r.json()["data"]
