import { createRouter, createWebHistory } from "vue-router";
import { useAppStore } from "./store.js";

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: "/", redirect: "/dashboard" },
    {
      path: "/login",
      name: "login",
      component: () => import("./views/Login.vue"),
      meta: { public: true },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("./views/Dashboard.js"),
      meta: { title: "工作台" },
    },
    {
      path: "/goods",
      name: "goods",
      component: () => import("./views/GoodsList.js"),
      meta: { title: "商品档案" },
    },
    {
      path: "/goods/new",
      name: "goods-new",
      component: () => import("./views/GoodsNew.js"),
      meta: { title: "新增商品", write: true },
    },
    {
      path: "/goods/:barcode/detail",
      name: "goods-detail",
      component: () => import("./views/GoodsDetail.js"),
      meta: { title: "商品详情" },
    },
    {
      path: "/fillprice",
      name: "fillprice",
      component: () => import("./views/FillPrice.js"),
      meta: { title: "价格待补清单", write: true },
    },
    {
      path: "/categories",
      name: "category",
      component: () => import("./views/Category.js"),
      meta: { title: "分类与属性模板", admin: true },
    },
    {
      path: "/barcodes",
      name: "barcode",
      component: () => import("./views/Barcode.js"),
      meta: { title: "条码管理", admin: true },
    },
    {
      path: "/dictionary",
      name: "dict",
      component: () => import("./views/Dictionary.js"),
      meta: { title: "基础字典", admin: true },
    },
    {
      path: "/governance",
      name: "govern",
      component: () => import("./views/Governance.js"),
      meta: { title: "数据治理", admin: true },
    },
    {
      path: "/users",
      name: "users",
      component: () => import("./views/Users.js"),
      meta: { title: "用户管理", admin: true },
    },
  ],
});

router.beforeEach((to) => {
  const store = useAppStore();
  if (to.meta.public) return store.logged ? { name: "dashboard" } : true;
  if (!store.logged) return { name: "login", query: { redirect: to.fullPath } };
  if ((to.meta.admin && !store.isAdmin) || (to.meta.write && !store.canWrite)) {
    store.toast("当前角色无此权限", "err");
    return { name: "dashboard" };
  }
});
