"""测试夹具：真实 DB 连接（远程 goods_mdm），每个测试用事务回滚隔离。"""
import os
import sys

import psycopg2
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import PG_DSN_APP


@pytest.fixture
def cur():
    """每个测试开一个连接，测试结束 rollback + close，不留痕。"""
    conn = psycopg2.connect(PG_DSN_APP)
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def contract_users():
    """契约测试用三角色账号：session 开始创建，结束清理，不污染种子账号。"""
    from app.core.auth import hash_password
    conn = psycopg2.connect(PG_DSN_APP)
    cur = conn.cursor()
    accounts = [("ct_viewer", "Viewer"), ("ct_operator", "Operator"), ("ct_steward", "Steward")]
    try:
        for acct, role in accounts:
            cur.execute("DELETE FROM sys_user WHERE account=%s", (acct,))
            cur.execute(
                "INSERT INTO sys_user(account,display_name,role,status,password_hash) "
                "VALUES(%s,%s,%s,'ACTIVE',%s)",
                (acct, acct, role, hash_password("Contract123!")),
            )
        conn.commit()
        yield
    finally:
        for acct, _ in accounts:
            cur.execute("DELETE FROM sys_user WHERE account=%s", (acct,))
        conn.commit()
        cur.close()
        conn.close()
