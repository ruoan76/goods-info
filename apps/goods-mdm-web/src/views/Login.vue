<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { errorMessage } from "../api.js";
import { useAppStore } from "../store.js";

const store = useAppStore();
const route = useRoute();
const router = useRouter();
const account = ref("");
const password = ref("");
const pending = ref(false);
const message = ref("");

async function login() {
  pending.value = true;
  message.value = "";
  try {
    await store.login(account.value.trim(), password.value);
    store.toast(`欢迎回来，${store.roleCn} · ${store.account}`, "ok");
    const redirect = route.query.redirect;
    await router.push(
      typeof redirect === "string" &&
        redirect.startsWith("/") &&
        !redirect.startsWith("//")
        ? redirect
        : "/dashboard",
    );
  } catch (error) {
    message.value = errorMessage(error);
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <div id="login">
    <form class="login-box" @submit.prevent="login">
      <h2>商品主数据管理系统</h2>
      <div class="sub">统一维护，全库一致</div>
      <div class="field">
        <label for="login-account">用户名</label>
        <input
          id="login-account"
          v-model="account"
          autocomplete="username"
          required
        />
      </div>
      <div class="field">
        <label for="login-password">密码</label>
        <input
          id="login-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
        />
      </div>
      <p v-if="message" class="result-line err" role="alert">{{ message }}</p>
      <button class="btn" type="submit" :disabled="pending">
        {{ pending ? "登录中…" : "登录" }}
      </button>
    </form>
  </div>
</template>
