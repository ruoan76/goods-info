# gunicorn 配置 · UvicornWorker ×2（与令牌落库方案配套，多 worker 状态共享靠 DB）
bind = "127.0.0.1:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 200
timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "/var/log/goods-mdm/access.log"
errorlog = "/var/log/goods-mdm/error.log"
loglevel = "info"
proc_name = "goods-mdm"
# 请求 ID/耗时由 FastAPI 中间件记录；此处 access log 补状态码
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s'
