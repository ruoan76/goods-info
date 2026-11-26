import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  Fragment,
  renderList,
  normalizeClass,
  withModifiers,
  toDisplayString,
  createTextVNode,
  createCommentVNode,
  createVNode,
  withCtx,
  ref,
  computed,
} from "vue";
import { categoryApi, errorMessage } from "../api.js";
import InfoBox from "../components/InfoBox.js";

const J = {
    class: "tree-layout",
  },
  q = {
    class: "card",
    style: {
      margin: "0",
    },
  },
  K = {
    class: "tree",
  },
  Q = ["onClick"],
  R = ["onClick"],
  W = {
    key: 1,
    class: "caret",
  },
  X = {
    class: "cnt",
  },
  Y = {
    key: 0,
    class: "children",
  },
  Z = ["onClick"],
  ee = {
    class: "cnt",
  },
  te = {
    key: 0,
  },
  se = {
    class: "card",
  },
  ae = {
    class: "kv",
  },
  le = {
    key: 0,
    class: "tip-note warn",
  },
  ne = ["innerHTML"],
  Category = {
    name: "Category",
    setup(oe) {
      const u = useAppStore(),
        y = ref([]),
        g = ref(new Set(["C01", "C02"])),
        a = ref(null),
        b = ref(null),
        m = ref(null),
        C = ref(null),
        v = ref({
          show: !1,
          title: "",
          html: "",
        }),
        r = (e) => (e ?? 0).toLocaleString("en-US"),
        x = computed(() => {
          const e = [],
            t = (l) =>
              l.forEach((p) => {
                e.push(p);
                t(p.children || []);
              });
          return (t(y.value), e);
        }),
        V = (e) => {
          const t = x.value.find((l) => l.category_id === e.parent_id);
          return t ? t.name + " → " + e.name : e.name;
        };
      function h(e, t) {
        v.value = {
          show: !0,
          title: e,
          html: t,
        };
      }
      async function L() {
        try {
          y.value = (await categoryApi.tree()).tree || [];
        } catch (e) {
          u.toast(errorMessage(e), "err");
        }
      }
      async function f(e) {
        a.value = e;
        try {
          const [t, l] = await Promise.all([
            categoryApi.impact(e.category_id),
            categoryApi.getExternalMap(e.category_id),
          ]);
          b.value = t;
          C.value = l;
          m.value = await categoryApi.getTemplate(e.category_id).catch(() => null);
        } catch (t) {
          u.toast(errorMessage(t), "err");
        }
      }
      function P(e) {
        const t = new Set(g.value);
        t.has(e) ? t.delete(e) : t.add(e);
        g.value = t;
      }
      function B() {
        const e = b.value;
        h(
          "调整影响分析 · " + a.value.name,
          `<div class="big-num">${r((e == null ? void 0 : e.goods_count) || 0)}</div><div class="mini">个商品在此分类下 · ${(e == null ? void 0 : e.child_count) || 0} 个子分类</div>
     <div class="result-line warn" style="margin-top:12px"><b>${e != null && e.can_delete ? "可删除" : "⚠ 有商品的分类不能直接删除"}</b>，只能改名/排序/启停。</div>
     <p>来自 <code>POST /api/v1/categories/${a.value.category_id}/impact</code>：${(e == null ? void 0 : e.message) || ""}</p>`,
        );
      }
      function I() {
        if (!u.isAdmin) {
          u.toast("仅管理员可编辑分类", "err");
          return;
        }
        h(
          "编辑分类 / 设置属性模板",
          `<div class="result-line ok"><b>管理员操作</b>　PUT <code>/categories/${a.value.category_id}</code> + <code>/categories/${a.value.category_id}/template</code></div>
     <div class="drow"><span class="k">分类名称</span><span class="v">${a.value.name}</span></div>
     <div class="drow"><span class="k">层级</span><span class="v">${a.value.level} 级</span></div>
     <div class="drow"><span class="k">商品数</span><span class="v">${r(a.value.count)}</span></div>
     <div class="drow"><span class="k">当前模板</span><span class="v">${m.value ? JSON.stringify(m.value) : "未设置（可添加必填属性，如净含量、包装形态）"}</span></div>
     <div class="tip-note" style="margin:12px 0 0">模板变动影响该分类下 ${r(a.value.count)} 个商品的必填校验，需谨慎。</div>`,
        );
      }
      function U() {
        const e = C.value;
        h(
          "外部编码对照 · " + ((e == null ? void 0 : e.category_name) || a.value.name),
          `<div class="result-line ok"><b>共 ${(e == null ? void 0 : e.total) || 0} 条对照关系</b>　GET <code>/categories/${a.value.category_id}/external-map</code></div>
     <table><thead><tr><th>外部系统</th><th>外部编码</th><th>外部名称</th><th>映射方式</th><th>状态</th></tr></thead><tbody>
     ${((e == null ? void 0 : e.mappings) || []).map((t) => `<tr><td>${t.source_system}</td><td style="font-family:Menlo">${t.source_code}</td><td>${t.source_name}</td><td><span class="tag tg-blue">${t.map_type}</span></td><td>${t.status}</td></tr>`).join("")}
     </tbody></table>
     <div class="tip-note">${u.isAdmin ? "维护入口可用：PUT /categories/{id}/external-map（写入留痕）。" : "维护需管理员权限。"}</div>`,
        );
      }
      return (
        onMounted(async () => {
          await L();
          const e = x.value.find((t) => t.category_id === "C0203");
          e && f(e);
        }),
        (e, t) => (
          openBlock(),
          createElementBlock("div", null, [
            t[7] ||
              (t[7] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "分类与属性模板",
                -1,
              )),
            t[8] ||
              (t[8] = createElementVNode(
                "div",
                {
                  class: "page-desc",
                },
                "分类体系来自真实库 · 13 大类 / 149 启用小类 · 面向管理员",
                -1,
              )),
            createElementVNode("div", J, [
              createElementVNode("div", q, [
                t[1] || (t[1] = createElementVNode("h3", null, "分类树", -1)),
                createElementVNode("div", K, [
                  (openBlock(!0),
                  createElementBlock(
                    Fragment,
                    null,
                    renderList(y.value, (l) => {
                      var p, T, M;
                      return (
                        openBlock(),
                        createElementBlock(
                          "div",
                          {
                            key: l.category_id,
                          },
                          [
                            createElementVNode(
                              "div",
                              {
                                class: normalizeClass([
                                  "node",
                                  {
                                    sel:
                                      ((p = a.value) == null ? void 0 : p.category_id) ===
                                      l.category_id,
                                    c00: l.is_placeholder,
                                  },
                                ]),
                                onClick: (c) => f(l),
                              },
                              [
                                (T = l.children) != null && T.length
                                  ? (openBlock(),
                                    createElementBlock(
                                      "span",
                                      {
                                        key: 0,
                                        class: "caret",
                                        onClick: withModifiers((c) => P(l.category_id), ["stop"]),
                                      },
                                      toDisplayString(g.value.has(l.category_id) ? "▾" : "▸"),
                                      9,
                                      R,
                                    ))
                                  : (openBlock(), createElementBlock("span", W, "▪")),
                                createElementVNode("b", null, toDisplayString(l.name), 1),
                                createElementVNode("span", X, toDisplayString(r(l.count)), 1),
                              ],
                              10,
                              Q,
                            ),
                            (M = l.children) != null && M.length && g.value.has(l.category_id)
                              ? (openBlock(),
                                createElementBlock("div", Y, [
                                  (openBlock(!0),
                                  createElementBlock(
                                    Fragment,
                                    null,
                                    renderList(l.children, (c) => {
                                      var S;
                                      return (
                                        openBlock(),
                                        createElementBlock(
                                          "div",
                                          {
                                            class: normalizeClass([
                                              "node",
                                              {
                                                sel:
                                                  ((S = a.value) == null
                                                    ? void 0
                                                    : S.category_id) === c.category_id,
                                              },
                                            ]),
                                            key: c.category_id,
                                            onClick: (ie) => f(c),
                                          },
                                          [
                                            createTextVNode(toDisplayString(c.name), 1),
                                            createElementVNode(
                                              "span",
                                              ee,
                                              toDisplayString(r(c.count)),
                                              1,
                                            ),
                                          ],
                                          10,
                                          Z,
                                        )
                                      );
                                    }),
                                    128,
                                  )),
                                ]))
                              : createCommentVNode("", !0),
                          ],
                        )
                      );
                    }),
                    128,
                  )),
                ]),
              ]),
              a.value
                ? (openBlock(),
                  createElementBlock("div", te, [
                    createElementVNode("div", se, [
                      createElementVNode("h3", null, [
                        createTextVNode(toDisplayString(a.value.name) + " ", 1),
                        createElementVNode(
                          "span",
                          {
                            class: normalizeClass([
                              "tag",
                              a.value.status === "ACTIVE" ? "tg-green" : "tg-gray",
                            ]),
                          },
                          toDisplayString(a.value.status),
                          3,
                        ),
                      ]),
                      createElementVNode("div", ae, [
                        t[2] ||
                          (t[2] = createElementVNode(
                            "span",
                            {
                              class: "k",
                            },
                            "所属",
                            -1,
                          )),
                        createElementVNode("span", null, toDisplayString(V(a.value)), 1),
                        t[3] ||
                          (t[3] = createElementVNode(
                            "span",
                            {
                              class: "k",
                            },
                            "商品数",
                            -1,
                          )),
                        createElementVNode(
                          "span",
                          null,
                          toDisplayString(r(a.value.count)) + "（实时统计）",
                          1,
                        ),
                        t[4] ||
                          (t[4] = createElementVNode(
                            "span",
                            {
                              class: "k",
                            },
                            "属性模板",
                            -1,
                          )),
                        createElementVNode(
                          "span",
                          null,
                          toDisplayString(m.value ? "已设置" : "未设置"),
                          1,
                        ),
                        t[5] ||
                          (t[5] = createElementVNode(
                            "span",
                            {
                              class: "k",
                            },
                            "层级",
                            -1,
                          )),
                        createElementVNode("span", null, toDisplayString(a.value.level) + " 级", 1),
                      ]),
                      createElementVNode(
                        "div",
                        {
                          style: {
                            "margin-top": "14px",
                            display: "flex",
                            gap: "8px",
                            "flex-wrap": "wrap",
                          },
                        },
                        [
                          createElementVNode(
                            "button",
                            {
                              class: "btn sm",
                              onClick: B,
                            },
                            "调整影响分析",
                          ),
                          createElementVNode(
                            "button",
                            {
                              class: "btn plain sm",
                              onClick: I,
                            },
                            "编辑 / 设置属性模板",
                          ),
                          createElementVNode(
                            "button",
                            {
                              class: "btn plain sm",
                              onClick: U,
                            },
                            "外部编码对照",
                          ),
                        ],
                      ),
                    ]),
                    a.value.is_placeholder
                      ? (openBlock(),
                        createElementBlock("div", le, [
                          ...(t[6] ||
                            (t[6] = [
                              createElementVNode("b", null, "「未分类」说明", -1),
                              createTextVNode(
                                "：系统自动归置的仓库，不能往里新增商品，也不能删除。",
                                -1,
                              ),
                            ])),
                        ]))
                      : createCommentVNode("", !0),
                  ]))
                : createCommentVNode("", !0),
            ]),
            createVNode(
              InfoBox,
              {
                show: v.value.show,
                title: v.value.title,
                onClose: t[0] || (t[0] = (l) => (v.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(v.value.html),
                    },
                    null,
                    8,
                    ne,
                  ),
                ]),
                _: 1,
              },
              8,
              ["show", "title"],
            ),
          ])
        )
      );
    },
  };

export default Category;
