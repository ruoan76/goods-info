from secrets import token_urlsafe

import sys, json
sys.path.insert(0, "/data/projects/goods-info/09_管理系统/backend")
from fastapi.testclient import TestClient
from app.core.auth import issue_token, hash_password
from app.core.config import PG_DSN_APP
from app.main import app
import psycopg2

conn=psycopg2.connect(PG_DSN_APP); cur=conn.cursor()
cur.execute("DELETE FROM sys_user WHERE account='probe'")
cur.execute("INSERT INTO sys_user(account,display_name,role,status,password_hash) VALUES('probe','探针','Steward','ACTIVE',%s)",(hash_password(token_urlsafe(32)),))
conn.commit(); cur.close(); conn.close()

c = TestClient(app)
h = {"Authorization": "Bearer " + issue_token("probe", "Steward", 0)}

def probe(label, method, path, **kw):
    kw.setdefault("headers", h)
    try:
        r = c.request(method, path, **kw)
        j = r.json()
        d = j.get("data") if isinstance(j, dict) else j
        s = json.dumps(d, ensure_ascii=False)
        if len(s) > 900:
            s = s[:900] + "..."
        print(f"\n### {label}  [{method} {path}]  code={j.get('code') if isinstance(j,dict) else '?'}")
        print(s)
    except Exception as e:
        print(f"\n### {label} ERROR: {e}")

probe("dashboard", "GET", "/api/v1/admin/dashboard")
probe("change-log", "GET", "/api/v1/admin/change-log?limit=3")
probe("goods list", "GET", "/api/v1/goods?page=1&page_size=2")
probe("goods detail", "GET", "/api/v1/goods/6901035623162")
probe("goods attrs", "GET", "/api/v1/goods/6901035623162/attrs")
probe("check", "POST", "/api/v1/goods/check", json={"barcode":"6901035623162","goods_name":"青岛啤酒经典1903"})
probe("check-new", "POST", "/api/v1/goods/check", json={"barcode":"6901234567890","goods_name":"测试新品XYZ"})
probe("cat tree", "GET", "/api/v1/categories/tree")
probe("cat impact", "POST", "/api/v1/categories/C0203/impact")
probe("cat template", "GET", "/api/v1/categories/C0203/template")
probe("cat extmap", "GET", "/api/v1/categories/C0203/external-map")
probe("validate", "POST", "/api/v1/barcodes/validate", json={"barcode":"6901035623162"})
probe("units", "GET", "/api/v1/admin/units")
probe("sources", "GET", "/api/v1/admin/sources")
probe("users", "GET", "/api/v1/admin/users")
probe("quarantine", "GET", "/api/v1/admin/quarantine?page=1&page_size=2")
probe("attributes", "GET", "/api/v1/attributes")
