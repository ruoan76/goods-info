"""FastAPI 应用工厂：中间件 + 错误注册 + 路由挂载。"""
from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core import config
from .core.errors import (
    BizError,
    biz_error_handler,
    internal_handler,
    token_error_handler,
    validation_handler,
)
from .routers import auth as auth_router
from .routers import goods as goods_router
from .routers import categories as categories_router
from .routers import attributes as attributes_router
from .routers import barcodes as barcodes_router
from .routers import admin as admin_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="商品主数据管理系统 API",
        version="1.2",
        description="40 端点契约见接口方案 v1.2；六域全量实现（auth/goods/categories/attributes/barcodes/admin）",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # 请求 ID 中间件：注入 X-Request-ID，记录耗时/状态码
    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        start = time.time()
        response = await call_next(request)
        cost_ms = (time.time() - start) * 1000
        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time"] = f"{cost_ms:.1f}ms"
        return response

    # 统一错误注册
    app.add_exception_handler(BizError, biz_error_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(StarletteHTTPException, token_error_handler)
    app.add_exception_handler(Exception, internal_handler)

    # 路由：6 域 40 端点全部挂载
    for r in (auth_router.router, goods_router.router, categories_router.router,
              attributes_router.router, barcodes_router.router, admin_router.router):
        app.include_router(r, prefix=config.API_PREFIX)

    @app.get("/health", tags=["运维"])
    def health():
        return {"status": "ok", "version": "1.2"}

    return app


app = create_app()
