import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  createTextVNode,
  toDisplayString,
  Fragment,
  renderList,
  createVNode,
  withCtx,
  ref,
} from "vue";
import { adminApi, errorMessage } from "../api.js";
import { useRouter } from "vue-router";
import InfoBox from "../components/InfoBox.js";

const A = {
    class: "card",
  },
  B = {
    class: "tag tg-orange",
  },
  $ = {
    key: 0,
  },
  j = {
    key: 1,
  },
  q = {
    style: {
      "font-family": "Menlo",
    },
  },
  G = {
    class: "pager",
  },
  I = ["disabled"],
  N = {
    class: "cur",
  },
  T = ["innerHTML"],
  Governance = {
    name: "Governance",
    setup(V) {
      const v = useAppStore(),
        _ = useRouter(),
        c = ref([]),
        f = ref(0),
        a = ref(1),
        g = ref(!1),
        o = ref({
          show: !1,
          title: "",
          html: "",
        }),
        b = (l) => (l ?? 0).toLocaleString("en-US");
      function k(l, s) {
        o.value = {
          show: !0,
          title: l,
          html: s,
        };
      }
      async function m() {
        g.value = !0;
        try {
          const l = await adminApi.quarantine({
            page: a.value,
            page_size: 20,
            issue_type: "SAME_CODE_DIFF_GOODS",
          });
          c.value = l.items || [];
          f.value = l.total || 0;
        } catch (l) {
          v.toast(errorMessage(l), "err");
        } finally {
          g.value = !1;
        }
      }
      async function h() {
        var l;
        try {
          const { resp: s } = await adminApi.quarantineExport({
              issue_type: "SAME_CODE_DIFF_GOODS",
            }),
            e = await s.blob(),
            E = s.headers.get("content-disposition") || "",
            p = document.createElement("a");
          p.href = URL.createObjectURL(e);
          p.download =
            ((l = E.match(/filename="?([^";]+)"?/i)) == null ? void 0 : l[1]) ||
            "quarantine_export.csv";
          p.click();
          URL.revokeObjectURL(p.href);
          v.toast("导出已开始 · 行为已记入系统日志", "ok");
        } catch (s) {
          v.toast(errorMessage(s), "err");
        }
      }
      function x() {
        _.push("/goods?category_id=C00");
      }
      function C() {
        k(
          "类目增设提案 · 边界说明",
          '<div class="result-line warn"><b>此项需业务拍板</b>，由数据治理流程执行，本系统只读。</div><p>约 7.8 万条书号商品（978/979 开头）积压在「未分类」，因体系当前无「图书」一级类目。业务确认增设后，由治理流程批量迁移，本系统提供查询与迁移后的落库。</p><div class="tip-note">数据治理裁决不在本期系统范围（方案二 v3.5 边界）。</div>',
        );
      }
      return (
        onMounted(m),
        (l, s) => (
          openBlock(),
          createElementBlock("div", null, [
            s[12] ||
              (s[12] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "数据治理",
                -1,
              )),
            s[13] ||
              (s[13] = createElementVNode(
                "div",
                {
                  class: "page-desc",
                },
                "与数据治理流程协作的问题清单 · 本系统只读，处理归治理流程",
                -1,
              )),
            createElementVNode("div", A, [
              createElementVNode("h3", null, [
                s[3] || (s[3] = createTextVNode("「一码多品」冲突 ", -1)),
                createElementVNode("span", B, toDisplayString(b(f.value)) + " 条待处理", 1),
                createElementVNode(
                  "button",
                  {
                    class: "btn plain sm",
                    style: {
                      float: "right",
                    },
                    onClick: h,
                  },
                  "导出清单",
                ),
              ]),
              s[9] ||
                (s[9] = createElementVNode(
                  "div",
                  {
                    class: "tip-note warn",
                  },
                  [
                    createTextVNode("同一个条码对应了不同商品。这些条码在本系统中"),
                    createElementVNode("b", null, "禁止新增/修改商品"),
                    createTextVNode("，避免脏数据扩散；处理结果由治理流程回流后自动解锁。"),
                  ],
                  -1,
                )),
              createElementVNode("table", null, [
                s[8] ||
                  (s[8] = createElementVNode(
                    "thead",
                    null,
                    [
                      createElementVNode("tr", null, [
                        createElementVNode("th", null, "条码"),
                        createElementVNode("th", null, "问题类型"),
                        createElementVNode("th", null, "冲突字段"),
                        createElementVNode("th", null, "候选值 A / B"),
                        createElementVNode("th", null, "状态"),
                        createElementVNode("th", null, "发现时间"),
                      ]),
                    ],
                    -1,
                  )),
                createElementVNode("tbody", null, [
                  g.value
                    ? (openBlock(),
                      createElementBlock("tr", $, [
                        ...(s[4] ||
                          (s[4] = [
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
                    : c.value.length
                      ? (openBlock(!0),
                        createElementBlock(
                          Fragment,
                          {
                            key: 2,
                          },
                          renderList(
                            c.value,
                            (e) => (
                              openBlock(),
                              createElementBlock(
                                "tr",
                                {
                                  key: e.id,
                                },
                                [
                                  createElementVNode("td", q, toDisplayString(e.barcode), 1),
                                  s[6] ||
                                    (s[6] = createElementVNode(
                                      "td",
                                      null,
                                      [
                                        createElementVNode(
                                          "span",
                                          {
                                            class: "tag tg-orange",
                                          },
                                          "一码多品",
                                        ),
                                      ],
                                      -1,
                                    )),
                                  createElementVNode(
                                    "td",
                                    null,
                                    toDisplayString(e.conflict_field),
                                    1,
                                  ),
                                  createElementVNode(
                                    "td",
                                    null,
                                    toDisplayString(e.value_a) + " / " + toDisplayString(e.value_b),
                                    1,
                                  ),
                                  s[7] ||
                                    (s[7] = createElementVNode(
                                      "td",
                                      null,
                                      [
                                        createElementVNode(
                                          "span",
                                          {
                                            class: "tag tg-gray",
                                          },
                                          "待治理裁决",
                                        ),
                                      ],
                                      -1,
                                    )),
                                  createElementVNode("td", null, toDisplayString(e.created_at), 1),
                                ],
                              )
                            ),
                          ),
                          128,
                        ))
                      : (openBlock(),
                        createElementBlock("tr", j, [
                          ...(s[5] ||
                            (s[5] = [
                              createElementVNode(
                                "td",
                                {
                                  colspan: "6",
                                  class: "empty-row",
                                },
                                "暂无数据",
                                -1,
                              ),
                            ])),
                        ])),
                ]),
              ]),
              createElementVNode("div", G, [
                createTextVNode(
                  "共 " +
                    toDisplayString(b(f.value)) +
                    " 条 · 第 " +
                    toDisplayString(a.value) +
                    " 页 ",
                  1,
                ),
                createElementVNode(
                  "button",
                  {
                    disabled: a.value <= 1,
                    onClick:
                      s[0] ||
                      (s[0] = (e) => {
                        a.value--;
                        m();
                      }),
                  },
                  "‹",
                  8,
                  I,
                ),
                createElementVNode("button", N, toDisplayString(a.value), 1),
                createElementVNode(
                  "button",
                  {
                    onClick:
                      s[1] ||
                      (s[1] = (e) => {
                        a.value++;
                        m();
                      }),
                  },
                  "›",
                ),
              ]),
            ]),
            createElementVNode(
              "div",
              {
                class: "card",
              },
              [
                s[10] ||
                  (s[10] = createElementVNode(
                    "h3",
                    null,
                    [
                      createTextVNode("暂未分类积压 "),
                      createElementVNode(
                        "span",
                        {
                          class: "tag tg-gray",
                        },
                        "197,059 条",
                      ),
                    ],
                    -1,
                  )),
                s[11] ||
                  (s[11] = createElementVNode(
                    "div",
                    {
                      class: "tip-note",
                    },
                    "其中约 7.8 万条为书号商品（978/979 开头），体系当前无「图书」类目可归属。增设类目后可批量迁移——此项需业务拍板后由治理流程执行。",
                    -1,
                  )),
                createElementVNode(
                  "div",
                  {
                    style: {
                      "margin-top": "4px",
                      display: "flex",
                      gap: "8px",
                    },
                  },
                  [
                    createElementVNode(
                      "button",
                      {
                        class: "btn plain sm",
                        onClick: x,
                      },
                      "查看积压商品",
                    ),
                    createElementVNode(
                      "button",
                      {
                        class: "btn plain sm",
                        onClick: C,
                      },
                      "类目增设提案",
                    ),
                  ],
                ),
              ],
            ),
            createVNode(
              InfoBox,
              {
                show: o.value.show,
                title: o.value.title,
                onClose: s[2] || (s[2] = (e) => (o.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(o.value.html),
                    },
                    null,
                    8,
                    T,
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

export default Governance;
