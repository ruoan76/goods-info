import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  createTextVNode,
  toDisplayString,
  createCommentVNode,
  unref,
  Fragment,
  renderList,
  createVNode,
  withCtx,
  ref,
} from "vue";
import { useRouter } from "vue-router";
import { goodsApi, errorMessage, adminApi } from "../api.js";
import InfoBox from "../components/InfoBox.js";

const M = {
    class: "overview",
  },
  N = {
    class: "ov-card",
  },
  j = {
    class: "ov-n",
  },
  q = {
    key: 0,
    style: {
      "font-size": "11px",
      color: "var(--text3)",
      "font-weight": "400",
    },
  },
  A = {
    class: "ov-card",
  },
  B = {
    class: "ov-n",
  },
  G = {
    style: {
      "font-size": "14px",
      color: "var(--text3)",
    },
  },
  W = {
    class: "ov-card",
  },
  D = {
    class: "ov-n",
    style: {
      color: "var(--warning)",
    },
  },
  F = {
    class: "ov-card",
  },
  H = {
    class: "ov-n",
    style: {
      color: "var(--info)",
    },
  },
  I = {
    class: "dash-grid",
  },
  O = {
    class: "card",
    style: {
      padding: "14px 16px",
    },
  },
  P = {
    class: "num",
    style: {
      color: "var(--warning)",
    },
  },
  J = {
    class: "num",
    style: {
      color: "var(--warning)",
    },
  },
  K = {
    class: "todo-card ro",
    style: {
      border: "none",
      padding: "10px 2px",
    },
  },
  Q = {
    class: "num",
    style: {
      color: "var(--info)",
    },
  },
  X = {
    class: "card",
    style: {
      padding: "14px 16px",
    },
  },
  Y = {
    key: 0,
  },
  Z = {
    class: "rt",
  },
  ss = {
    class: "rt",
  },
  ts = {
    key: 1,
    class: "recent-item",
    style: {
      cursor: "default",
      border: "none",
    },
  },
  os = {
    class: "card",
    style: {
      padding: "14px 16px",
    },
  },
  ns = {
    class: "filter-row",
    style: {
      "margin-bottom": "10px",
    },
  },
  as = ["innerHTML"],
  Dashboard = {
    name: "Dashboard",
    setup(ls) {
      const p = useAppStore(),
        c = useRouter(),
        o = ref({
          goods_total: 0,
          category_l1: 0,
          category_l2_active: 0,
          price_pending: 0,
          unclassified: 0,
          quarantine_conflict: 0,
        }),
        y = ref([]),
        u = ref({
          show: !1,
          title: "",
          html: "",
        }),
        i = (l) => (l ?? 0).toLocaleString("en-US");
      function w(l, s) {
        u.value = {
          show: !0,
          title: l,
          html: s,
        };
      }
      async function _() {
        try {
          const [l, s] = await Promise.all([
            adminApi.dashboard(),
            adminApi
              .changeLog({
                limit: 8,
              })
              .catch(() => ({
                items: [],
              })),
          ]);
          o.value = l;
          y.value = s.items || [];
        } catch (l) {
          p.toast(errorMessage(l), "err");
        }
      }
      function C() {
        w(
          "首页数据来源 · 实时接口",
          `<div class="result-line ok"><b>4 张统计卡 + 最近处理均来自真实 API</b></div>
     <div class="drow"><span class="k">统计卡</span><span class="v"><code>GET /api/v1/admin/dashboard</code>（${o.value.goods_total_approx ? "总量为近似数（带标记）" : "精确数"}，待办数精确）</span></div>
     <div class="drow"><span class="k">最近处理</span><span class="v"><code>GET /api/v1/admin/change-log?limit=8</code></span></div>
     <div class="drow"><span class="k">用户活动</span><span class="v"><code>GET /api/v1/admin/users/{account}/activity</code></span></div>
     <div class="tip-note" style="margin:12px 0 0">当前实库：商品 ${i(o.value.goods_total)} · 价格待补 ${i(o.value.price_pending)} · 未分类 ${i(o.value.unclassified)} · 一码多品 ${i(o.value.quarantine_conflict)}</div>`,
        );
      }
      async function $() {
        var l;
        try {
          const { resp: s } = await goodsApi.export({
              page: 1,
              page_size: 1,
            }),
            n = s.headers.get("content-disposition") || "goods_export.csv",
            b = await s.blob(),
            m = document.createElement("a");
          m.href = URL.createObjectURL(b);
          m.download =
            ((l = n.match(/filename="?([^";]+)"?/i)) == null ? void 0 : l[1]) || "goods_export.csv";
          m.click();
          URL.revokeObjectURL(m.href);
          p.toast("导出已开始（上限 20 万行）· 行为已记入系统日志", "ok");
        } catch (s) {
          p.toast(errorMessage(s), "err");
        }
      }
      return (
        onMounted(_),
        (l, s) => (
          openBlock(),
          createElementBlock("div", null, [
            createElementVNode("div", M, [
              createElementVNode("div", N, [
                s[6] ||
                  (s[6] = createElementVNode(
                    "div",
                    {
                      class: "ov-bar",
                      style: {
                        background: "var(--primary)",
                      },
                    },
                    null,
                    -1,
                  )),
                createElementVNode("div", j, [
                  createTextVNode(toDisplayString(i(o.value.goods_total)), 1),
                  o.value.goods_total_approx
                    ? (openBlock(), createElementBlock("span", q, " ≈"))
                    : createCommentVNode("", !0),
                ]),
                s[7] ||
                  (s[7] = createElementVNode(
                    "div",
                    {
                      class: "ov-l",
                    },
                    "商品档案总数",
                    -1,
                  )),
                s[8] ||
                  (s[8] = createElementVNode(
                    "div",
                    {
                      class: "ov-x",
                    },
                    "条码全库唯一 · 主数据基线",
                    -1,
                  )),
              ]),
              createElementVNode("div", A, [
                s[9] ||
                  (s[9] = createElementVNode(
                    "div",
                    {
                      class: "ov-bar",
                      style: {
                        background: "var(--success)",
                      },
                    },
                    null,
                    -1,
                  )),
                createElementVNode("div", B, [
                  createTextVNode(toDisplayString(o.value.category_l1) + " ", 1),
                  createElementVNode(
                    "span",
                    G,
                    "/ " + toDisplayString(o.value.category_l2_active),
                    1,
                  ),
                ]),
                s[10] ||
                  (s[10] = createElementVNode(
                    "div",
                    {
                      class: "ov-l",
                    },
                    "大类 / 启用小类",
                    -1,
                  )),
                s[11] ||
                  (s[11] = createElementVNode(
                    "div",
                    {
                      class: "ov-x",
                    },
                    "分类体系 · 属性模板挂载",
                    -1,
                  )),
              ]),
              createElementVNode("div", W, [
                s[12] ||
                  (s[12] = createElementVNode(
                    "div",
                    {
                      class: "ov-bar",
                      style: {
                        background: "var(--warning)",
                      },
                    },
                    null,
                    -1,
                  )),
                createElementVNode("div", D, toDisplayString(i(o.value.price_pending)), 1),
                s[13] ||
                  (s[13] = createElementVNode(
                    "div",
                    {
                      class: "ov-l",
                    },
                    "价格待补商品",
                    -1,
                  )),
                s[14] ||
                  (s[14] = createElementVNode(
                    "div",
                    {
                      class: "ov-x",
                    },
                    "售价为 0 或未填 · 可批量维护",
                    -1,
                  )),
              ]),
              createElementVNode("div", F, [
                s[15] ||
                  (s[15] = createElementVNode(
                    "div",
                    {
                      class: "ov-bar",
                      style: {
                        background: "var(--info)",
                      },
                    },
                    null,
                    -1,
                  )),
                createElementVNode("div", H, toDisplayString(i(o.value.unclassified)), 1),
                s[16] ||
                  (s[16] = createElementVNode(
                    "div",
                    {
                      class: "ov-l",
                    },
                    "暂未分类商品",
                    -1,
                  )),
                s[17] ||
                  (s[17] = createElementVNode(
                    "div",
                    {
                      class: "ov-x",
                    },
                    "系统占位 · 待治理流程归属",
                    -1,
                  )),
              ]),
            ]),
            createElementVNode("div", I, [
              createElementVNode("div", null, [
                createElementVNode("div", O, [
                  s[26] ||
                    (s[26] = createElementVNode(
                      "h3",
                      {
                        style: {
                          "margin-bottom": "8px",
                        },
                      },
                      "今日待办",
                      -1,
                    )),
                  unref(p).canWrite
                    ? (openBlock(),
                      createElementBlock(
                        "div",
                        {
                          key: 0,
                          class: "todo-card",
                          style: {
                            border: "none",
                            padding: "10px 2px",
                          },
                          onClick: s[0] || (s[0] = (n) => unref(c).push("/fillprice")),
                        },
                        [
                          s[18] ||
                            (s[18] = createElementVNode(
                              "span",
                              {
                                class: "go",
                              },
                              "去处理 →",
                              -1,
                            )),
                          s[19] ||
                            (s[19] = createElementVNode(
                              "div",
                              {
                                class: "tl",
                              },
                              [
                                createTextVNode("价格待补 "),
                                createElementVNode(
                                  "span",
                                  {
                                    style: {
                                      "font-size": "11px",
                                      color: "var(--text3)",
                                    },
                                  },
                                  "（价格为 0 或未填）",
                                ),
                              ],
                              -1,
                            )),
                          createElementVNode(
                            "div",
                            P,
                            toDisplayString(i(o.value.price_pending)),
                            1,
                          ),
                          s[20] ||
                            (s[20] = createElementVNode(
                              "div",
                              {
                                class: "td2",
                              },
                              "填一个少一个，点这里进入补价清单",
                              -1,
                            )),
                        ],
                      ))
                    : createCommentVNode("", !0),
                  unref(p).isAdmin
                    ? (openBlock(),
                      createElementBlock(
                        "div",
                        {
                          key: 1,
                          class: "todo-card",
                          style: {
                            border: "none",
                            padding: "10px 2px",
                          },
                          onClick: s[1] || (s[1] = (n) => unref(c).push("/governance")),
                        },
                        [
                          s[21] ||
                            (s[21] = createElementVNode(
                              "span",
                              {
                                class: "go",
                              },
                              "查看 →",
                              -1,
                            )),
                          s[22] ||
                            (s[22] = createElementVNode(
                              "div",
                              {
                                class: "tl",
                              },
                              [
                                createTextVNode("一码多品待裁决 "),
                                createElementVNode(
                                  "span",
                                  {
                                    class: "tag tg-gray",
                                  },
                                  "只读",
                                ),
                              ],
                              -1,
                            )),
                          createElementVNode(
                            "div",
                            J,
                            toDisplayString(i(o.value.quarantine_conflict)),
                            1,
                          ),
                          s[23] ||
                            (s[23] = createElementVNode(
                              "div",
                              {
                                class: "td2",
                              },
                              "同一条码对应多个商品，由治理流程处理，本系统只提供查询",
                              -1,
                            )),
                        ],
                      ))
                    : createCommentVNode("", !0),
                  createElementVNode("div", K, [
                    s[24] ||
                      (s[24] = createElementVNode(
                        "div",
                        {
                          class: "tl",
                        },
                        [
                          createTextVNode("暂未分类 "),
                          createElementVNode(
                            "span",
                            {
                              class: "tag tg-gray",
                            },
                            "管理员处理",
                          ),
                        ],
                        -1,
                      )),
                    createElementVNode("div", Q, toDisplayString(i(o.value.unclassified)), 1),
                    s[25] ||
                      (s[25] = createElementVNode(
                        "div",
                        {
                          class: "td2",
                        },
                        "含一批书籍类商品，需扩充分类后归属，由管理员跟进",
                        -1,
                      )),
                  ]),
                ]),
                createElementVNode("div", X, [
                  createElementVNode(
                    "h3",
                    {
                      style: {
                        "margin-bottom": "6px",
                      },
                    },
                    [
                      s[27] || (s[27] = createTextVNode("最近处理 ", -1)),
                      createElementVNode(
                        "a",
                        {
                          style: {
                            float: "right",
                            "font-size": "11px",
                            "font-weight": "400",
                          },
                          onClick: C,
                        },
                        "数据来源 ↗",
                      ),
                    ],
                  ),
                  y.value.length
                    ? (openBlock(),
                      createElementBlock("div", Y, [
                        (openBlock(!0),
                        createElementBlock(
                          Fragment,
                          null,
                          renderList(
                            y.value,
                            (n, b) => (
                              openBlock(),
                              createElementBlock(
                                "div",
                                {
                                  class: "recent-item",
                                  key: b,
                                },
                                [
                                  createElementVNode("span", null, [
                                    createTextVNode(
                                      toDisplayString(n.barcode || n.target) + " ",
                                      1,
                                    ),
                                    createElementVNode(
                                      "span",
                                      Z,
                                      toDisplayString(n.action || n.field || "变更"),
                                      1,
                                    ),
                                  ]),
                                  createElementVNode(
                                    "span",
                                    ss,
                                    toDisplayString(n.operator || n.created_at || ""),
                                    1,
                                  ),
                                ],
                              )
                            ),
                          ),
                          128,
                        )),
                      ]))
                    : (openBlock(),
                      createElementBlock("div", ts, "暂无变更记录 · 商品改动后自动显示在这里")),
                ]),
              ]),
              createElementVNode("div", null, [
                createElementVNode("div", os, [
                  s[28] ||
                    (s[28] = createElementVNode(
                      "h3",
                      {
                        style: {
                          "margin-bottom": "8px",
                        },
                      },
                      "常用操作",
                      -1,
                    )),
                  createElementVNode("div", ns, [
                    createElementVNode(
                      "button",
                      {
                        class: "btn sm",
                        onClick: s[2] || (s[2] = (n) => unref(c).push("/goods")),
                      },
                      "浏览商品档案",
                    ),
                    unref(p).canWrite
                      ? (openBlock(),
                        createElementBlock(
                          "button",
                          {
                            key: 0,
                            class: "btn plain sm",
                            onClick: s[3] || (s[3] = (n) => unref(c).push("/goods/new")),
                          },
                          "+ 单条建档",
                        ))
                      : createCommentVNode("", !0),
                    unref(p).canWrite
                      ? (openBlock(),
                        createElementBlock(
                          "button",
                          {
                            key: 1,
                            class: "btn plain sm",
                            onClick: s[4] || (s[4] = (n) => unref(c).push("/goods/new?tab=batch")),
                          },
                          "批量导入 CSV",
                        ))
                      : createCommentVNode("", !0),
                    createElementVNode(
                      "button",
                      {
                        class: "btn plain sm",
                        onClick: $,
                      },
                      "导出数据",
                    ),
                  ]),
                  s[29] ||
                    (s[29] = createElementVNode(
                      "div",
                      {
                        class: "tip-note",
                        style: {
                          margin: "0",
                        },
                      },
                      "新品引进走规范建档：新增必查重、条码不可改、变更必留痕 · 大批量请用 CSV 模板导入",
                      -1,
                    )),
                ]),
                s[30] ||
                  (s[30] = createElementVNode(
                    "div",
                    {
                      class: "card",
                      style: {
                        padding: "14px 16px",
                      },
                    },
                    [
                      createElementVNode(
                        "h3",
                        {
                          style: {
                            "margin-bottom": "6px",
                          },
                        },
                        "使用提示",
                      ),
                      createElementVNode(
                        "div",
                        {
                          style: {
                            "font-size": "12px",
                            color: "var(--text2)",
                            "line-height": "2",
                          },
                        },
                        [
                          createTextVNode(" · 商品档案页"),
                          createElementVNode("b", null, "左边选分类、右边看商品"),
                          createTextVNode("，也可按条码/名称查询"),
                          createElementVNode("br"),
                          createTextVNode(" · 详情页里"),
                          createElementVNode("b", null, "点价格、名称就能直接改"),
                          createTextVNode("，改完回车保存"),
                          createElementVNode("br"),
                          createTextVNode(
                            " · 本系统负责主数据维护，门店上报/扫码校准属演进项，不在本期",
                          ),
                          createElementVNode("br"),
                          createTextVNode(" · 停用的商品记录永远保留，随时可以恢复 "),
                        ],
                      ),
                    ],
                    -1,
                  )),
              ]),
            ]),
            createVNode(
              InfoBox,
              {
                show: u.value.show,
                title: u.value.title,
                onClose: s[5] || (s[5] = (n) => (u.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(u.value.html),
                    },
                    null,
                    8,
                    as,
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

export default Dashboard;
