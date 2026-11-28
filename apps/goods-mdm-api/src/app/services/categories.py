"""分类路径和准入规则；每次请求一次目录读取，不按商品逐条查询。"""
from __future__ import annotations

from ..core.errors import CODE_CATEGORY_INVALID, BizError


def category_paths(cur, *, for_write=False):
    cur.execute("SELECT category_id, parent_id, category_name, status, is_leaf "
                "FROM mdm_category" + (" FOR SHARE" if for_write else ""))
    nodes = {row[0]: row[1:] for row in cur.fetchall()}
    paths = {}
    for cid in nodes:
        chain, seen, current = [], set(), cid
        while current is not None:
            if current in seen or current not in nodes:
                chain = []  # Broken trees have no complete path, never a misleading partial path.
                break
            seen.add(current)
            chain.append(current)
            current = nodes[current][0]
        if chain:
            chain.reverse()
            paths[cid] = {
                "code": "/" + "/".join(chain) + "/",
                "name": " / ".join(nodes[key][1] for key in chain),
                "active": all(nodes[key][2] == "ACTIVE" for key in chain),
                "leaf": bool(nodes[cid][3]),
            }
    return paths


def goods_category_path(cur, category_id):
    if category_id is None:
        return None
    path = category_paths(cur, for_write=True).get(category_id)
    if not path or not path["active"] or not path["leaf"]:
        raise BizError(CODE_CATEGORY_INVALID, "分类须为有效且启用的末级节点，父链不得缺失或循环")
    return path["code"]
