# goods-mdm-api

FastAPI 商品主数据管理 API。

源码位于 `src/app`，测试位于 `tests`，联调工具位于 `tools`。运行时通过 `PG_DSN_APP`、`PG_DSN_RO` 和 `JWT_SECRET` 注入配置。

运维可通过 `GET /health` 检查 API 进程，通过 `GET /ready` 检查两个 PostgreSQL 账号的连接和只读查询。数据库不可用时，`/ready` 返回 HTTP 503。

当前写入、分类路径、ISBN 和导出上限契约见 [维护说明](../../docs/maintenance/goods-mdm-write-contracts.md)。商品和治理清单导出均最多 20 万条数据行，超限会在文件末尾提示截断。
