"""配置：全部取自远程实测环境，环境变量可覆盖（便于测试）。"""
import os

# 数据库 DSN（远程实测；goods_app 读写 / goods_ro 只读）
PG_DSN_APP = os.getenv(
    "PG_DSN_APP",
    "host=127.0.0.1 port=5432 dbname=goods_mdm user=goods_app",
)
PG_DSN_RO = os.getenv(
    "PG_DSN_RO",
    "host=127.0.0.1 port=5432 dbname=goods_mdm user=goods_ro",
)

# JWT（HS256，8h）
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_TTL_HOURS = 8

# 登录失败锁定
LOGIN_MAX_ATTEMPTS = 5
LOCK_MINUTES = 10

# custom exception 与统一响应
API_PREFIX = "/api/v1"
