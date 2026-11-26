import { defineStore } from "pinia";
import { authApi, getToken, setToken, setUnauthorizedHandler } from "./api.js";

export const roleLabels = {
  Operator: "录入员",
  Steward: "管理员",
  Viewer: "只读",
};
export const roleColors = {
  Operator: "#409eff",
  Steward: "#7c3aed",
  Viewer: "#909399",
};
export const roleClasses = {
  Operator: "tg-blue",
  Steward: "tg-violet",
  Viewer: "tg-gray",
};
export const rolePermissions = {
  Operator: [
    "查看商品、按分类浏览、按条码/名称查询",
    "新增商品、修改名称/价格/属性",
  ],
  Steward: [
    "查看商品、按分类浏览、按条码/名称查询",
    "新增商品、修改名称/价格/属性",
    "停用商品",
    "作废商品（不可逆）",
    "分类、属性模板、条码、字典",
    "用户管理（新增/停用/改角色）",
    "导出数据",
  ],
  Viewer: ["查看商品、按分类浏览、按条码/名称查询", "导出数据"],
};

export const useAppStore = defineStore("app", {
  state: () => ({
    token: "",
    account: "",
    name: "",
    role: "",
    logged: false,
    toasts: [],
    toastSequence: 0,
  }),
  getters: {
    isAdmin: (state) => state.role === "Steward",
    isRO: (state) => state.role === "Viewer",
    canWrite: (state) => state.role === "Operator" || state.role === "Steward",
    roleCn: (state) => roleLabels[state.role] || state.role || "未登录",
  },
  actions: {
    startSession(token, account, role) {
      setToken(token);
      this.token = token;
      this.account = this.name = account;
      this.role = role;
      this.logged = true;
    },
    clearSession() {
      setToken("");
      this.token = this.account = this.name = this.role = "";
      this.logged = false;
    },
    async login(account, password) {
      const result = await authApi.login(account, password);
      this.startSession(result.access_token, account, result.role);
      return result;
    },
    async logout() {
      try {
        await authApi.logout();
      } catch {
        /* Clear the local session if the server is unavailable. */
      } finally {
        this.clearSession();
      }
    },
    restore() {
      const token = getToken();
      if (!token) return;
      try {
        const encoded = token
          .split(".")[1]
          .replaceAll("-", "+")
          .replaceAll("_", "/");
        const claims = JSON.parse(
          new TextDecoder().decode(
            Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0)),
          ),
        );
        if (
          !claims.sub ||
          !roleLabels[claims.role] ||
          !(claims.exp * 1000 > Date.now())
        ) {
          this.clearSession();
          return;
        }
        this.startSession(token, claims.sub, claims.role);
      } catch {
        this.clearSession();
      }
    },
    toast(message, type = "") {
      const id = ++this.toastSequence;
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter((toast) => toast.id !== id);
      }, 3400);
    },
    setupUnauthorized(router) {
      setUnauthorizedHandler(() => {
        this.clearSession();
        router.replace({
          name: "login",
          query: { redirect: router.currentRoute.value.fullPath },
        });
      });
    },
  },
});
