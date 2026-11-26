"""双账号数据库连接池。

goods_app  读写池（业务表 DML；审计表仅 INSERT）
goods_ro   只读池（隔离区 dq_quarantine 强制走此池；DB 层已 REVOKE 写权限）

架构裁决④不引 Redis/MQ；连接池用 psycopg2 ThreadedConnectionPool。

连接自愈（2026-11-24）：SSL 长连接被中间设备或服务端断开后，池中会残留死连接，
取用即报 OperationalError: SSL connection has been closed unexpectedly。
故 getconn 后先做一次轻量探活，失败则丢弃该连接新建一条；同时 DSN 附加
TCP keepalive 参数，降低被中间设备静默回收的概率。
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from threading import Lock

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from .config import PG_DSN_APP, PG_DSN_RO

_log = logging.getLogger(__name__)

_pools: dict[str, ThreadedConnectionPool] = {}
_init_lock = Lock()

# 单次探活的超时上限（秒），避免死连接把请求拖住
_PROBE_TIMEOUT_MS = 3000

# TCP keepalive：让内核在连接空闲时周期性探测，及时发现对端已消失
_KEEPALIVE = "keepalives=1 keepalives_idle=60 keepalives_interval=10 keepalives_count=3"


def _dsn(base: str) -> str:
    """在基础 DSN 上附加 keepalive 与探活超时。已存在同名参数时不重复追加。"""
    extra = []
    if "keepalives" not in base:
        extra.append(_KEEPALIVE)
    if "connect_timeout" not in base:
        extra.append("connect_timeout=10")
    return base + (" " + " ".join(extra) if extra else "")


def _pool(which: str) -> ThreadedConnectionPool:
    with _init_lock:
        if which not in _pools:
            base = PG_DSN_APP if which == "app" else PG_DSN_RO
            _pools[which] = ThreadedConnectionPool(
                minconn=1, maxconn=10, dsn=_dsn(base)
            )
        return _pools[which]


def _checkout(which: str):
    """取一条可用连接。池中连接探活失败则关闭并重取，最多重试 3 次。

    探活使用独立连接的 statement_timeout，避免在死连接上无限等待。
    """
    p = _pool(which)
    last_exc = None
    for _ in range(3):
        c = p.getconn()
        try:
            with c.cursor() as cur:
                cur.execute("SET statement_timeout = %s", (_PROBE_TIMEOUT_MS,))
                cur.execute("SELECT 1")
            c.rollback()
            return p, c
        except psycopg2.Error as exc:
            last_exc = exc
            _log.warning("连接探活失败，丢弃并重取：%s", exc)
            # 关闭死连接且不归还池（close=True 从池中移除）
            try:
                p.putconn(c, close=True)
            except Exception:  # noqa: BLE001 - 关闭失败不应遮蔽原始探活错误
                pass
            continue
        except Exception as exc:  # noqa: BLE001 - 归还连接后才能上抛
            last_exc = exc
            try:
                p.putconn(c)
            except Exception:  # noqa: BLE001 - 归还失败不应遮蔽原始错误
                pass
            raise
    raise last_exc if last_exc else RuntimeError("连接池无法提供可用连接")


@contextmanager
def conn_app():
    """读写连接。用法：with conn_app() as c: ...（事务自动 commit/rollback）"""
    p, c = _checkout("app")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        p.putconn(c)


@contextmanager
def conn_app_manual():
    """手动事务连接：不自动 commit/rollback，由调用方显式控制。

    用于"先落库再抛异常"的场景（如登录失败计数必须先提交再返回 401），
    避免异常触发自动回滚把状态更新撤销。
    """
    p, c = _checkout("app")
    try:
        yield c
    finally:
        p.putconn(c)


@contextmanager
def conn_ro():
    """只读连接（隔离区强制）。只读事务，结束即 rollback 释放。"""
    p, c = _checkout("ro")
    try:
        yield c
        c.rollback()
    finally:
        p.putconn(c)


def check_database_readiness() -> None:
    """Verify both database roles can connect and execute a read-only query."""
    for dsn in (PG_DSN_APP, PG_DSN_RO):
        conn = psycopg2.connect(
            dsn,
            connect_timeout=2,
            options="-c default_transaction_read_only=on -c statement_timeout=1500",
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            conn.close()


def close_pools():
    for p in _pools.values():
        p.closeall()
    _pools.clear()
