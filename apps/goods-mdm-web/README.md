# goods-mdm-web

Vue 3 商品主数据管理前端。登录页和应用外壳使用 Vue 单文件组件。其余业务页面位于 `src/views`，使用 Vue 渲染函数保留原发布版的业务交互。

## 构建与发布

在本目录使用 Node.js 22 运行 `npm ci` 和 `npm run build`。依赖由 `package-lock.json` 锁定，构建产物位于 `dist/`。通过 `ops/deploy/deploy_frontend.sh publish BUILD_DIR` 发布，Nginx 从 `/var/www/goods-mdm/current` 提供当前版本。使用 `ops/deploy/deploy_frontend.sh rollback RELEASE_ID` 切回已归档的版本。

## 源码来源

2026-11-23 的部署流程在 Mac 构建后向服务器传输 `dist/`。服务器上的项目备份和 Git 历史保留了联通验证页，发布包保存了完整页面编译产物。当前工程依据生产发布包重建，依赖、组件、样式、路由和 API 接口均纳入源码管理。之前的发布包保存在数据盘 `/data/archive/goods-info-review-20261127`。

商品详情编辑携带编辑开始时的版本号，批量补价携带列表行的版本号。登录页使用用户输入的凭据，新增和重置账号时显示后端生成的初始密码。
