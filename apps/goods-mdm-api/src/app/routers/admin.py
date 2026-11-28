"""管理后台域 14 端点。"""
from __future__ import annotations

import csv
import io
import secrets

from fastapi import APIRouter, Depends, Query

from ..core import auth as A
from ..core.audit import audit, gen_batch_id
from ..core.streaming import ClosingStreamingResponse
from ..core.db import conn_app, conn_ro
from ..core.errors import ok
from ..daos import admin as da
from ..schemas.admin import UnitCreate, UnitUpdate, UserCreate, UserUpdate

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/dashboard", summary="首页统计概览")
def dashboard(user: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        data = da.dashboard(cur)
        data.update(da.quality_metrics(cur))
    with conn_ro() as c, c.cursor() as cur:  # 隔离区计数强制 goods_ro
        data["quarantine_conflict"] = da.dashboard_quarantine(cur)
    return ok(data)


@router.get("/change-log", summary="最近处理时间轴")
def change_log(limit: int = 10, operator: str | None = None,
               _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(da.change_log(cur, limit, operator))


@router.get("/units", summary="单位字典列表")
def list_units(_: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        return ok(da.list_units(cur))


@router.post("/units", summary="新增单位")
def create_unit(body: UnitCreate, user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        da.create_unit(cur, body.code, body.name, body.sort_order, body.enabled)
        audit(cur, entity_type="UNIT", entity_key=body.code, action="CREATE",
              operator=user["account"], after=body.model_dump(),
              batch_id=gen_batch_id(user["account"]))
    return ok({"code": body.code, "created": True})


@router.put("/units/{code}", summary="编辑单位")
def update_unit(code: str, body: UnitUpdate, user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        da.update_unit(cur, code, body.model_dump(exclude_none=True))
        audit(cur, entity_type="UNIT", entity_key=code, action="UPDATE",
              operator=user["account"], after=body.model_dump(exclude_none=True),
              batch_id=gen_batch_id(user["account"]))
    return ok({"code": code, "updated": True})


@router.get("/sources", summary="来源可靠程度")
def sources(_: dict = Depends(A.require_role(*A.ALL_ROLES))):
    from ..daos.catalog import list_sources
    with conn_app() as c, c.cursor() as cur:
        return ok(list_sources(cur))


@router.get("/quarantine", summary="隔离区只读（goods_ro）")
def quarantine(issue_type: str | None = None, batch_id: str | None = None,
               status: str | None = None, page: int = 1, page_size: int = 20,
               _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    from ..daos.catalog import list_quarantine
    params = dict(issue_type=issue_type, batch_id=batch_id, status=status,
                  page=page, page_size=page_size)
    with conn_ro() as c, c.cursor() as cur:  # 强制只读账号
        return ok(list_quarantine(cur, params))


@router.get("/quarantine/export", summary="治理清单导出（goods_ro）")
def quarantine_export(issue_type: str | None = None, batch_id: str | None = None,
                      _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    from ..daos.catalog import quarantine_export as qe
    params = dict(issue_type=issue_type, batch_id=batch_id)
    def gen():
        with conn_ro() as c, c.cursor(name="quarantine_export") as cur:
            qe(cur, params, limit=200001)
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(["条码", "问题类型", "涉及商品数", "状态", "发现时间"])
            yield "\ufeff" + buf.getvalue(); buf.seek(0); buf.truncate(0)
            emitted = 0
            while emitted < 200000:
                rows = cur.fetchmany(min(2000, 200000 - emitted))
                if not rows:
                    break
                for r in rows:
                    w.writerow([r[0], r[1], r[2], r[3], str(r[4])])
                emitted += len(rows)
                yield buf.getvalue(); buf.seek(0); buf.truncate(0)
            if emitted == 200000 and cur.fetchmany(1):
                w.writerow(["#", "已达到导出上限 200000 行，结果已截断，请缩小筛选范围", "", "", ""])
                yield buf.getvalue()
    return ClosingStreamingResponse(gen(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="quarantine.csv"',
                             "X-Export-Limit": "200000"})


@router.get("/users", summary="用户列表")
def list_users(q: str | None = None, role: str | None = None, status: str | None = None,
               _: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        return ok(da.list_users(cur, q, role, status))


@router.post("/users", summary="新增用户")
def create_user(body: UserCreate, user: dict = Depends(A.require_role(A.STEWARD))):
    initial = secrets.token_urlsafe(9)
    pwd_hash = A.hash_password(initial)
    batch = gen_batch_id(user["account"])
    with conn_app() as c, c.cursor() as cur:
        da.create_user(cur, body.account, body.name, body.role, pwd_hash, body.dept, body.phone)
        audit(cur, entity_type="USER", entity_key=body.account, action="CREATE",
              operator=user["account"], after=body.model_dump(),
              batch_id=batch)
    return ok({"account": body.account, "initial_password": initial})


@router.put("/users/{account}", summary="编辑/改角色/启停")
def update_user(account: str, body: UserUpdate, user: dict = Depends(A.require_role(A.STEWARD))):
    batch = gen_batch_id(user["account"])
    with conn_app() as c, c.cursor() as cur:
        old = da.list_users(cur, q=account, role=None, status=None)
        da.update_user(cur, account, body.model_dump(exclude_none=True))
        # 账号停用：令牌立即失效（token_version+1）
        if body.status == "INACTIVE":
            cur.execute("UPDATE sys_user SET token_version=token_version+1 WHERE account=%s", (account,))
        audit(cur, entity_type="USER", entity_key=account, action="UPDATE",
              operator=user["account"], after=body.model_dump(exclude_none=True),
              batch_id=batch)
    return ok({"account": account, "updated": True})


@router.post("/users/{account}/reset-password", summary="重置密码")
def reset_password(account: str, user: dict = Depends(A.require_role(A.STEWARD))):
    initial = secrets.token_urlsafe(9)
    with conn_app() as c, c.cursor() as cur:
        da.reset_password(cur, account, A.hash_password(initial))
        audit(cur, entity_type="USER", entity_key=account, action="PASSWORD_RESET",
              operator=user["account"], after={"account": account},
              batch_id=gen_batch_id(user["account"]))
    return ok({"account": account, "initial_password": initial})


@router.get("/users/{account}/activity", summary="用户最近活动")
def user_activity(account: str, _: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        log = da.change_log(cur, limit=50, operator=account)
    return ok({"items": [{"date": i["changed_at"][:10], "event": i["action"]}
                         for i in log["items"]], "total": log["total"]})


@router.get("/import-jobs/{job_id}", summary="导入进度与失败行清单")
def import_job(job_id: int, _: dict = Depends(A.require_role(A.OPERATOR, A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        return ok(da.get_import_job(cur, job_id))
