"""认证：PBKDF2 密码 + JWT HS256(8h) + token_version 落库 + 失败锁定。

关键修正（方案 v1.2 P0-2）：
    登出不用内存黑名单（2 worker 多进程不共享），改为 sys_user.token_version+1；
    JWT claim.ver 与库中不一致即拒 → 旧令牌在全 worker 立即失效。
    登录失败 failed_attempts+1，达 5 次写 locked_until=now()+10min，成功清零。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, Header, HTTPException, status

from . import config
from .db import conn_app, conn_app_manual


# ---------------- PBKDF2 密码 ----------------
_PBKDF2_ROUNDS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return "pbkdf2_sha256${}${}${}".format(
        _PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, dk_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, int(rounds)
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


# ---------------- JWT ----------------
def issue_token(account: str, role: str, token_version: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": account,
        "role": role,
        "ver": token_version,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_TTL_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])


# ---------------- 登录状态（落库，跨 worker 一致） ----------------
def authenticate(account: str, password: str) -> tuple[str, str, int] | None:
    """校验账号密码与锁定状态；成功返回 (account, role, token_version)。

    失败抛 HTTPException(401)，错误信息不区分"账号不存在/密码错"（防枚举）。
    """
    # 用手动事务：失败计数的 UPDATE 必须先 commit 再抛 401，
    # 否则异常会触发自动回滚把计数撤销（实测曾导致 5 次失败不锁定）。
    with conn_app_manual() as c:
        try:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT account, role, status, password_hash, token_version, "
                    "failed_attempts, locked_until FROM sys_user "
                    "WHERE account=%s FOR UPDATE",
                    (account,),
                )
                row = cur.fetchone()
                now = datetime.now(timezone.utc)

                if row is None:
                    verify_password(password, hash_password("dummy"))  # 防枚举：拉平时序
                    c.rollback()
                    raise HTTPException(status_code=401, detail="invalid credentials")

                (acct, role, status_, pwd_hash, ver, failed, locked_until) = row

                if locked_until and locked_until > now:
                    c.rollback()
                    raise HTTPException(status_code=401, detail="account locked")

                if status_ != "ACTIVE":
                    c.rollback()
                    raise HTTPException(status_code=401, detail="account inactive")

                if not verify_password(password, pwd_hash):
                    failed = (failed or 0) + 1
                    locked = now + timedelta(minutes=config.LOCK_MINUTES) \
                        if failed >= config.LOGIN_MAX_ATTEMPTS else None
                    cur.execute(
                        "UPDATE sys_user SET failed_attempts=%s, locked_until=%s "
                        "WHERE account=%s",
                        (failed, locked, account),
                    )
                    c.commit()  # 关键：先提交失败计数，再抛 401
                    raise HTTPException(status_code=401, detail="invalid credentials")

                # 成功：清零失败计数与锁定
                cur.execute(
                    "UPDATE sys_user SET failed_attempts=0, locked_until=NULL, "
                    "last_login=now() WHERE account=%s",
                    (account,),
                )
                c.commit()
                return acct, role, ver
        except HTTPException:
            raise
        except Exception:
            c.rollback()
            raise


def logout(account: str) -> None:
    """登出：token_version+1，当前及旧令牌全 worker 立即失效。"""
    with conn_app() as c:
        with c.cursor() as cur:
            cur.execute(
                "UPDATE sys_user SET token_version=token_version+1 WHERE account=%s",
                (account,),
            )


# ---------------- 依赖：当前用户 / 角色守卫 ----------------
def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token")

    account = claims.get("sub")
    ver = claims.get("ver")
    with conn_app() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT role, status, token_version FROM sys_user WHERE account=%s",
                (account,),
            )
            row = cur.fetchone()
    if row is None or row[1] != "ACTIVE" or row[2] != ver:
        # 账号停用或令牌版本落后（已登出/已改密）→ 拒
        raise HTTPException(status_code=401, detail="token revoked")
    return {"account": account, "role": row[0], "ver": ver}


def require_role(*roles: str) -> Callable:
    """端点级角色守卫：JWT claim.role 唯一依据，不信任 body/query 的 role。"""

    def _guard(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return _guard


VIEWER = "Viewer"
OPERATOR = "Operator"
STEWARD = "Steward"
ALL_ROLES = (VIEWER, OPERATOR, STEWARD)
