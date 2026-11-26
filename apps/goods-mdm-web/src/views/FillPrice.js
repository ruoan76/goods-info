import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  createTextVNode,
  toDisplayString,
  createCommentVNode,
  Fragment,
  renderList,
  withDirectives,
  vModelText,
  withKeys,
  unref,
  ref,
} from "vue";
import { goodsApi, errorMessage, adminApi } from "../api.js";

const C = {
    class: "page-desc",
  },
  $ = {
    class: "card",
  },
  B = {
    key: 0,
  },
  D = {
    style: {
      "font-family": "Menlo",
    },
  },
  K = {
    class: "zero",
  },
  L = {
    key: 0,
    class: "tag tg-green",
  },
  P = ["onUpdate:modelValue", "onKeyup"],
  z = ["disabled", "onClick"],
  FillPrice = {
    name: "FillPrice",
    setup(A) {
      const n = useAppStore(),
        goods = ref([]),
        pendingCount = ref(0),
        priceInputs = ref({}),
        savedBarcodes = ref(new Set());
      async function loadPendingPrices() {
        try {
          const [s, t] = await Promise.all([
            adminApi.dashboard(),
            goodsApi.list({
              price_state: "PENDING",
              page: 1,
              page_size: 100,
            }),
          ]);
          pendingCount.value = s.price_pending;
          goods.value = t.items || [];
        } catch (s) {
          n.toast(errorMessage(s), "err");
        }
      }
      async function savePrice(s) {
        const t = (priceInputs.value[s.barcode] || "").trim();
        if (!t || isNaN(+t) || +t <= 0) {
          n.toast("请先填入有效的新售价", "err");
          return;
        }
        try {
          await goodsApi.patch(s.barcode, "outprice", t, "价格待补清单批量补价", s.version);
          savedBarcodes.value.add(s.barcode);
          pendingCount.value = Math.max(0, pendingCount.value - 1);
          n.toast(
            `已保存售价 ¥${(+t).toFixed(2)} · 剩余 ${pendingCount.value.toLocaleString()} 条待补`,
            "ok",
          );
        } catch (a) {
          n.toast(errorMessage(a), "err");
        }
      }
      return (
        onMounted(loadPendingPrices),
        (s, t) => (
          openBlock(),
          createElementBlock("div", null, [
            t[5] ||
              (t[5] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "价格待补清单",
                -1,
              )),
            createElementVNode("div", C, [
              t[0] ||
                (t[0] = createTextVNode("这些商品的价格为 0 或未填，填一个少一个 · 剩余 ", -1)),
              createElementVNode(
                "b",
                null,
                toDisplayString(pendingCount.value.toLocaleString()),
                1,
              ),
              t[1] || (t[1] = createTextVNode(" 条（来自实时统计）", -1)),
            ]),
            createElementVNode("div", $, [
              createElementVNode("table", null, [
                t[3] ||
                  (t[3] = createElementVNode(
                    "thead",
                    null,
                    [
                      createElementVNode("tr", null, [
                        createElementVNode("th", null, "条码"),
                        createElementVNode("th", null, "商品名称"),
                        createElementVNode("th", null, "分类"),
                        createElementVNode("th", null, "当前售价"),
                        createElementVNode("th", null, "填入新售价"),
                        createElementVNode("th"),
                      ]),
                    ],
                    -1,
                  )),
                createElementVNode("tbody", null, [
                  goods.value.length
                    ? createCommentVNode("", !0)
                    : (openBlock(),
                      createElementBlock("tr", B, [
                        ...(t[2] ||
                          (t[2] = [
                            createElementVNode(
                              "td",
                              {
                                colspan: "6",
                                style: {
                                  "text-align": "center",
                                  padding: "30px",
                                  color: "var(--text3)",
                                },
                              },
                              "加载中或无待补商品",
                              -1,
                            ),
                          ])),
                      ])),
                  (openBlock(!0),
                  createElementBlock(
                    Fragment,
                    null,
                    renderList(
                      goods.value,
                      (a) => (
                        openBlock(),
                        createElementBlock(
                          "tr",
                          {
                            key: a.barcode,
                          },
                          [
                            createElementVNode("td", D, toDisplayString(a.barcode), 1),
                            createElementVNode("td", null, toDisplayString(a.goods_name), 1),
                            createElementVNode(
                              "td",
                              null,
                              toDisplayString(a.category_path || "—"),
                              1,
                            ),
                            createElementVNode(
                              "td",
                              K,
                              toDisplayString(
                                a.outprice && +a.outprice > 0
                                  ? "¥" + (+a.outprice).toFixed(2)
                                  : "价格待补",
                              ),
                              1,
                            ),
                            createElementVNode("td", null, [
                              savedBarcodes.value.has(a.barcode)
                                ? (openBlock(),
                                  createElementBlock("span", L, "✓ 已补 · 今天已记录"))
                                : withDirectives(
                                    (openBlock(),
                                    createElementBlock(
                                      "input",
                                      {
                                        key: 1,
                                        class: "inline-input",
                                        "onUpdate:modelValue": (v) =>
                                          (priceInputs.value[a.barcode] = v),
                                        placeholder: "如 198.00",
                                        onKeyup: withKeys((v) => savePrice(a), ["enter"]),
                                      },
                                      null,
                                      40,
                                      P,
                                    )),
                                    [[vModelText, priceInputs.value[a.barcode]]],
                                  ),
                            ]),
                            createElementVNode("td", null, [
                              savedBarcodes.value.has(a.barcode)
                                ? createCommentVNode("", !0)
                                : (openBlock(),
                                  createElementBlock(
                                    "button",
                                    {
                                      key: 0,
                                      class: "btn sm",
                                      disabled: !unref(n).canWrite,
                                      onClick: (v) => savePrice(a),
                                    },
                                    "保存",
                                    8,
                                    z,
                                  )),
                            ]),
                          ],
                        )
                      ),
                    ),
                    128,
                  )),
                ]),
              ]),
              t[4] ||
                (t[4] = createElementVNode(
                  "div",
                  {
                    class: "tip-note",
                    style: {
                      margin: "12px 0 0",
                    },
                  },
                  "填完价格点保存即生效，改动自动记录到商品历史；价格写入经乐观锁 CAS 校验，避免并发覆盖。",
                  -1,
                )),
            ]),
          ])
        )
      );
    },
  };

export default FillPrice;
