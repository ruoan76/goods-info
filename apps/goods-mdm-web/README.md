# goods-mdm-web

Vue 3 商品主数据管理前端。当前源码包含联通验证页。线上完整页面的 Vue 源码仍待找回。

现有线上版本使用 2026-11-23 的发布包，经 `ops/deploy/prepare_goods_version_release.py` 为商品详情和补价请求加入商品版本号。该脚本核对原始文件摘要，并为新资源生成独立文件名。基准发布包及回退信息存放在数据盘 `/data/archive/goods-info-review-20261127`。

发布和回退使用 `ops/deploy/deploy_frontend.sh publish BUILD_DIR` 和 `ops/deploy/deploy_frontend.sh rollback RELEASE_ID`。Nginx 从 `/var/www/goods-mdm/current` 提供已选中的版本。
