import sys
sys.path.insert(0, "/data/projects/goods-info/09_管理系统/backend")
from fastapi.testclient import TestClient
from app.core.auth import issue_token
from app.core.config import PG_DSN_APP
from app.main import app
import psycopg2, json

c = psycopg2.connect(PG_DSN_APP)
cur = c.cursor()
bc="8800100100100"
for t in ("mdm_goods_attrs","mdm_goods_history","mdm_barcode_alias"):
    cur.execute(f"delete from {t} where barcode=%s" if t!="mdm_barcode_alias" else f"delete from {t} where alias_barcode=%s",(bc,))
cur.execute("delete from mdm_goods where barcode=%s",(bc,))
c.commit(); cur.close(); c.close()

client=TestClient(app)
tok=issue_token("e2e_steward","Steward",0)
h={"Authorization":"Bearer "+tok}
def call(m,p,b=None):
    r=client.request(m,p,json=b,headers=h)
    return r.status_code, r.json()

s,r=call("POST","/api/v1/goods",{"barcode":bc,"goods_name":"E2E测试商品-唯品","category_id":"C0203","unit_id":"000007","inprice":100,"outprice":150,"quality_grade":"B"})
print("建档",s,r.get("code"),r.get("message"))
assert r["code"]==0
s,r=call("POST","/api/v1/goods/check",{"barcode":bc,"goods_name":"E2E测试商品-唯品"})
print("再查重",s,r["data"]["verdict"])
assert r["data"]["verdict"]=="BLOCK"
s,r=call("PATCH",f"/api/v1/goods/{bc}",{"field":"outprice","new_value":"220.00","reason":"调价"})
print("PATCH",s,r.get("code"),r.get("data"))
assert r["code"]==0
s,r=call("PUT",f"/api/v1/goods/{bc}/attrs",{"attrs":{"净含量":"500ml"}})
print("属性写",s,r.get("code"))
s,r=call("GET",f"/api/v1/goods/{bc}")
print("详情history数",len(r["data"]["history"]))
s,r=call("POST",f"/api/v1/goods/{bc}/status",{"to_status":"INACTIVE","reason":"停用"})
print("停用",s,r.get("code"))
s,r=call("POST",f"/api/v1/goods/{bc}/status",{"to_status":"VOIDED","reason":"作废"})
print("作废",s,r.get("code"))
s,r=call("POST","/api/v1/barcodes/validate",{"barcode":bc})
print("禁复用",s,r["data"]["in_ban_period"],r["data"]["allowed"])
assert r["data"]["in_ban_period"] and not r["data"]["allowed"]
print("\n=== QUICK E2E PASS ===")
