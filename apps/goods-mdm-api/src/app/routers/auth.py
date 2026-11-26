"""认证域 2 端点：POST /auth/token · POST /auth/logout"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm

from ..core import auth as auth_core
from ..core.errors import ok

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/token", summary="OAuth2 密码流换 JWT")
def token(form: OAuth2PasswordRequestForm = Depends()):
    result = auth_core.authenticate(form.username, form.password)
    account, role, ver = result
    token_str = auth_core.issue_token(account, role, ver)
    return ok({
        "access_token": token_str,
        "token_type": "bearer",
        "expires_in": auth_core.config.JWT_TTL_HOURS * 3600,
        "role": role,
    })


@router.post("/logout", summary="登出（token_version+1 全 worker 失效）")
def logout(user: dict = Depends(auth_core.current_user)):
    auth_core.logout(user["account"])
    return ok({"account": user["account"]})
