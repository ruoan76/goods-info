import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  watch,
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  withDirectives,
  vModelText,
  normalizeClass,
  toDisplayString,
  Fragment,
  renderList,
  withModifiers,
  createTextVNode,
  createCommentVNode,
  withKeys,
  vModelSelect,
  unref,
  createVNode,
  withCtx,
  ref,
  computed,
} from "vue";
import { goodsApi, errorMessage, categoryApi } from "../api.js";
import { useRouter, useRoute } from "vue-router";
import InfoBox from "../components/InfoBox.js";

const pe = {
    class: "tree-layout",
  },
  ge = {
    class: "card",
    style: {
      margin: "0",
    },
  },
  ye = {
    class: "gtree-wrap",
  },
  _e = {
    class: "tree",
  },
  me = {
    class: "cnt",
  },
  he = ["title", "onClick"],
  fe = ["onClick"],
  ke = {
    key: 1,
    class: "caret",
  },
  be = {
    key: 2,
  },
  we = {
    key: 4,
    class: "ph",
  },
  Ce = {
    class: "cnt",
  },
  xe = {
    key: 0,
    class: "children",
  },
  Le = ["onClick"],
  Ae = {
    class: "cnt",
  },
  Ve = {
    class: "card",
    style: {
      margin: "0",
    },
  },
  Ee = {
    class: "gl-head",
  },
  Se = {
    class: "gl-title",
  },
  $e = {
    class: "gl-sub",
  },
  Ie = {
    style: {
      color: "var(--primary)",
    },
  },
  Me = {
    key: 0,
    style: {
      color: "var(--text3)",
    },
  },
  Ne = {
    class: "filter-row",
    style: {
      "margin-bottom": "10px",
    },
  },
  Te = {
    class: "gl-table",
  },
  Ue = {
    key: 0,
  },
  De = {
    key: 1,
  },
  qe = ["onClick"],
  ze = {
    style: {
      "font-family": "Menlo",
    },
  },
  Re = {
    class: "pager",
  },
  Fe = ["disabled"],
  Oe = {
    class: "cur",
  },
  je = ["disabled"],
  Be = ["innerHTML"],
  GoodsList = {
    name: "GoodsList",
    setup(Ge) {
      const _ = useAppStore(),
        z = useRouter(),
        M = useRoute(),
        x = ref([]),
        m = ref(""),
        L = ref(new Set(["C01", "C02"])),
        c = ref({
          category_id: "ALL",
          name: "全部分类",
          count: 0,
          path: "全部分类",
        }),
        p = ref(""),
        h = ref(""),
        f = ref(""),
        v = ref(1),
        W = ref(20),
        A = ref([]),
        V = ref(0),
        R = ref(!1),
        F = ref(!1),
        N = ref(!1),
        E = ref({
          show: !1,
          title: "",
          html: "",
        }),
        k = (o) => (o ?? 0).toLocaleString("en-US"),
        O = {
          ACTIVE: ["在售", "tg-green"],
          INACTIVE: ["已停用", "tg-gray"],
          VOIDED: ["已作废", "tg-red"],
        };
      function j(o, e = []) {
        return (
          o.forEach((t) => {
            var d;
            e.push(t);
            (d = t.children) != null && d.length && j(t.children, e);
          }),
          e
        );
      }
      const g = computed(() => j(x.value)),
        J = computed(() => {
          const o = m.value.trim();
          if (!o) return x.value;
          const e = new Set();
          g.value.forEach((d) => {
            var u;
            if (d.name.includes(o)) {
              e.add(d.category_id);
              let s = d.parent_id;
              for (; s;) {
                e.add(s);
                s = (u = g.value.find((B) => B.category_id === s)) == null ? void 0 : u.parent_id;
              }
            }
          });
          const t = (d) =>
            d
              .filter((u) => e.has(u.category_id))
              .map((u) => ({
                ...u,
                children: t(u.children || []),
              }));
          return t(x.value);
        });
      async function X() {
        try {
          const o = await categoryApi.tree();
          x.value = o.tree || [];
          const e = g.value.find((t) => t.category_id === "ALL");
        } catch (o) {
          _.toast(errorMessage(o), "err");
        }
      }
      async function b() {
        N.value = !0;
        try {
          const o = {
            page: v.value,
            page_size: W.value,
          };
          c.value.category_id !== "ALL" && (o.category_id = c.value.category_id);
          p.value && (o.q = p.value);
          h.value && (o.status = h.value);
          f.value && (o.price_state = f.value);
          const e = await goodsApi.list(o);
          A.value = e.items || [];
          V.value = e.total ?? 0;
          R.value = !!e.total_approx;
          F.value = !!e.has_more;
        } catch (o) {
          _.toast(errorMessage(o), "err");
          A.value = [];
        } finally {
          N.value = !1;
        }
      }
      function S(o) {
        c.value = {
          category_id: o.category_id,
          name: o.name,
          count: o.count,
          path: o.path || o.name,
        };
        v.value = 1;
        b();
      }
      function Y(o) {
        const e = new Set(L.value);
        e.has(o) ? e.delete(o) : e.add(o);
        L.value = e;
      }
      function T() {
        v.value = 1;
        b();
      }
      function Z() {
        p.value = "";
        h.value = "";
        f.value = "";
        T();
      }
      function U(o) {
        if (o.level === 1) return o.name;
        const e = g.value.find((t) => t.category_id === o.parent_id);
        return e ? e.name + " / " + o.name : o.name;
      }
      async function ee() {
        var o;
        try {
          const e = {
            page: 1,
            page_size: 1,
          };
          c.value.category_id !== "ALL" && (e.category_id = c.value.category_id);
          p.value && (e.q = p.value);
          const { resp: t } = await goodsApi.export(e),
            d = await t.blob(),
            u = t.headers.get("content-disposition") || "",
            s = document.createElement("a");
          s.href = URL.createObjectURL(d);
          s.download =
            ((o = u.match(/filename="?([^";]+)"?/i)) == null ? void 0 : o[1]) || "goods_export.csv";
          s.click();
          URL.revokeObjectURL(s.href);
          _.toast("导出已开始 · 行为已记入系统日志", "ok");
        } catch (e) {
          _.toast(errorMessage(e), "err");
        }
      }
      function te(o) {
        z.push(`/goods/${encodeURIComponent(o)}/detail`);
      }
      return (
        watch(
          () => M.query.category_id,
          (o) => {
            if (o) {
              const e = g.value.find((t) => t.category_id === o);
              e && S(e);
            }
          },
        ),
        onMounted(async () => {
          if ((await X(), M.query.category_id)) {
            const o = g.value.find((e) => e.category_id === M.query.category_id);
            o &&
              (c.value = {
                category_id: o.category_id,
                name: o.name,
                count: o.count,
                path: U(o),
              });
          }
          b();
        }),
        (o, e) => (
          openBlock(),
          createElementBlock("div", null, [
            e[19] ||
              (e[19] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "商品档案",
                -1,
              )),
            e[20] ||
              (e[20] = createElementVNode(
                "div",
                {
                  class: "page-desc",
                },
                "左边选分类，右边看商品 · 也可按条码或名称精确查询",
                -1,
              )),
            createElementVNode("div", pe, [
              createElementVNode("div", ge, [
                withDirectives(
                  createElementVNode(
                    "input",
                    {
                      class: "tree-search",
                      "onUpdate:modelValue": e[0] || (e[0] = (t) => (m.value = t)),
                      placeholder: "搜索分类名称",
                    },
                    null,
                    512,
                  ),
                  [[vModelText, m.value]],
                ),
                createElementVNode("div", ye, [
                  createElementVNode("div", _e, [
                    createElementVNode(
                      "div",
                      {
                        class: normalizeClass([
                          "node",
                          {
                            sel: c.value.category_id === "ALL",
                          },
                        ]),
                        onClick:
                          e[1] ||
                          (e[1] = (t) =>
                            S({
                              category_id: "ALL",
                              name: "全部分类",
                              count: 0,
                            })),
                      },
                      [
                        e[9] || (e[9] = createElementVNode("b", null, "全部分类", -1)),
                        createElementVNode("span", me, toDisplayString(k(V.value)), 1),
                      ],
                      2,
                    ),
                    (openBlock(!0),
                    createElementBlock(
                      Fragment,
                      null,
                      renderList(J.value, (t) => {
                        var d, u;
                        return (
                          openBlock(),
                          createElementBlock(
                            Fragment,
                            {
                              key: t.category_id,
                            },
                            [
                              createElementVNode(
                                "div",
                                {
                                  class: normalizeClass([
                                    "node",
                                    {
                                      sel: c.value.category_id === t.category_id,
                                      c00: t.is_placeholder,
                                    },
                                  ]),
                                  title: t.is_placeholder
                                    ? "系统占位分类：治理流程归属地，不能新增商品"
                                    : "",
                                  onClick: (s) =>
                                    S({
                                      ...t,
                                      path: U(t),
                                    }),
                                },
                                [
                                  (d = t.children) != null && d.length
                                    ? (openBlock(),
                                      createElementBlock(
                                        "span",
                                        {
                                          key: 0,
                                          class: "caret",
                                          onClick: withModifiers((s) => Y(t.category_id), ["stop"]),
                                        },
                                        toDisplayString(
                                          L.value.has(t.category_id) || m.value ? "▾" : "▸",
                                        ),
                                        9,
                                        fe,
                                      ))
                                    : (openBlock(), createElementBlock("span", ke, "▪")),
                                  t.level === 1
                                    ? (openBlock(),
                                      createElementBlock("b", be, toDisplayString(t.name), 1))
                                    : (openBlock(),
                                      createElementBlock(
                                        Fragment,
                                        {
                                          key: 3,
                                        },
                                        [createTextVNode(toDisplayString(t.name), 1)],
                                        64,
                                      )),
                                  t.is_placeholder
                                    ? (openBlock(), createElementBlock("span", we, "占位"))
                                    : createCommentVNode("", !0),
                                  createElementVNode("span", Ce, toDisplayString(k(t.count)), 1),
                                ],
                                10,
                                he,
                              ),
                              (u = t.children) != null &&
                              u.length &&
                              (L.value.has(t.category_id) || m.value)
                                ? (openBlock(),
                                  createElementBlock("div", xe, [
                                    (openBlock(!0),
                                    createElementBlock(
                                      Fragment,
                                      null,
                                      renderList(
                                        t.children,
                                        (s) => (
                                          openBlock(),
                                          createElementBlock(
                                            "div",
                                            {
                                              class: normalizeClass([
                                                "node",
                                                {
                                                  sel: c.value.category_id === s.category_id,
                                                },
                                              ]),
                                              key: s.category_id,
                                              onClick: (B) =>
                                                S({
                                                  ...s,
                                                  path: U(s),
                                                }),
                                            },
                                            [
                                              createTextVNode(toDisplayString(s.name), 1),
                                              createElementVNode(
                                                "span",
                                                Ae,
                                                toDisplayString(k(s.count)),
                                                1,
                                              ),
                                            ],
                                            10,
                                            Le,
                                          )
                                        ),
                                      ),
                                      128,
                                    )),
                                  ]))
                                : createCommentVNode("", !0),
                            ],
                            64,
                          )
                        );
                      }),
                      128,
                    )),
                  ]),
                ]),
                e[10] ||
                  (e[10] = createElementVNode(
                    "div",
                    {
                      style: {
                        "margin-top": "10px",
                        "padding-top": "8px",
                        "border-top": "1px dashed var(--border)",
                        "font-size": "11px",
                        color: "var(--text3)",
                      },
                    },
                    [
                      createTextVNode("分类数据来自 "),
                      createElementVNode("code", null, "/categories/tree"),
                    ],
                    -1,
                  )),
              ]),
              createElementVNode("div", Ve, [
                createElementVNode("div", Ee, [
                  createElementVNode("div", Se, toDisplayString(c.value.path), 1),
                  createElementVNode("div", $e, [
                    e[11] || (e[11] = createTextVNode("共 ", -1)),
                    createElementVNode("b", Ie, toDisplayString(k(V.value)), 1),
                    e[12] || (e[12] = createTextVNode(" 条", -1)),
                    R.value
                      ? (openBlock(), createElementBlock("span", Me, "（近似）"))
                      : createCommentVNode("", !0),
                  ]),
                ]),
                createElementVNode("div", Ne, [
                  withDirectives(
                    createElementVNode(
                      "input",
                      {
                        "onUpdate:modelValue": e[2] || (e[2] = (t) => (p.value = t)),
                        placeholder: "条码或商品名称，回车查询",
                        onKeyup: withKeys(T, ["enter"]),
                      },
                      null,
                      544,
                    ),
                    [[vModelText, p.value]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "select",
                      {
                        "onUpdate:modelValue": e[3] || (e[3] = (t) => (h.value = t)),
                      },
                      [
                        ...(e[13] ||
                          (e[13] = [
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
                              "在售",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "INACTIVE",
                              },
                              "已停用",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "VOIDED",
                              },
                              "已作废",
                              -1,
                            ),
                          ])),
                      ],
                      512,
                    ),
                    [[vModelSelect, h.value]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "select",
                      {
                        "onUpdate:modelValue": e[4] || (e[4] = (t) => (f.value = t)),
                      },
                      [
                        ...(e[14] ||
                          (e[14] = [
                            createElementVNode(
                              "option",
                              {
                                value: "",
                              },
                              "价格不限",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "HAS",
                              },
                              "有价格",
                              -1,
                            ),
                            createElementVNode(
                              "option",
                              {
                                value: "PENDING",
                              },
                              "价格待补",
                              -1,
                            ),
                          ])),
                      ],
                      512,
                    ),
                    [[vModelSelect, f.value]],
                  ),
                  createElementVNode(
                    "button",
                    {
                      class: "btn sm",
                      onClick: T,
                    },
                    "查询",
                  ),
                  createElementVNode(
                    "button",
                    {
                      class: "btn plain sm",
                      onClick: Z,
                    },
                    "重置",
                  ),
                  createElementVNode(
                    "button",
                    {
                      class: "btn plain sm",
                      onClick: ee,
                    },
                    "导出",
                  ),
                  unref(_).canWrite
                    ? (openBlock(),
                      createElementBlock(
                        "button",
                        {
                          key: 0,
                          class: "btn plain sm",
                          onClick: e[5] || (e[5] = (t) => unref(z).push("/goods/new")),
                        },
                        "+ 新增商品",
                      ))
                    : createCommentVNode("", !0),
                ]),
                createElementVNode("table", Te, [
                  e[18] ||
                    (e[18] = createElementVNode(
                      "thead",
                      null,
                      [
                        createElementVNode("tr", null, [
                          createElementVNode("th", null, "条码"),
                          createElementVNode("th", null, "商品名称"),
                          createElementVNode("th", null, "分类"),
                          createElementVNode("th", null, "售价"),
                          createElementVNode("th", null, "状态"),
                          createElementVNode("th", null, "操作"),
                        ]),
                      ],
                      -1,
                    )),
                  createElementVNode("tbody", null, [
                    N.value
                      ? (openBlock(),
                        createElementBlock("tr", Ue, [
                          ...(e[15] ||
                            (e[15] = [
                              createElementVNode(
                                "td",
                                {
                                  colspan: "6",
                                  class: "empty-row",
                                },
                                "加载中…",
                                -1,
                              ),
                            ])),
                        ]))
                      : A.value.length
                        ? (openBlock(!0),
                          createElementBlock(
                            Fragment,
                            {
                              key: 2,
                            },
                            renderList(
                              A.value,
                              (t) => (
                                openBlock(),
                                createElementBlock(
                                  "tr",
                                  {
                                    key: t.barcode,
                                    onClick: (d) => te(t.barcode),
                                  },
                                  [
                                    createElementVNode("td", ze, toDisplayString(t.barcode), 1),
                                    createElementVNode(
                                      "td",
                                      null,
                                      toDisplayString(t.goods_name),
                                      1,
                                    ),
                                    createElementVNode(
                                      "td",
                                      null,
                                      toDisplayString(t.category_path || "—"),
                                      1,
                                    ),
                                    createElementVNode(
                                      "td",
                                      {
                                        class: normalizeClass({
                                          zero: !t.outprice || +t.outprice == 0,
                                        }),
                                      },
                                      toDisplayString(
                                        t.outprice && +t.outprice > 0
                                          ? "¥ " + (+t.outprice).toFixed(2)
                                          : "价格待补",
                                      ),
                                      3,
                                    ),
                                    createElementVNode("td", null, [
                                      createElementVNode(
                                        "span",
                                        {
                                          class: normalizeClass([
                                            "tag",
                                            (O[t.status] || ["—", "tg-gray"])[1],
                                          ]),
                                        },
                                        toDisplayString((O[t.status] || ["—", ""])[0]),
                                        3,
                                      ),
                                    ]),
                                    e[17] ||
                                      (e[17] = createElementVNode(
                                        "td",
                                        null,
                                        [createElementVNode("a", null, "详情")],
                                        -1,
                                      )),
                                  ],
                                  8,
                                  qe,
                                )
                              ),
                            ),
                            128,
                          ))
                        : (openBlock(),
                          createElementBlock("tr", De, [
                            ...(e[16] ||
                              (e[16] = [
                                createElementVNode(
                                  "td",
                                  {
                                    colspan: "6",
                                    class: "empty-row",
                                  },
                                  "没有匹配的商品，换个分类或关键词试试",
                                  -1,
                                ),
                              ])),
                          ])),
                  ]),
                ]),
                createElementVNode("div", Re, [
                  createTextVNode(
                    " 共 " +
                      toDisplayString(k(V.value)) +
                      " 条 · 第 " +
                      toDisplayString(v.value) +
                      " 页 ",
                    1,
                  ),
                  createElementVNode(
                    "button",
                    {
                      disabled: v.value <= 1,
                      onClick:
                        e[6] ||
                        (e[6] = (t) => {
                          v.value--;
                          b();
                        }),
                    },
                    "‹",
                    8,
                    Fe,
                  ),
                  createElementVNode("button", Oe, toDisplayString(v.value), 1),
                  createElementVNode(
                    "button",
                    {
                      disabled: !F.value,
                      onClick:
                        e[7] ||
                        (e[7] = (t) => {
                          v.value++;
                          b();
                        }),
                    },
                    "›",
                    8,
                    je,
                  ),
                ]),
              ]),
            ]),
            createVNode(
              InfoBox,
              {
                show: E.value.show,
                title: E.value.title,
                onClose: e[8] || (e[8] = (t) => (E.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(E.value.html),
                    },
                    null,
                    8,
                    Be,
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

export default GoodsList;
