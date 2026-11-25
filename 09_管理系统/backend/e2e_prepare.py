import os

import psycopg2
from app.core.auth import hash_password
from app.core.config import PG_DSN_APP

h = hash_password(os.environ["GOODS_E2E_PASSWORD"])
c = psycopg2.connect(PG_DSN_APP)
cur = c.cursor()
cur.execute("DELETE FROM sys_user WHERE account=%s", ("e2e_steward",))
cur.execute(
    "INSERT INTO sys_user(account,display_name,role,status,password_hash) VALUES(%s,%s,%s,%s,%s)",
    ("e2e_steward", "E2E管理员", "Steward", "ACTIVE", h),
)
# 清理可能残留的测试条码
for bc in ("8800100100100", "8800100100101"):
    cur.execute("DELETE FROM mdm_goods_attrs WHERE barcode=%s", (bc,))
    cur.execute("DELETE FROM mdm_goods_history WHERE barcode=%s", (bc,))
    cur.execute("DELETE FROM mdm_barcode_alias WHERE alias_barcode=%s", (bc,))
    cur.execute("DELETE FROM mdm_goods WHERE barcode=%s", (bc,))
c.commit()
print("e2e account + clean barcode ready")
cur.close(); c.close()
