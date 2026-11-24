# 商品主数据管理系统

后端使用 FastAPI 和 PostgreSQL。前端源码在 frontend/src，评审原型在 prototype。

- 启动后端前，在运行环境中设置 JWT_SECRET。数据库连接可通过 PG_DSN_APP 和 PG_DSN_RO 配置。默认目标是本机 5432 端口的 goods_mdm，分别使用 goods_app 和 goods_ro。可用权限为 0600 的 .pgpass 提供数据库密码。
- 在现有 goods_mdm 基础库上初始化管理系统时，以管理员身份运行 migrations/m1_init.sql。首次创建 goods_ro 后，在 psql 中执行 \password goods_ro 设置密码。
- 首次运行 backend/e2e_prepare.py 前，在测试环境设置 GOODS_E2E_PASSWORD。
- 使用 deploy/backup_goods_mdm.sh 时，通过 libpq 提供 goods_app 的密码。整库备份要求执行账号具备所有表的读取权限。
