"""测试使用独立的本机 PostgreSQL 实例，默认只运行无数据库用例。"""
import os
from pathlib import Path
from secrets import token_urlsafe

import psycopg2
from psycopg2.extensions import make_dsn
import pytest


def pytest_configure():
    socket = os.environ.get("GOODS_MDM_TEST_SOCKET")
    port = os.environ.get("GOODS_MDM_TEST_PORT", "55432")
    database = os.environ.get("GOODS_MDM_TEST_DATABASE", "goods_mdm_test")
    if socket:
        if (
            not Path(socket).is_absolute()
            or "," in socket
            or not port.isdecimal()
            or not 1024 <= int(port) <= 65535
            or not database.startswith("goods_mdm_test")
            or not database.replace("_", "").isalnum()
        ):
            raise pytest.UsageError("测试需要独立的 Unix socket、高位端口及 goods_mdm_test 前缀库名")
        for suffix, role in (("APP", "goods_test_app"), ("RO", "goods_test_ro")):
            os.environ["PG_DSN_" + suffix] = make_dsn(
                host=socket, hostaddr="", port=port, dbname=database, user=role, connect_timeout=3,
            )
    else:
        for suffix in ("APP", "RO"):
            os.environ["PG_DSN_" + suffix] = make_dsn(
                host="/nonexistent/goods-mdm-test", hostaddr="", port=port,
                dbname="goods_mdm_test", user="goods_test_" + suffix.lower(), connect_timeout=3,
            )
    os.environ["JWT_SECRET"] = token_urlsafe(48)


@pytest.fixture(scope="session")
def test_db():
    if not os.environ.get("GOODS_MDM_TEST_SOCKET"):
        pytest.skip("未配置独立 PostgreSQL 测试实例")
    for suffix, role in (("APP", "goods_test_app"), ("RO", "goods_test_ro")):
        conn = psycopg2.connect(os.environ["PG_DSN_" + suffix])
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_database(), current_user, inet_server_addr(), "
                    "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user)"
                )
                expected_db = os.environ.get("GOODS_MDM_TEST_DATABASE", "goods_mdm_test")
                if cur.fetchone() != (expected_db, role, None, False):
                    pytest.fail("连接目标未通过 PostgreSQL 测试环境校验")
        finally:
            conn.close()


@pytest.fixture
def cur(test_db):
    """每个测试开一个连接，测试结束 rollback + close，不留痕。"""
    conn = psycopg2.connect(os.environ["PG_DSN_APP"])
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        conn.rollback()
        cursor.close()
        conn.close()


@pytest.fixture(scope="session")
def contract_users(test_db):
    """契约测试用三角色账号：session 开始创建，结束清理，不污染种子账号。"""
    from app.core.auth import hash_password
    conn = psycopg2.connect(os.environ["PG_DSN_APP"])
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
