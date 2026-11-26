const API_ROOT = "/api/v1";
const TOKEN_KEY = "mdm_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY) ?? "";

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

let onUnauthorized;
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const errorMessage = (error) => error?.message || "操作失败";

async function request(
  method,
  path,
  { params, body, form, download = false, login = false } = {},
) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value != null && value !== "") query.set(key, String(value));
  }
  const url = API_ROOT + path + (query.size ? "?" + query : "");
  const headers = new Headers();
  if (login) headers.set("Content-Type", "application/x-www-form-urlencoded");
  else if (body !== undefined) headers.set("Content-Type", "application/json");
  const token = getToken();
  if (!login && token) headers.set("Authorization", "Bearer " + token);

  const response = await fetch(url, {
    method,
    headers,
    body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
  });
  if (
    download &&
    response.ok &&
    !response.headers.get("Content-Type")?.includes("json")
  ) {
    return { resp: response };
  }
  const payload = await response.json().catch(() => null);
  if (!login && (response.status === 401 || payload?.code === 2001))
    onUnauthorized?.();
  if (!response.ok || (payload?.code !== undefined && payload.code !== 0)) {
    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : payload?.detail?.[0]?.msg;
    throw new ApiError(
      payload?.message || detail || "请求失败",
      response.status,
      payload?.code,
    );
  }
  if (download || payload === null)
    throw new ApiError("服务返回了无法识别的响应", response.status);
  return "code" in payload ? payload.data : payload;
}

const get = (path, params) => request("GET", path, { params });
const post = (path, body) => request("POST", path, { body });
const put = (path, body) => request("PUT", path, { body });
const goodsPath = (barcode) => "/goods/" + encodeURIComponent(barcode);
const categoryPath = (id) => "/categories/" + encodeURIComponent(id);
const userPath = (account) => "/admin/users/" + encodeURIComponent(account);

export const authApi = {
  login: (username, password) =>
    request("POST", "/auth/token", {
      login: true,
      form: new URLSearchParams({ username, password }),
    }),
  logout: () => post("/auth/logout"),
};

export const goodsApi = {
  list: (params) => get("/goods", params),
  detail: (barcode) => get(goodsPath(barcode)),
  check: (barcode, goods_name) => post("/goods/check", { barcode, goods_name }),
  create: (body) => post("/goods", body),
  patch(barcode, field, new_value, reason, version) {
    if (!Number.isInteger(version) || version < 1)
      throw new Error("商品版本已失效，请刷新后重试");
    return request("PATCH", goodsPath(barcode), {
      body: { field, new_value, reason, version },
    });
  },
  changeCategory: (barcode, category_id, reason) =>
    post(goodsPath(barcode) + "/category", { category_id, reason }),
  changeStatus: (barcode, to_status, reason) =>
    post(goodsPath(barcode) + "/status", { to_status, reason }),
  getAttrs: (barcode) => get(goodsPath(barcode) + "/attrs"),
  putAttrs: (barcode, attrs) => put(goodsPath(barcode) + "/attrs", { attrs }),
  importCsv(file) {
    const form = new FormData();
    form.append("file", file);
    return request("POST", "/goods/import", { form });
  },
  export: (params) =>
    request("GET", "/goods/export", { params, download: true }),
};

export const categoryApi = {
  tree: () => get("/categories/tree"),
  update: (id, body) => put(categoryPath(id), body),
  impact: (id) => post(categoryPath(id) + "/impact"),
  getTemplate: (id) => get(categoryPath(id) + "/template"),
  putTemplate: (id, template) =>
    put(categoryPath(id) + "/template", { template }),
  getExternalMap: (id) => get(categoryPath(id) + "/external-map"),
  putExternalMap: (id, mappings) =>
    put(categoryPath(id) + "/external-map", { mappings }),
};

export const barcodeApi = {
  validate: (barcode) => post("/barcodes/validate", { barcode }),
  alias: (alias_barcode, master_barcode, alias_type) =>
    post("/barcodes/alias", { alias_barcode, master_barcode, alias_type }),
  reassign: (old_barcode, new_barcode, reason) =>
    post("/barcodes/reassign", { old_barcode, new_barcode, reason }),
};

export const adminApi = {
  dashboard: () => get("/admin/dashboard"),
  changeLog: (params) => get("/admin/change-log", params),
  units: () => get("/admin/units"),
  createUnit: (body) => post("/admin/units", body),
  updateUnit: (code, body) =>
    put("/admin/units/" + encodeURIComponent(code), body),
  sources: () => get("/admin/sources"),
  quarantine: (params) => get("/admin/quarantine", params),
  quarantineExport: (params) =>
    request("GET", "/admin/quarantine/export", { params, download: true }),
  users: (params) => get("/admin/users", params),
  createUser: (body) => post("/admin/users", body),
  updateUser: (account, body) => put(userPath(account), body),
  userActivity: (account) => get(userPath(account) + "/activity"),
  resetPassword: (account) => post(userPath(account) + "/reset-password"),
  importJob: (id) => get("/admin/import-jobs/" + encodeURIComponent(id)),
};
