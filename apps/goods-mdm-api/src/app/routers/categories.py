"""分类域 7 端点。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core import auth as A
from ..core.audit import audit, gen_batch_id
from ..core.db import conn_app
from ..core.errors import CODE_CATEGORY_HAS_GOODS, BizError, ok
from ..daos import catalog as dc
from ..schemas.admin import ExternalMapWrite, TemplateWrite

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("/tree", summary="分类全量树")
def tree(_: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.category_tree(cur))


@router.put("/{cid}", summary="分类节点维护")
def update_node(cid: str, body: dict, user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        node = dc.category_node(cur, cid)
        if not node:
            return ok(None)
        dc.update_category(cur, cid, body)
        batch = gen_batch_id(user["account"])
        audit(cur, entity_type="CATEGORY", entity_key=cid, action="NODE_UPDATE",
              operator=user["account"], before=node, after=body, batch_id=batch)
    return ok({"category_id": cid, "updated": True})


@router.post("/{cid}/impact", summary="调整影响分析")
def impact(cid: str, _: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        r = dc.category_impact(cur, cid)
        if not r["can_delete"] and r["goods_count"] > 0:
            r["message"] = "分类下仍有商品，不可删除"
        return ok(r)


@router.get("/{cid}/template", summary="属性模板读取")
def get_template(cid: str, _: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.get_template(cur, cid))


@router.put("/{cid}/template", summary="属性模板写入")
def put_template(cid: str, body: TemplateWrite, user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        old = dc.get_template(cur, cid)
        dc.put_template(cur, cid, body.template, user["account"])
        audit(cur, entity_type="CATEGORY_TEMPLATE", entity_key=cid, action="TEMPLATE_WRITE",
              operator=user["account"], before=old, after=body.template,
              batch_id=gen_batch_id(user["account"]))
    return ok({"category_id": cid, "updated": True})


@router.get("/{cid}/external-map", summary="外部编码对照查询")
def get_ext_map(cid: str, _: dict = Depends(A.require_role(*A.ALL_ROLES))):
    with conn_app() as c, c.cursor() as cur:
        return ok(dc.external_map(cur, cid))


@router.put("/{cid}/external-map", summary="外部编码映射维护")
def put_ext_map(cid: str, body: ExternalMapWrite, user: dict = Depends(A.require_role(A.STEWARD))):
    with conn_app() as c, c.cursor() as cur:
        old = dc.external_map(cur, cid)
        n = dc.put_external_map(cur, cid, body.mappings)
        audit(cur, entity_type="CATEGORY_MAP", entity_key=cid, action="EXTERNAL_MAP_WRITE",
              operator=user["account"], before={"total": old["total"]},
              after={"updated": n}, batch_id=gen_batch_id(user["account"]))
    return ok({"category_id": cid, "updated": n})
