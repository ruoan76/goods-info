"""统一错误体系：业务拒绝 200+code / 401 / 403 / 422 / 500+error_id。

契约来源：接口方案 v1.2 §4.1 / §4.4。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------- 业务码常量（与接口 v1.2 §4.4 一致） ----------
CODE_OK = 0
CODE_TOKEN_INVALID = 2001
CODE_FORBIDDEN = 2002

CODE_DUP_BARCODE = 3001        # 条码已存在（BLOCK）
CODE_SUSPECT_SAME_NAME = 3002  # 疑似同名（WARN）
CODE_BANNED_BARCODE = 3003     # 条码在禁复用期
CODE_BOOK_ISBN = 3004          # 书号非商品条码
CODE_CATEGORY_INVALID = 3005   # 分类不存在或已停用
CODE_ATTR_REQUIRED = 3006      # 必填属性缺失
CODE_STATUS_ILLEGAL = 3007     # 状态流转非法
CODE_CATEGORY_HAS_GOODS = 3008 # 分类下有商品不可删
CODE_VERSION_CONFLICT = 3009   # 乐观锁冲突

CODE_IMPORT_FORMAT = 4001
CODE_IMPORT_PARTIAL = 4002
CODE_DEEP_PAGE = 4003

CODE_INTERNAL = 5000

MESSAGES = {
    CODE_OK: "ok",
    CODE_TOKEN_INVALID: "令牌无效或已过期",
    CODE_FORBIDDEN: "当前角色无此权限",
    CODE_DUP_BARCODE: "条码已被占用，不能重复建档",
    CODE_SUSPECT_SAME_NAME: "疑似同名商品，请人工核对",
    CODE_BANNED_BARCODE: "条码处于 90 天禁复用期，禁止使用",
    CODE_BOOK_ISBN: "书号 ISBN 非商品条码",
    CODE_CATEGORY_INVALID: "分类不存在或已停用",
    CODE_ATTR_REQUIRED: "必填属性缺失",
    CODE_STATUS_ILLEGAL: "状态流转非法",
    CODE_CATEGORY_HAS_GOODS: "分类下仍有商品，不可删除",
    CODE_VERSION_CONFLICT: "数据已被他人修改，请刷新重拉详情",
    CODE_IMPORT_FORMAT: "导入文件格式错误",
    CODE_IMPORT_PARTIAL: "部分行导入失败",
    CODE_DEEP_PAGE: "查询范围过大，请改用分类树或精确查询",
    CODE_INTERNAL: "服务端异常",
}


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": CODE_OK, "message": message, "data": data}


def fail(code: int, message: str | None = None, data: Any = None) -> dict:
    return {"code": code, "message": message or MESSAGES.get(code, "业务拒绝"), "data": data}


class BizError(Exception):
    """业务拒绝：统一以 HTTP 200 + 业务码返回（前端按 code 分支）。"""

    def __init__(self, code: int, message: str | None = None, data: Any = None):
        self.code = code
        self.message = message or MESSAGES.get(code, "业务拒绝")
        self.data = data
        super().__init__(self.message)


def gen_error_id() -> str:
    return "E-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:4].upper()


async def biz_error_handler(_: Request, exc: BizError) -> JSONResponse:
    return JSONResponse(status_code=200, content=fail(exc.code, exc.message, exc.data))


def _jsonable(obj):
    """pydantic v2 的 errors() 里 ctx.error 是异常对象，json.dumps 无法序列化，需降级为字符串。"""
    if isinstance(obj, Exception):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    return obj


async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # 422 保留 FastAPI detail 结构，前端可直接定位字段；
    # 必须把 ctx 里的 ValueError 等异常对象降级为字符串，否则 json.dumps 抛 500（实测 bug）
    return JSONResponse(status_code=422, content={"detail": _jsonable(exc.errors())})


async def token_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """401/403 统一业务码；其余 HTTPException 原样。"""
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content=fail(CODE_TOKEN_INVALID))
    if exc.status_code == 403:
        return JSONResponse(status_code=403, content=fail(CODE_FORBIDDEN))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def internal_handler(_: Request, exc: Exception) -> JSONResponse:
    """兜底 500 + error_id，便于内网排查。"""
    error_id = gen_error_id()
    # 生产应写日志；此处保留 error_id 返回
    return JSONResponse(
        status_code=500,
        content=fail(CODE_INTERNAL, data={"error_id": error_id}),
    )
