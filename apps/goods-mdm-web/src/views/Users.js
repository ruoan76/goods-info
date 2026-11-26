import DOMPurify from "dompurify";
import {
  useAppStore,
  roleColors,
  roleClasses,
  roleLabels,
  rolePermissions,
} from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  toDisplayString,
  createTextVNode,
  unref,
  createCommentVNode,
  withDirectives,
  vModelText,
  vModelSelect,
  Fragment,
  renderList,
  normalizeClass,
  normalizeStyle,
  withModifiers,
  createStaticVNode,
  createVNode,
  withCtx,
  computed,
  ref,
} from "vue";
import { adminApi, errorMessage } from "../api.js";
import ConfirmDlg from "../components/ConfirmDlg.js";
import InfoBox from "../components/InfoBox.js";

const rt = {
    class: "stat-row",
  },
  ut = {
    class: "stat",
  },
  vt = {
    class: "n",
  },
  ct = {
    class: "stat",
  },
  pt = {
    class: "n",
    style: {
      color: "var(--success)",
    },
  },
  mt = {
    class: "stat",
  },
  ft = {
    class: "n",
    style: {
      color: "var(--warning)",
    },
  },
  yt = {
    class: "stat",
  },
  gt = {
    class: "n",
    style: {
      color: "var(--danger)",
    },
  },
  wt = {
    class: "card",
  },
  kt = {
    class: "filter-row",
  },
  Ct = {
    style: {
      "font-size": "12px",
      color: "var(--text3)",
    },
  },
  xt = ["onClick"],
  Vt = {
    style: {
      "font-family": "Menlo",
    },
  },
  _t = {
    class: "role-cell",
  },
  bt = ["onClick"],
  ht = ["onClick"],
  At = {
    key: 0,
  },
  Et = {
    key: 0,
    class: "drawer-wrap",
  },
  It = {
    class: "drawer",
  },
  Tt = {
    class: "drawer-hd",
  },
  $t = {
    class: "t",
  },
  Mt = {
    class: "s",
  },
  Ut = {
    key: 0,
    class: "drawer-bd",
  },
  Nt = {
    class: "dsec",
  },
  St = {
    class: "drow",
  },
  Ot = {
    class: "v",
    style: {
      "font-family": "Menlo",
    },
  },
  Lt = {
    class: "drow",
  },
  zt = {
    class: "v",
  },
  Rt = {
    class: "drow",
  },
  Dt = {
    class: "v",
  },
  Ft = {
    class: "drow",
  },
  Bt = {
    class: "v",
  },
  Gt = {
    class: "drow",
  },
  Ht = {
    class: "v",
  },
  Pt = {
    class: "drow",
  },
  jt = {
    class: "v",
  },
  qt = {
    class: "dsec",
  },
  Jt = {
    class: "dsec",
  },
  Kt = {
    class: "k",
    style: {
      width: "110px",
    },
  },
  Qt = {
    class: "v",
  },
  Wt = {
    key: 0,
    style: {
      color: "var(--text3)",
      "font-size": "12px",
    },
  },
  Xt = {
    key: 1,
    class: "drawer-ft",
  },
  Yt = {
    class: "uf-box",
  },
  Zt = {
    class: "hd",
  },
  ts = {
    class: "bd",
  },
  ss = {
    class: "field",
  },
  ls = ["disabled"],
  es = {
    class: "hint",
  },
  as = {
    class: "grid2",
  },
  ns = {
    class: "field",
  },
  os = {
    class: "field",
  },
  is = {
    class: "grid2",
  },
  ds = {
    class: "field",
  },
  rs = {
    class: "field",
  },
  us = {
    class: "field",
  },
  vs = {
    class: "tip-note",
    style: {
      margin: "4px 0 0",
    },
  },
  cs = {
    class: "ft",
  },
  ps = ["innerHTML"],
  Users = {
    name: "Users",
    setup(ms) {
      const r = useAppStore(),
        f = ref([]),
        x = ref(""),
        A = ref(""),
        E = ref(""),
        N = ref(!1),
        o = ref(null),
        I = ref([]),
        g = ref(!1),
        p = ref(null),
        n = ref({
          account: "",
          name: "",
          role: "Operator",
          dept: "",
          phone: "",
          status: "ACTIVE",
        }),
        y = ref({
          show: !1,
          title: "",
          message: "",
          action: null,
        }),
        V = ref({
          show: !1,
          title: "",
          html: "",
        }),
        S = computed(() =>
          f.value.filter(
            (e) =>
              (!x.value ||
                e.account.includes(x.value) ||
                (e.name || "").includes(x.value)) &&
              (!A.value || e.role === A.value) &&
              (!E.value || e.status === E.value),
          ),
        ),
        T = computed(() => ({
          all: f.value.length,
          on: f.value.filter((e) => e.status === "ACTIVE").length,
          adm: f.value.filter(
            (e) => e.role === "Steward" && e.status === "ACTIVE",
          ).length,
          off: f.value.filter((e) => e.status !== "ACTIVE").length,
        }));
      function W(e, s) {
        V.value = {
          show: !0,
          title: e,
          html: s,
        };
      }
      function B(e, s, w) {
        y.value = {
          show: !0,
          title: e,
          message: s,
          action: w,
        };
      }
      function X() {
        const e = y.value.action;
        y.value.show = !1;
        typeof e == "function" && e();
      }
      async function O() {
        try {
          f.value = (await adminApi.users()).items || [];
        } catch (e) {
          r.toast(errorMessage(e), "err");
        }
      }
      async function G(e) {
        o.value = e;
        N.value = !0;
        try {
          const s = await adminApi.userActivity(e.account);
          I.value = Array.isArray(s) ? s : s.items || [];
        } catch {
          I.value = [];
        }
      }
      function $() {
        N.value = !1;
        o.value = null;
      }
      function L(e) {
        if (!r.isAdmin) {
          r.toast("仅管理员可管理用户", "err");
          return;
        }
        p.value = (e == null ? void 0 : e.account) || null;
        n.value = e
          ? {
              account: e.account,
              name: e.name || "",
              role: e.role,
              dept: e.dept || "",
              phone: e.phone || "",
              status: e.status,
            }
          : {
              account: "",
              name: "",
              role: "Operator",
              dept: "",
              phone: "",
              status: "ACTIVE",
            };
        g.value = !0;
      }
      async function Y() {
        if (!n.value.account || !n.value.name) {
          r.toast("账号和姓名是必填项", "err");
          return;
        }
        try {
          const { account, name, role, dept, phone, status } = n.value;
          const fields = {
            name,
            role,
            dept: dept || null,
            phone: phone || null,
          };
          if (p.value) {
            await adminApi.updateUser(p.value, { ...fields, status });
            r.toast("已保存账号修改", "ok");
          } else {
            const result = await adminApi.createUser({ account, ...fields });
            W("已创建账号", passwordResult(result.initial_password));
          }
          g.value = !1;
          O();
        } catch (e) {
          r.toast(errorMessage(e), "err");
        }
      }
      function H(e) {
        const s = e.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
        B(
          s === "INACTIVE"
            ? `停用「${e.name}」的账号？`
            : `恢复「${e.name}」的使用？`,
          s === "INACTIVE"
            ? "停用后该账号立即不能登录，历史操作记录全部保留，可随时恢复。"
            : "恢复后该账号可以正常登录，权限不变。",
          async () => {
            try {
              await adminApi.updateUser(e.account, {
                status: s,
              });
              r.toast(
                `已${s === "INACTIVE" ? "停用" : "恢复"}「${e.name}」`,
                "ok",
              );
              $();
              O();
            } catch (w) {
              r.toast(errorMessage(w), "err");
            }
          },
        );
      }
      function passwordResult(password) {
        const node = document.createElement("code");
        node.textContent = password;
        return "<p>请通过安全渠道交付新密码。</p>" + node.outerHTML;
      }

      function Z(e) {
        B(
          `重置「${e.name}」的密码？`,
          "系统将生成一个新密码，原密码和已签发的令牌立即失效。",
          async () => {
            try {
              const s = await adminApi.resetPassword(e.account);
              W("密码已重置", passwordResult(s.initial_password));
            } catch (s) {
              r.toast(errorMessage(s), "err");
            }
          },
        );
      }
      return (
        onMounted(O),
        (e, s) => {
          var w, P, j, q;
          return (
            openBlock(),
            createElementBlock("div", null, [
              s[49] ||
                (s[49] = createElementVNode(
                  "div",
                  {
                    class: "page-title",
                  },
                  "用户管理",
                  -1,
                )),
              s[50] ||
                (s[50] = createElementVNode(
                  "div",
                  {
                    class: "page-desc",
                  },
                  "管理谁能登录、能做什么 · 点一行看详情，改动全部留痕",
                  -1,
                )),
              createElementVNode("div", rt, [
                createElementVNode("div", ut, [
                  createElementVNode(
                    "div",
                    vt,
                    toDisplayString(T.value.all),
                    1,
                  ),
                  s[19] ||
                    (s[19] = createElementVNode(
                      "div",
                      {
                        class: "l",
                      },
                      "全部账号",
                      -1,
                    )),
                  s[20] ||
                    (s[20] = createElementVNode(
                      "div",
                      {
                        class: "mini",
                      },
                      "系统账号总数",
                      -1,
                    )),
                ]),
                createElementVNode("div", ct, [
                  createElementVNode("div", pt, toDisplayString(T.value.on), 1),
                  s[21] ||
                    (s[21] = createElementVNode(
                      "div",
                      {
                        class: "l",
                      },
                      "正常使用",
                      -1,
                    )),
                  s[22] ||
                    (s[22] = createElementVNode(
                      "div",
                      {
                        class: "mini",
                      },
                      "可登录系统",
                      -1,
                    )),
                ]),
                createElementVNode("div", mt, [
                  createElementVNode(
                    "div",
                    ft,
                    toDisplayString(T.value.adm),
                    1,
                  ),
                  s[23] ||
                    (s[23] = createElementVNode(
                      "div",
                      {
                        class: "l",
                      },
                      "管理员",
                      -1,
                    )),
                  s[24] ||
                    (s[24] = createElementVNode(
                      "div",
                      {
                        class: "mini",
                      },
                      "拥有全部权限",
                      -1,
                    )),
                ]),
                createElementVNode("div", yt, [
                  createElementVNode(
                    "div",
                    gt,
                    toDisplayString(T.value.off),
                    1,
                  ),
                  s[25] ||
                    (s[25] = createElementVNode(
                      "div",
                      {
                        class: "l",
                      },
                      "已停用",
                      -1,
                    )),
                  s[26] ||
                    (s[26] = createElementVNode(
                      "div",
                      {
                        class: "mini",
                      },
                      "不能登录 · 可随时恢复",
                      -1,
                    )),
                ]),
              ]),
              createElementVNode("div", wt, [
                createElementVNode("h3", null, [
                  s[27] || (s[27] = createTextVNode("用户列表 ", -1)),
                  unref(r).isAdmin
                    ? (openBlock(),
                      createElementBlock(
                        "button",
                        {
                          key: 0,
                          class: "btn sm",
                          style: {
                            float: "right",
                          },
                          onClick: s[0] || (s[0] = (l) => L(null)),
                        },
                        "+ 新增用户",
                      ))
                    : createCommentVNode("", !0),
                ]),
                createElementVNode("div", kt, [
                  withDirectives(
                    createElementVNode(
                      "input",
                      {
                        "onUpdate:modelValue":
                          s[1] || (s[1] = (l) => (x.value = l)),
                        placeholder: "账号或姓名，输入即筛选",
                      },
                      null,
                      512,
                    ),
                    [[vModelText, x.value]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "select",
                      {
                        "onUpdate:modelValue":
                          s[2] || (s[2] = (l) => (A.value = l)),
                      },
                      [
                        ...(s[28] ||
                          (s[28] = [
                            createElementVNode(
                              "option",
                              {
                                value: "",
                              },
                              "全部角色",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "Operator",
                              },
                              "录入员",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "Steward",
                              },
                              "管理员",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "Viewer",
                              },
                              "只读",
                              -1,
                            ),
                          ])),
                      ],
                      512,
                    ),
                    [[vModelSelect, A.value]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "select",
                      {
                        "onUpdate:modelValue":
                          s[3] || (s[3] = (l) => (E.value = l)),
                      },
                      [
                        ...(s[29] ||
                          (s[29] = [
                            createElementVNode(
                              "option",
                              {
                                value: "",
                              },
                              "全部状态",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "ACTIVE",
                              },
                              "启用",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "INACTIVE",
                              },
                              "停用",
                              -1,
                            ),
                          ])),
                      ],
                      512,
                    ),
                    [[vModelSelect, E.value]],
                  ),
                  createElementVNode(
                    "span",
                    Ct,
                    "显示 " +
                      toDisplayString(S.value.length) +
                      " / " +
                      toDisplayString(f.value.length) +
                      " 人",
                    1,
                  ),
                ]),
                createElementVNode("table", null, [
                  s[31] ||
                    (s[31] = createElementVNode(
                      "thead",
                      null,
                      [
                        createElementVNode("tr", null, [
                          createElementVNode("th", null, "账号"),
                          createElementVNode("th", null, "姓名"),
                          createElementVNode("th", null, "角色"),
                          createElementVNode("th", null, "状态"),
                          createElementVNode("th", null, "最近登录"),
                          createElementVNode("th", null, "操作"),
                        ]),
                      ],
                      -1,
                    )),
                  createElementVNode("tbody", null, [
                    (openBlock(!0),
                    createElementBlock(
                      Fragment,
                      null,
                      renderList(
                        S.value,
                        (l) => (
                          openBlock(),
                          createElementBlock(
                            "tr",
                            {
                              key: l.account,
                              class: normalizeClass({
                                "row-disabled": l.status !== "ACTIVE",
                              }),
                              onClick: (k) => G(l),
                            },
                            [
                              createElementVNode(
                                "td",
                                Vt,
                                toDisplayString(l.account),
                                1,
                              ),
                              createElementVNode(
                                "td",
                                null,
                                toDisplayString(l.name || "—"),
                                1,
                              ),
                              createElementVNode("td", null, [
                                createElementVNode("div", _t, [
                                  createElementVNode(
                                    "span",
                                    {
                                      class: "role-dot",
                                      style: normalizeStyle({
                                        background: unref(roleColors)[l.role],
                                      }),
                                    },
                                    null,
                                    4,
                                  ),
                                  createElementVNode(
                                    "span",
                                    {
                                      class: normalizeClass([
                                        "tag",
                                        unref(roleClasses)[l.role],
                                      ]),
                                    },
                                    toDisplayString(
                                      unref(roleLabels)[l.role] || l.role,
                                    ),
                                    3,
                                  ),
                                ]),
                              ]),
                              createElementVNode("td", null, [
                                createElementVNode(
                                  "span",
                                  {
                                    class: normalizeClass([
                                      "tag",
                                      l.status === "ACTIVE"
                                        ? "tg-green"
                                        : "tg-gray",
                                    ]),
                                  },
                                  toDisplayString(
                                    l.status === "ACTIVE" ? "启用" : "停用",
                                  ),
                                  3,
                                ),
                              ]),
                              createElementVNode(
                                "td",
                                null,
                                toDisplayString(l.last_login || "从未登录"),
                                1,
                              ),
                              createElementVNode("td", null, [
                                createElementVNode(
                                  "span",
                                  {
                                    class: "op",
                                    onClick: withModifiers(
                                      (k) => G(l),
                                      ["stop"],
                                    ),
                                  },
                                  "查看",
                                  8,
                                  bt,
                                ),
                                unref(r).isAdmin
                                  ? (openBlock(),
                                    createElementBlock(
                                      "span",
                                      {
                                        key: 0,
                                        class: "op",
                                        onClick: withModifiers(
                                          (k) => L(l),
                                          ["stop"],
                                        ),
                                      },
                                      "编辑",
                                      8,
                                      ht,
                                    ))
                                  : createCommentVNode("", !0),
                              ]),
                            ],
                            10,
                            xt,
                          )
                        ),
                      ),
                      128,
                    )),
                    S.value.length
                      ? createCommentVNode("", !0)
                      : (openBlock(),
                        createElementBlock("tr", At, [
                          ...(s[30] ||
                            (s[30] = [
                              createElementVNode(
                                "td",
                                {
                                  colspan: "6",
                                  style: {
                                    "text-align": "center",
                                    color: "var(--text3)",
                                    padding: "30px",
                                  },
                                },
                                "没有符合条件的用户，换个条件试试",
                                -1,
                              ),
                            ])),
                        ])),
                  ]),
                ]),
                s[32] ||
                  (s[32] = createElementVNode(
                    "div",
                    {
                      class: "tip-note",
                      style: {
                        margin: "12px 0 0",
                      },
                    },
                    "点任意一行可查看用户详情、登录记录与完整权限；停用账号后立即不能登录，历史操作记录全部保留",
                    -1,
                  )),
              ]),
              s[51] ||
                (s[51] = createStaticVNode(
                  '<div class="card"><h3>角色权限一览</h3><table><thead><tr><th>能做的事</th><th style="text-align:center;">录入员</th><th style="text-align:center;">管理员</th><th style="text-align:center;">只读</th></tr></thead><tbody><tr><td>查看商品、按分类浏览、按条码/名称查询</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--success);">✓</td></tr><tr><td>新增商品、修改名称/价格/属性</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--text3);">—</td></tr><tr><td>停用 / 作废商品</td><td style="text-align:center;color:var(--text3);">—</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--text3);">—</td></tr><tr><td>分类、属性模板、条码、字典、用户管理</td><td style="text-align:center;color:var(--text3);">—</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--text3);">—</td></tr><tr><td>导出数据</td><td style="text-align:center;color:var(--text3);">—</td><td style="text-align:center;color:var(--success);">✓</td><td style="text-align:center;color:var(--success);">✓</td></tr></tbody></table></div>',
                  1,
                )),
              N.value
                ? (openBlock(),
                  createElementBlock("div", Et, [
                    createElementVNode("div", {
                      class: "drawer-mask",
                      onClick: $,
                    }),
                    createElementVNode("div", It, [
                      createElementVNode("div", Tt, [
                        createElementVNode("div", null, [
                          createElementVNode(
                            "div",
                            $t,
                            toDisplayString(
                              (w = o.value) == null ? void 0 : w.name,
                            ),
                            1,
                          ),
                          createElementVNode(
                            "div",
                            Mt,
                            "账号 " +
                              toDisplayString(
                                (P = o.value) == null ? void 0 : P.account,
                              ) +
                              " · " +
                              toDisplayString(
                                ((j = o.value) == null ? void 0 : j.dept) ||
                                  "未设部门",
                              ),
                            1,
                          ),
                        ]),
                        createElementVNode(
                          "span",
                          {
                            class: "x",
                            onClick: $,
                          },
                          "✕",
                        ),
                      ]),
                      o.value
                        ? (openBlock(),
                          createElementBlock("div", Ut, [
                            createElementVNode("div", Nt, [
                              s[39] ||
                                (s[39] = createElementVNode(
                                  "h4",
                                  null,
                                  "基本信息",
                                  -1,
                                )),
                              createElementVNode("div", St, [
                                s[33] ||
                                  (s[33] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "账号",
                                    -1,
                                  )),
                                createElementVNode(
                                  "span",
                                  Ot,
                                  toDisplayString(o.value.account),
                                  1,
                                ),
                              ]),
                              createElementVNode("div", Lt, [
                                s[34] ||
                                  (s[34] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "姓名",
                                    -1,
                                  )),
                                createElementVNode(
                                  "span",
                                  zt,
                                  toDisplayString(o.value.name),
                                  1,
                                ),
                              ]),
                              createElementVNode("div", Rt, [
                                s[35] ||
                                  (s[35] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "角色",
                                    -1,
                                  )),
                                createElementVNode("span", Dt, [
                                  createElementVNode(
                                    "span",
                                    {
                                      class: normalizeClass([
                                        "tag",
                                        unref(roleClasses)[o.value.role],
                                      ]),
                                    },
                                    toDisplayString(
                                      unref(roleLabels)[o.value.role],
                                    ),
                                    3,
                                  ),
                                ]),
                              ]),
                              createElementVNode("div", Ft, [
                                s[36] ||
                                  (s[36] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "状态",
                                    -1,
                                  )),
                                createElementVNode("span", Bt, [
                                  createElementVNode(
                                    "span",
                                    {
                                      class: normalizeClass([
                                        "tag",
                                        o.value.status === "ACTIVE"
                                          ? "tg-green"
                                          : "tg-gray",
                                      ]),
                                    },
                                    toDisplayString(
                                      o.value.status === "ACTIVE"
                                        ? "启用"
                                        : "停用",
                                    ),
                                    3,
                                  ),
                                ]),
                              ]),
                              createElementVNode("div", Gt, [
                                s[37] ||
                                  (s[37] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "手机号",
                                    -1,
                                  )),
                                createElementVNode(
                                  "span",
                                  Ht,
                                  toDisplayString(o.value.phone || "—"),
                                  1,
                                ),
                              ]),
                              createElementVNode("div", Pt, [
                                s[38] ||
                                  (s[38] = createElementVNode(
                                    "span",
                                    {
                                      class: "k",
                                    },
                                    "最近登录",
                                    -1,
                                  )),
                                createElementVNode(
                                  "span",
                                  jt,
                                  toDisplayString(
                                    o.value.last_login || "从未登录",
                                  ),
                                  1,
                                ),
                              ]),
                            ]),
                            createElementVNode("div", qt, [
                              createElementVNode(
                                "h4",
                                null,
                                "权限（" +
                                  toDisplayString(
                                    unref(roleLabels)[o.value.role],
                                  ) +
                                  "）",
                                1,
                              ),
                              (openBlock(!0),
                              createElementBlock(
                                Fragment,
                                null,
                                renderList(
                                  unref(rolePermissions)[o.value.role] || [],
                                  (l, k) => (
                                    openBlock(),
                                    createElementBlock(
                                      "div",
                                      {
                                        class: "pline",
                                        key: k,
                                      },
                                      [
                                        s[40] ||
                                          (s[40] = createElementVNode(
                                            "span",
                                            {
                                              class: "pyes",
                                            },
                                            "✓",
                                            -1,
                                          )),
                                        createTextVNode(toDisplayString(l), 1),
                                      ],
                                    )
                                  ),
                                ),
                                128,
                              )),
                            ]),
                            createElementVNode("div", Jt, [
                              createElementVNode(
                                "h4",
                                null,
                                "最近活动 · GET /admin/users/" +
                                  toDisplayString(o.value.account) +
                                  "/activity",
                                1,
                              ),
                              (openBlock(!0),
                              createElementBlock(
                                Fragment,
                                null,
                                renderList(
                                  I.value,
                                  (l, k) => (
                                    openBlock(),
                                    createElementBlock(
                                      "div",
                                      {
                                        class: "drow",
                                        key: k,
                                      },
                                      [
                                        createElementVNode(
                                          "span",
                                          Kt,
                                          toDisplayString(
                                            l.at || l.created_at || "",
                                          ),
                                          1,
                                        ),
                                        createElementVNode(
                                          "span",
                                          Qt,
                                          toDisplayString(
                                            l.action || l.detail || "—",
                                          ),
                                          1,
                                        ),
                                      ],
                                    )
                                  ),
                                ),
                                128,
                              )),
                              I.value.length
                                ? createCommentVNode("", !0)
                                : (openBlock(),
                                  createElementBlock(
                                    "div",
                                    Wt,
                                    "暂无活动记录",
                                  )),
                            ]),
                          ]))
                        : createCommentVNode("", !0),
                      unref(r).isAdmin
                        ? (openBlock(),
                          createElementBlock("div", Xt, [
                            createElementVNode(
                              "button",
                              {
                                class: "btn plain sm",
                                onClick: s[4] || (s[4] = (l) => Z(o.value)),
                              },
                              "重置密码",
                            ),
                            createElementVNode(
                              "button",
                              {
                                class: "btn plain sm",
                                onClick:
                                  s[5] ||
                                  (s[5] = (l) => {
                                    $();
                                    L(o.value);
                                  }),
                              },
                              "编辑资料",
                            ),
                            ((q = o.value) == null ? void 0 : q.status) ===
                            "ACTIVE"
                              ? (openBlock(),
                                createElementBlock(
                                  "button",
                                  {
                                    key: 0,
                                    class: "btn warn sm",
                                    onClick: s[6] || (s[6] = (l) => H(o.value)),
                                  },
                                  "停用账号",
                                ))
                              : (openBlock(),
                                createElementBlock(
                                  "button",
                                  {
                                    key: 1,
                                    class: "btn sm",
                                    onClick: s[7] || (s[7] = (l) => H(o.value)),
                                  },
                                  "恢复使用",
                                )),
                          ]))
                        : createCommentVNode("", !0),
                    ]),
                  ]))
                : createCommentVNode("", !0),
              g.value
                ? (openBlock(),
                  createElementBlock(
                    "div",
                    {
                      key: 1,
                      class: "mask",
                      onClick:
                        s[16] ||
                        (s[16] = withModifiers(
                          (l) => (g.value = !1),
                          ["self"],
                        )),
                    },
                    [
                      createElementVNode("div", Yt, [
                        createElementVNode("div", Zt, [
                          createElementVNode(
                            "span",
                            null,
                            toDisplayString(
                              p.value ? "编辑用户 · " + p.value : "新增用户",
                            ),
                            1,
                          ),
                          createElementVNode(
                            "span",
                            {
                              class: "x",
                              onClick: s[8] || (s[8] = (l) => (g.value = !1)),
                            },
                            "✕",
                          ),
                        ]),
                        createElementVNode("div", ts, [
                          createElementVNode("div", ss, [
                            s[41] ||
                              (s[41] = createElementVNode(
                                "label",
                                null,
                                [
                                  createTextVNode("账号 "),
                                  createElementVNode(
                                    "span",
                                    {
                                      style: {
                                        color: "var(--danger)",
                                      },
                                    },
                                    "*",
                                  ),
                                ],
                                -1,
                              )),
                            withDirectives(
                              createElementVNode(
                                "input",
                                {
                                  "onUpdate:modelValue":
                                    s[9] ||
                                    (s[9] = (l) => (n.value.account = l)),
                                  disabled: !!p.value,
                                  placeholder: "如 zhang.san",
                                },
                                null,
                                8,
                                ls,
                              ),
                              [[vModelText, n.value.account]],
                            ),
                            createElementVNode(
                              "div",
                              es,
                              toDisplayString(
                                p.value
                                  ? "账号创建后不能修改"
                                  : "用姓名拼音，全系统唯一",
                              ),
                              1,
                            ),
                          ]),
                          createElementVNode("div", as, [
                            createElementVNode("div", ns, [
                              s[42] ||
                                (s[42] = createElementVNode(
                                  "label",
                                  null,
                                  [
                                    createTextVNode("姓名 "),
                                    createElementVNode(
                                      "span",
                                      {
                                        style: {
                                          color: "var(--danger)",
                                        },
                                      },
                                      "*",
                                    ),
                                  ],
                                  -1,
                                )),
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    "onUpdate:modelValue":
                                      s[10] ||
                                      (s[10] = (l) => (n.value.name = l)),
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, n.value.name]],
                              ),
                            ]),
                            createElementVNode("div", os, [
                              s[44] ||
                                (s[44] = createElementVNode(
                                  "label",
                                  null,
                                  [
                                    createTextVNode("角色 "),
                                    createElementVNode(
                                      "span",
                                      {
                                        style: {
                                          color: "var(--danger)",
                                        },
                                      },
                                      "*",
                                    ),
                                  ],
                                  -1,
                                )),
                              withDirectives(
                                createElementVNode(
                                  "select",
                                  {
                                    "onUpdate:modelValue":
                                      s[11] ||
                                      (s[11] = (l) => (n.value.role = l)),
                                  },
                                  [
                                    ...(s[43] ||
                                      (s[43] = [
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "Operator",
                                          },
                                          "录入员",
                                          -1,
                                        ),
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "Steward",
                                          },
                                          "管理员",
                                          -1,
                                        ),
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "Viewer",
                                          },
                                          "只读",
                                          -1,
                                        ),
                                      ])),
                                  ],
                                  512,
                                ),
                                [[vModelSelect, n.value.role]],
                              ),
                            ]),
                          ]),
                          createElementVNode("div", is, [
                            createElementVNode("div", ds, [
                              s[45] ||
                                (s[45] = createElementVNode(
                                  "label",
                                  null,
                                  "所属部门",
                                  -1,
                                )),
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    "onUpdate:modelValue":
                                      s[12] ||
                                      (s[12] = (l) => (n.value.dept = l)),
                                    placeholder: "如 商品部",
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, n.value.dept]],
                              ),
                            ]),
                            createElementVNode("div", rs, [
                              s[46] ||
                                (s[46] = createElementVNode(
                                  "label",
                                  null,
                                  "手机号",
                                  -1,
                                )),
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    "onUpdate:modelValue":
                                      s[13] ||
                                      (s[13] = (l) => (n.value.phone = l)),
                                    placeholder: "选填",
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, n.value.phone]],
                              ),
                            ]),
                          ]),
                          createElementVNode("div", us, [
                            s[48] ||
                              (s[48] = createElementVNode(
                                "label",
                                null,
                                "状态",
                                -1,
                              )),
                            withDirectives(
                              createElementVNode(
                                "select",
                                {
                                  "onUpdate:modelValue":
                                    s[14] ||
                                    (s[14] = (l) => (n.value.status = l)),
                                },
                                [
                                  ...(s[47] ||
                                    (s[47] = [
                                      createElementVNode(
                                        "option",
                                        {
                                          value: "ACTIVE",
                                        },
                                        "启用",
                                        -1,
                                      ),
                                      createElementVNode(
                                        "option",
                                        {
                                          value: "INACTIVE",
                                        },
                                        "停用",
                                        -1,
                                      ),
                                    ])),
                                ],
                                512,
                              ),
                              [[vModelSelect, n.value.status]],
                            ),
                          ]),
                          createElementVNode(
                            "div",
                            vs,
                            toDisplayString(
                              p.value
                                ? "修改角色立即生效；改动记录到系统操作日志"
                                : "系统生成并显示初始密码，账号创建会记录到日志",
                            ),
                            1,
                          ),
                        ]),
                        createElementVNode("div", cs, [
                          createElementVNode(
                            "button",
                            {
                              class: "btn plain sm",
                              onClick: s[15] || (s[15] = (l) => (g.value = !1)),
                            },
                            "取消",
                          ),
                          createElementVNode(
                            "button",
                            {
                              class: "btn sm",
                              onClick: Y,
                            },
                            "保存",
                          ),
                        ]),
                      ]),
                    ],
                  ))
                : createCommentVNode("", !0),
              createVNode(
                ConfirmDlg,
                {
                  show: y.value.show,
                  title: y.value.title,
                  message: y.value.message,
                  onConfirm: X,
                  onCancel: s[17] || (s[17] = (l) => (y.value.show = !1)),
                },
                null,
                8,
                ["show", "title", "message"],
              ),
              createVNode(
                InfoBox,
                {
                  show: V.value.show,
                  title: V.value.title,
                  onClose: s[18] || (s[18] = (l) => (V.value.show = !1)),
                },
                {
                  default: withCtx(() => [
                    createElementVNode(
                      "div",
                      {
                        innerHTML: DOMPurify.sanitize(V.value.html),
                      },
                      null,
                      8,
                      ps,
                    ),
                  ]),
                  _: 1,
                },
                8,
                ["show", "title"],
              ),
            ])
          );
        }
      );
    },
  };

export default Users;
