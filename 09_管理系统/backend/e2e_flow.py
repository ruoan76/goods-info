"""E2E 业务流程：建档→查重→PATCH→属性→状态流转→禁复用 全链路。"""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1"
TOKEN = json.load(open("/tmp/e2e_login.json"))["data"]["access_token"]
HDR = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
BC = "8800100100100"


def call(method, path, body=None, headers=None):
    h = dict(HDR)
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def show(label, status, resp):
    print(f"[{label}] HTTP {status} code={resp.get('code')} {json.dumps(resp.get('data'), ensure_ascii=False)[:160]}")
    return resp


# 1. 查重（应 PASS）
s, r = call("POST", "/goods/check", {"barcode": BC, "goods_name": "E2E测试商品-唯品"})
show("1-查重PASS", s, r); assert r["data"]["verdict"] == "PASS"

# 2. 建档
s, r = call("POST", "/goods", {
    "barcode": BC, "goods_name": "E2E测试商品-唯品", "category_id": "C0203",
    "unit_id": "000007", "inprice": 100, "outprice": 150, "quality_grade": "B",
})
show("2-建档", s, r); assert r["code"] == 0 and r["data"]["version"] == 1

# 3. 再查重（应 BLOCK）
s, r = call("POST", "/goods/check", {"barcode": BC, "goods_name": "E2E测试商品-唯品"})
show("3-查重BLOCK", s, r); assert r["data"]["verdict"] == "BLOCK"

# 4. 重复建档（应 3001）
s, r = call("POST", "/goods", {"barcode": BC, "goods_name": "重复建档", "quality_grade": "C"})
show("4-重复建档拒", s, r); assert r["code"] == 3001

# 5. PATCH 改价
s, r = call("PATCH", f"/goods/{BC}", {"field": "outprice", "new_value": "220.00", "reason": "价格调整"})
show("5-PATCH改价", s, r); assert r["code"] == 0 and r["data"]["new_value"] == "220.000000"

# 6. PATCH 改条码（schema 应 422）
s, r = call("PATCH", f"/goods/{BC}", {"field": "barcode", "new_value": "12345678"})
show("6-改条码拒(422)", s, r); assert s == 422

# 7. 属性写入（无模板，直接写）
s, r = call("PUT", f"/goods/{BC}/attrs", {"attrs": {"净含量": "500ml", "口味": "经典"}})
show("7-属性写入", s, r); assert r["code"] == 0

# 8. 属性读取
s, r = call("GET", f"/goods/{BC}/attrs")
show("8-属性读取", s, r); assert r["data"]["净含量"] == "500ml"

# 9. 详情含历史时间轴
s, r = call("GET", f"/goods/{BC}")
show("9-详情历史", s, r)
assert len(r["data"]["history"]) >= 2  # CREATE + FIELD_EDIT

# 10. 状态流转 ACTIVE→INACTIVE
s, r = call("POST", f"/goods/{BC}/status", {"to_status": "INACTIVE", "reason": "测试停用"})
show("10-停用", s, r); assert r["data"]["to"] == "INACTIVE"

# 11. INACTIVE→VOIDED（触发 90 天禁复用）
s, r = call("POST", f"/goods/{BC}/status", {"to_status": "VOIDED", "reason": "测试作废"})
show("11-作废", s, r); assert r["data"]["to"] == "VOIDED"

# 12. VOIDED→ACTIVE（应 3007）
s, r = call("POST", f"/goods/{BC}/status", {"to_status": "ACTIVE", "reason": "恢复"})
show("12-作废后恢复拒", s, r); assert r["code"] == 3007

# 13. 禁复用校验（应 in_ban_period=true, allowed=false）
s, r = call("POST", "/barcodes/validate", {"barcode": BC})
show("13-禁复用校验", s, r); assert r["data"]["in_ban_period"] is True and r["data"]["allowed"] is False

# 14. 变更留痕可查
s, r = call("GET", "/admin/change-log?limit=5&operator=e2e_steward")
show("14-变更留痕", s, r); assert r["code"] == 0 and r["data"]["total"] >= 5

print("\n=== E2E FLOW ALL PASSED ===")
