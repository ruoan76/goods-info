<script setup>
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { useAppStore } from "./store.js";

const store = useAppStore();
const route = useRoute();
const router = useRouter();
const workspace = [
  { name: "dashboard", title: "工作台" },
  { name: "goods", title: "商品档案" },
  { name: "goods-new", title: "新增商品", write: true },
];
const administration = [
  { name: "category", title: "分类与属性模板" },
  { name: "barcode", title: "条码管理" },
  { name: "dict", title: "基础字典" },
  { name: "govern", title: "数据治理" },
  { name: "users", title: "用户管理" },
];

async function logout() {
  await store.logout();
  await router.push({ name: "login" });
  store.toast("已安全退出", "ok");
}
</script>

<template>
  <RouterView v-if="route.name === 'login'" />
  <div v-else class="shell">
    <aside class="sidebar">
      <div class="logo">商品主数据管理系统</div>
      <nav class="nav-group" aria-label="商品工作台">
        <div class="gt">商品工作台</div>
        <template v-for="item in workspace" :key="item.name">
          <RouterLink
            v-if="!item.write || store.canWrite"
            :to="{ name: item.name }"
            class="nav-item"
            exact-active-class="active"
          >
            <span>{{ item.title }}</span>
          </RouterLink>
        </template>
      </nav>
      <nav v-if="store.isAdmin" class="nav-group admin" aria-label="管理后台">
        <div class="gt">管理后台</div>
        <RouterLink
          v-for="item in administration"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav-item"
          exact-active-class="active"
        >
          <span>{{ item.title }}</span>
        </RouterLink>
      </nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="crumb">
          {{ route.meta.admin ? "管理后台" : "商品工作台" }} /
          <b>{{ route.meta.title || "工作台" }}</b>
        </div>
        <div class="userbox">
          <span class="avatar">{{
            (store.name || "U").slice(0, 1).toUpperCase()
          }}</span>
          <span>{{ store.name || store.account }}</span>
          <span
            class="role-tag"
            :class="{ adm: store.isAdmin, ro: store.isRO }"
            >{{ store.roleCn }}</span
          >
          <button class="btn plain sm" @click="logout">退出</button>
        </div>
      </header>
      <div class="content"><RouterView /></div>
    </main>
  </div>
  <div
    v-for="toast in store.toasts"
    :key="toast.id"
    class="toast"
    :class="toast.type"
    role="status"
  >
    {{ toast.message }}
  </div>
</template>
