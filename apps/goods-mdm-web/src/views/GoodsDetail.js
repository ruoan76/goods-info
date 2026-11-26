import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  withDirectives,
  vModelText,
  withKeys,
  toDisplayString,
  createTextVNode,
  normalizeClass,
  Fragment,
  unref,
  createCommentVNode,
  vShow,
  renderList,
  withModifiers,
  vModelSelect,
  createVNode,
  withCtx,
  ref,
  nextTick,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { goodsApi, errorMessage, categoryApi } from "../api.js";
import InfoBox from "../components/InfoBox.js";
import ConfirmDlg from "../components/ConfirmDlg.js";

const it = {
    key: 0,
  },
  ut = {
    class: "card",
  },
  rt = {
    class: "detail-head",
  },
  dt = {
    class: "bc",
  },
  vt = {
    key: 0,
  },
  pt = {
    class: "meta",
  },
  ct = {
    style: {
      display: "flex",
      gap: "8px",
      "align-items": "flex-start",
      "flex-wrap": "wrap",
    },
  },
  yt = {
    class: "tabs",
  },
  ft = {
    class: "tab-pane",
  },
  mt = {
    class: "kv",
    style: {
      "margin-top": "8px",
    },
  },
  gt = {
    style: {
      "font-family": "Menlo",
    },
  },
  kt = {
    key: 0,
  },
  bt = {
    key: 2,
  },
  Ct = {
    class: "sysinfo",
  },
  wt = {
    class: "tab-pane",
  },
  xt = {
    class: "tip-note",
  },
  _t = {
    class: "dyn-form",
    style: {
      display: "grid",
      "grid-template-columns": "1fr 1fr",
      gap: "0 24px",
    },
  },
  Vt = ["onUpdate:modelValue", "disabled"],
  $t = {
    key: 0,
    class: "fitem",
    style: {
      color: "var(--text3)",
    },
  },
  At = {
    class: "tab-pane",
  },
  Et = {
    key: 0,
    class: "empty-row",
    style: {
      padding: "24px 0",
      color: "var(--text3)",
      "text-align": "center",
    },
  },
  It = {
    class: "ht",
  },
  Tt = {
    key: 0,
    style: {
      color: "var(--text3)",
    },
  },
  Dt = {
    class: "hb",
  },
  Mt = {
    key: 0,
  },
  Nt = {
    class: "uf-box sm-box",
  },
  St = {
    class: "hd",
  },
  Ut = {
    class: "bd",
  },
  Ft = {
    class: "field",
  },
  Ot = ["value"],
  Wt = {
    class: "field",
  },
  Bt = ["value", "disabled"],
  Kt = {
    class: "ft",
  },
  zt = ["innerHTML"],
  Lt = {
    key: 1,
    class: "loading",
  },
  GoodsDetail = {
    name: "GoodsDetail",
    setup(Pt) {
      const n = useAppStore(),
        j = useRoute(),
        H = useRouter(),
        barcode = j.params.barcode,
        goods = ref(null),
        C = ref({}),
        p = ref("d1"),
        O = ref([]),
        editingField = ref(""),
        fieldValue = ref(""),
        w = ref(!1),
        $ = ref(""),
        T = ref({
          show: !1,
          title: "",
          html: "",
        }),
        k = ref({
          show: !1,
          title: "",
          message: "",
          action: null,
        });
      function W(l, t = []) {
        return (
          l.forEach((r) => {
            var e;
            t.push(r);
            (e = r.children) != null && e.length && W(r.children, t);
          }),
          t
        );
      }
      function B(l, t, r) {
        k.value = {
          show: !0,
          title: l,
          message: t,
          action: r,
        };
      }
      function R() {
        const l = k.value.action;
        k.value.show = !1;
        typeof l == "function" && l();
      }
      const K = (l) =>
          ({
            ACTIVE: "在售",
            INACTIVE: "已停用",
            VOIDED: "已作废",
          })[l] || l,
        z = (l) =>
          ({
            ACTIVE: "tg-green",
            INACTIVE: "tg-gray",
            VOIDED: "tg-red",
          })[l] || "tg-gray";
      const editInput = ref(null);
      let editingVersion;

      async function loadGoods() {
        try {
          goods.value = await goodsApi.detail(barcode);
          C.value = await goodsApi.getAttrs(barcode).catch(() => ({}));
          const l = await categoryApi.tree().catch(() => ({
            tree: [],
          }));
          O.value = l.tree || [];
        } catch (l) {
          n.toast(errorMessage(l), "err");
        }
      }
      async function startEditing(l, t) {
        var r;
        if (!n.canWrite) {
          n.toast("只读角色不能修改商品信息", "err");
          return;
        }
        if (((r = goods.value) == null ? void 0 : r.status) === "VOIDED") {
          n.toast("已作废商品不可修改", "err");
          return;
        }
        editingVersion = goods.value.version;
        editingField.value = l;
        fieldValue.value = t ?? "";
        await nextTick();
        editInput.value?.focus();
      }
      async function saveField(l) {
        const t = fieldValue.value.trim();
        editingField.value = "";
        try {
          await goodsApi.patch(barcode, l, t, "详情页即点即改", editingVersion);
          n.toast("已保存 · 改动已记录到历史", "ok");
          loadGoods();
        } catch (e) {
          n.toast(errorMessage(e), "err");
        }
      }
      function h() {
        var l;
        if (!n.canWrite) {
          n.toast("只读角色不能调整分类", "err");
          return;
        }
        $.value = ((l = goods.value) == null ? void 0 : l.category_id) || "";
        w.value = !0;
      }
      async function q() {
        if (!$.value) {
          n.toast("请选择目标分类", "err");
          return;
        }
        try {
          await goodsApi.changeCategory(barcode, $.value, "详情页调整分类");
          w.value = !1;
          n.toast("分类已调整 · 改动已记录到历史", "ok");
          loadGoods();
        } catch (l) {
          n.toast(errorMessage(l), "err");
        }
      }
      async function G() {
        if (!n.canWrite) {
          n.toast("只读角色不能修改属性", "err");
          return;
        }
        try {
          await goodsApi.putAttrs(barcode, C.value);
          n.toast("属性已保存 · 按分类模板校验必填项，逐字段留痕", "ok");
        } catch (l) {
          n.toast(errorMessage(l), "err");
        }
      }
      function L(l, t, r) {
        if (!n.isAdmin) {
          n.toast("仅管理员可停用/作废商品", "err");
          return;
        }
        B(t, r, async () => {
          try {
            await goodsApi.changeStatus(barcode, l, t);
            n.toast(`${t}成功`, "ok");
            loadGoods();
          } catch (e) {
            n.toast(errorMessage(e), "err");
          }
        });
      }
      function J() {
        B(
          "恢复商品为在售？",
          "恢复后商品重新对外使用，历史记录完整保留。",
          async () => {
            try {
              await goodsApi.changeStatus(barcode, "ACTIVE", "恢复在售");
              n.toast("已恢复在售", "ok");
              loadGoods();
            } catch (l) {
              n.toast(errorMessage(l), "err");
            }
          },
        );
      }
      return (
        onMounted(loadGoods),
        (l, t) => {
          var r;
          return goods.value
            ? (openBlock(),
              createElementBlock("div", it, [
                t[42] ||
                  (t[42] = createElementVNode(
                    "div",
                    {
                      class: "page-title",
                    },
                    "商品详情",
                    -1,
                  )),
                createElementVNode("div", ut, [
                  createElementVNode("div", rt, [
                    createElementVNode("div", null, [
                      createElementVNode("div", dt, [
                        editingField.value === "goods_name"
                          ? (openBlock(),
                            createElementBlock("span", vt, [
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    class: "inline-input",
                                    ref: editInput,
                                    "onUpdate:modelValue":
                                      t[0] ||
                                      (t[0] = (e) => (fieldValue.value = e)),
                                    onKeyup: [
                                      t[1] ||
                                        (t[1] = withKeys(
                                          (e) => saveField("goods_name"),
                                          ["enter"],
                                        )),
                                      t[2] ||
                                        (t[2] = withKeys(
                                          (e) => (editingField.value = ""),
                                          ["esc"],
                                        )),
                                    ],
                                    style: {
                                      width: "360px",
                                    },
                                  },
                                  null,
                                  544,
                                ),
                                [[vModelText, fieldValue.value]],
                              ),
                            ]))
                          : (openBlock(),
                            createElementBlock(
                              "span",
                              {
                                key: 1,
                                class: "editable",
                                onClick:
                                  t[3] ||
                                  (t[3] = (e) =>
                                    startEditing(
                                      "goods_name",
                                      goods.value.goods_name,
                                    )),
                                title: "点击修改名称",
                              },
                              toDisplayString(goods.value.goods_name),
                              1,
                            )),
                      ]),
                      createElementVNode("div", pt, [
                        createTextVNode(
                          "条码 " +
                            toDisplayString(goods.value.barcode) +
                            " · 分类：",
                          1,
                        ),
                        createElementVNode(
                          "span",
                          {
                            class: "editable",
                            onClick: h,
                            title: "点击调整分类",
                          },
                          toDisplayString(
                            goods.value.category_path || "未分类",
                          ),
                          1,
                        ),
                        t[24] ||
                          (t[24] = createTextVNode("（点分类可调整）", -1)),
                      ]),
                    ]),
                    createElementVNode("div", ct, [
                      createElementVNode(
                        "span",
                        {
                          class: normalizeClass(["tag", z(goods.value.status)]),
                          style: {
                            "font-size": "12px",
                            padding: "4px 12px",
                          },
                        },
                        toDisplayString(K(goods.value.status)),
                        3,
                      ),
                      goods.value.status === "ACTIVE"
                        ? (openBlock(),
                          createElementBlock(
                            Fragment,
                            {
                              key: 0,
                            },
                            [
                              unref(n).isAdmin
                                ? (openBlock(),
                                  createElementBlock(
                                    "button",
                                    {
                                      key: 0,
                                      class: "btn warn sm adm-only",
                                      onClick:
                                        t[4] ||
                                        (t[4] = (e) =>
                                          L(
                                            "INACTIVE",
                                            "停用这个商品？",
                                            "停用后商品不再对外使用，但记录完整保留，随时可以恢复。",
                                          )),
                                    },
                                    "停用",
                                  ))
                                : createCommentVNode("", !0),
                              unref(n).isAdmin
                                ? (openBlock(),
                                  createElementBlock(
                                    "button",
                                    {
                                      key: 1,
                                      class: "btn plain sm",
                                      onClick:
                                        t[5] ||
                                        (t[5] = (e) =>
                                          L(
                                            "VOIDED",
                                            "作废这个商品？",
                                            "作废不可逆，作废后条码 90 天内不能再次使用。",
                                          )),
                                    },
                                    "作废",
                                  ))
                                : createCommentVNode("", !0),
                            ],
                            64,
                          ))
                        : goods.value.status === "INACTIVE"
                          ? (openBlock(),
                            createElementBlock(
                              "button",
                              {
                                key: 1,
                                class: "btn sm",
                                onClick: J,
                              },
                              "恢复在售",
                            ))
                          : createCommentVNode("", !0),
                    ]),
                  ]),
                  createElementVNode("div", yt, [
                    createElementVNode(
                      "div",
                      {
                        class: normalizeClass([
                          "tab",
                          {
                            active: p.value === "d1",
                          },
                        ]),
                        onClick: t[6] || (t[6] = (e) => (p.value = "d1")),
                      },
                      "基本信息",
                      2,
                    ),
                    createElementVNode(
                      "div",
                      {
                        class: normalizeClass([
                          "tab",
                          {
                            active: p.value === "d3",
                          },
                        ]),
                        onClick: t[7] || (t[7] = (e) => (p.value = "d3")),
                      },
                      "商品属性",
                      2,
                    ),
                    createElementVNode(
                      "div",
                      {
                        class: normalizeClass([
                          "tab",
                          {
                            active: p.value === "d4",
                          },
                        ]),
                        onClick: t[8] || (t[8] = (e) => (p.value = "d4")),
                      },
                      "历史记录",
                      2,
                    ),
                  ]),
                  withDirectives(
                    createElementVNode(
                      "div",
                      ft,
                      [
                        createElementVNode("div", mt, [
                          t[25] ||
                            (t[25] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "条码",
                              -1,
                            )),
                          createElementVNode(
                            "span",
                            gt,
                            toDisplayString(goods.value.barcode) +
                              "（" +
                              toDisplayString(goods.value.barcode.length) +
                              " 位）",
                            1,
                          ),
                          t[26] ||
                            (t[26] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "状态",
                              -1,
                            )),
                          createElementVNode("span", null, [
                            createElementVNode(
                              "span",
                              {
                                class: normalizeClass([
                                  "tag",
                                  z(goods.value.status),
                                ]),
                              },
                              toDisplayString(K(goods.value.status)),
                              3,
                            ),
                          ]),
                          t[27] ||
                            (t[27] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "分类",
                              -1,
                            )),
                          createElementVNode(
                            "span",
                            null,
                            toDisplayString(
                              goods.value.category_path || "未分类",
                            ),
                            1,
                          ),
                          t[28] ||
                            (t[28] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "单位",
                              -1,
                            )),
                          createElementVNode(
                            "span",
                            null,
                            toDisplayString(goods.value.unit_id || "—"),
                            1,
                          ),
                          t[29] ||
                            (t[29] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "进价",
                              -1,
                            )),
                          editingField.value === "inprice"
                            ? (openBlock(),
                              createElementBlock("span", kt, [
                                withDirectives(
                                  createElementVNode(
                                    "input",
                                    {
                                      class: "inline-input",
                                      ref: editInput,
                                      "onUpdate:modelValue":
                                        t[9] ||
                                        (t[9] = (e) => (fieldValue.value = e)),
                                      onKeyup: [
                                        t[10] ||
                                          (t[10] = withKeys(
                                            (e) => saveField("inprice"),
                                            ["enter"],
                                          )),
                                        t[11] ||
                                          (t[11] = withKeys(
                                            (e) => (editingField.value = ""),
                                            ["esc"],
                                          )),
                                      ],
                                    },
                                    null,
                                    544,
                                  ),
                                  [[vModelText, fieldValue.value]],
                                ),
                              ]))
                            : (openBlock(),
                              createElementBlock(
                                "span",
                                {
                                  key: 1,
                                  class: "editable",
                                  onClick:
                                    t[12] ||
                                    (t[12] = (e) =>
                                      startEditing(
                                        "inprice",
                                        goods.value.inprice &&
                                          +goods.value.inprice,
                                      )),
                                },
                                "¥ " +
                                  toDisplayString(
                                    goods.value.inprice
                                      ? (+goods.value.inprice).toFixed(2)
                                      : "—",
                                  ),
                                1,
                              )),
                          t[30] ||
                            (t[30] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "售价",
                              -1,
                            )),
                          editingField.value === "outprice"
                            ? (openBlock(),
                              createElementBlock("span", bt, [
                                withDirectives(
                                  createElementVNode(
                                    "input",
                                    {
                                      class: "inline-input",
                                      ref: editInput,
                                      "onUpdate:modelValue":
                                        t[13] ||
                                        (t[13] = (e) => (fieldValue.value = e)),
                                      onKeyup: [
                                        t[14] ||
                                          (t[14] = withKeys(
                                            (e) => saveField("outprice"),
                                            ["enter"],
                                          )),
                                        t[15] ||
                                          (t[15] = withKeys(
                                            (e) => (editingField.value = ""),
                                            ["esc"],
                                          )),
                                      ],
                                    },
                                    null,
                                    544,
                                  ),
                                  [[vModelText, fieldValue.value]],
                                ),
                              ]))
                            : (openBlock(),
                              createElementBlock(
                                "span",
                                {
                                  key: 3,
                                  class: "editable",
                                  onClick:
                                    t[16] ||
                                    (t[16] = (e) =>
                                      startEditing(
                                        "outprice",
                                        goods.value.outprice &&
                                          +goods.value.outprice,
                                      )),
                                },
                                "¥ " +
                                  toDisplayString(
                                    goods.value.outprice
                                      ? (+goods.value.outprice).toFixed(2)
                                      : "—",
                                  ),
                                1,
                              )),
                          t[31] ||
                            (t[31] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "质量等级",
                              -1,
                            )),
                          createElementVNode(
                            "span",
                            null,
                            toDisplayString(goods.value.quality_grade || "—"),
                            1,
                          ),
                          t[32] ||
                            (t[32] = createElementVNode(
                              "span",
                              {
                                class: "k",
                              },
                              "版本",
                              -1,
                            )),
                          createElementVNode(
                            "span",
                            null,
                            "v" + toDisplayString(goods.value.version),
                            1,
                          ),
                        ]),
                        t[33] ||
                          (t[33] = createElementVNode(
                            "div",
                            {
                              class: "tip-note",
                              style: {
                                margin: "14px 0 0",
                              },
                            },
                            [
                              createTextVNode("带 ✎ 的字样"),
                              createElementVNode("b", null, "点一下就能改"),
                              createTextVNode(
                                "，改完回车保存，自动记录到历史；条码建档后不可修改。",
                              ),
                            ],
                            -1,
                          )),
                        createElementVNode(
                          "div",
                          Ct,
                          "数据来源：" +
                            toDisplayString(
                              goods.value.category_source || "—",
                            ) +
                            " · 最近更新 " +
                            toDisplayString(goods.value.updated_at || "—"),
                          1,
                        ),
                      ],
                      512,
                    ),
                    [[vShow, p.value === "d1"]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "div",
                      wt,
                      [
                        createElementVNode("div", xt, [
                          t[34] ||
                            (t[34] = createElementVNode(
                              "b",
                              null,
                              "商品属性",
                              -1,
                            )),
                          createTextVNode(
                            "：按「" +
                              toDisplayString(goods.value.category_path) +
                              "」分类的属性要求填写，带 ",
                            1,
                          ),
                          t[35] ||
                            (t[35] = createElementVNode(
                              "span",
                              {
                                style: {
                                  color: "var(--danger)",
                                },
                              },
                              "*",
                              -1,
                            )),
                          t[36] || (t[36] = createTextVNode(" 的为必填项", -1)),
                        ]),
                        createElementVNode("div", _t, [
                          (openBlock(!0),
                          createElementBlock(
                            Fragment,
                            null,
                            renderList(
                              C.value,
                              (e, x) => (
                                openBlock(),
                                createElementBlock(
                                  "div",
                                  {
                                    class: "fitem",
                                    key: x,
                                  },
                                  [
                                    createElementVNode(
                                      "label",
                                      null,
                                      toDisplayString(x),
                                      1,
                                    ),
                                    withDirectives(
                                      createElementVNode(
                                        "input",
                                        {
                                          "onUpdate:modelValue": (Q) =>
                                            (C.value[x] = Q),
                                          disabled: !unref(n).canWrite,
                                        },
                                        null,
                                        8,
                                        Vt,
                                      ),
                                      [[vModelText, C.value[x]]],
                                    ),
                                  ],
                                )
                              ),
                            ),
                            128,
                          )),
                          Object.keys(C.value).length
                            ? createCommentVNode("", !0)
                            : (openBlock(),
                              createElementBlock(
                                "div",
                                $t,
                                "该商品暂无属性；可按分类模板添加。",
                              )),
                          unref(n).canWrite
                            ? (openBlock(),
                              createElementBlock(
                                "button",
                                {
                                  key: 1,
                                  class: "btn sm",
                                  onClick: G,
                                },
                                "保存属性",
                              ))
                            : createCommentVNode("", !0),
                        ]),
                      ],
                      512,
                    ),
                    [[vShow, p.value === "d3"]],
                  ),
                  withDirectives(
                    createElementVNode(
                      "div",
                      At,
                      [
                        t[37] ||
                          (t[37] = createElementVNode(
                            "div",
                            {
                              class: "tip-note",
                            },
                            [
                              createTextVNode(
                                "本页展示这条商品的每次变动：谁、什么时候、改了什么（来自 ",
                              ),
                              createElementVNode(
                                "code",
                                null,
                                "/goods/{barcode}",
                              ),
                              createTextVNode(" 的 history）"),
                            ],
                            -1,
                          )),
                        (r = goods.value.history) != null && r.length
                          ? createCommentVNode("", !0)
                          : (openBlock(),
                            createElementBlock("div", Et, "暂无历史记录")),
                        (openBlock(!0),
                        createElementBlock(
                          Fragment,
                          null,
                          renderList(
                            goods.value.history,
                            (e, x) => (
                              openBlock(),
                              createElementBlock(
                                "div",
                                {
                                  class: "history-item",
                                  key: x,
                                },
                                [
                                  createElementVNode("div", It, [
                                    createTextVNode(
                                      toDisplayString(
                                        e.changed_at || e.created_at || "",
                                      ) +
                                        " · " +
                                        toDisplayString(e.operator || "系统") +
                                        " ",
                                      1,
                                    ),
                                    e.batch_id
                                      ? (openBlock(),
                                        createElementBlock(
                                          "span",
                                          Tt,
                                          "[" +
                                            toDisplayString(e.batch_id) +
                                            "]",
                                          1,
                                        ))
                                      : createCommentVNode("", !0),
                                  ]),
                                  createElementVNode("div", Dt, [
                                    createTextVNode(
                                      toDisplayString(
                                        e.field_name || e.action,
                                      ) + "：",
                                      1,
                                    ),
                                    e.old_value
                                      ? (openBlock(),
                                        createElementBlock(
                                          "span",
                                          Mt,
                                          toDisplayString(e.old_value) + " → ",
                                          1,
                                        ))
                                      : createCommentVNode("", !0),
                                    createTextVNode(
                                      toDisplayString(e.new_value),
                                      1,
                                    ),
                                  ]),
                                ],
                              )
                            ),
                          ),
                          128,
                        )),
                      ],
                      512,
                    ),
                    [[vShow, p.value === "d4"]],
                  ),
                ]),
                createElementVNode(
                  "button",
                  {
                    class: "btn plain sm",
                    onClick: t[17] || (t[17] = (e) => unref(H).push("/goods")),
                  },
                  "← 返回商品档案",
                ),
                w.value
                  ? (openBlock(),
                    createElementBlock(
                      "div",
                      {
                        key: 0,
                        class: "mask",
                        onClick:
                          t[21] ||
                          (t[21] = withModifiers(
                            (e) => (w.value = !1),
                            ["self"],
                          )),
                      },
                      [
                        createElementVNode("div", Nt, [
                          createElementVNode("div", St, [
                            t[38] ||
                              (t[38] = createElementVNode(
                                "span",
                                null,
                                "调整商品分类",
                                -1,
                              )),
                            createElementVNode(
                              "span",
                              {
                                class: "x",
                                onClick:
                                  t[18] || (t[18] = (e) => (w.value = !1)),
                              },
                              "✕",
                            ),
                          ]),
                          createElementVNode("div", Ut, [
                            createElementVNode("div", Ft, [
                              t[39] ||
                                (t[39] = createElementVNode(
                                  "label",
                                  null,
                                  "当前分类",
                                  -1,
                                )),
                              createElementVNode(
                                "input",
                                {
                                  value: goods.value.category_path,
                                  disabled: "",
                                  style: {
                                    background: "#f5f7fa",
                                  },
                                },
                                null,
                                8,
                                Ot,
                              ),
                            ]),
                            createElementVNode("div", Wt, [
                              t[40] ||
                                (t[40] = createElementVNode(
                                  "label",
                                  null,
                                  [
                                    createTextVNode("调整为 "),
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
                                      t[19] || (t[19] = (e) => ($.value = e)),
                                  },
                                  [
                                    (openBlock(!0),
                                    createElementBlock(
                                      Fragment,
                                      null,
                                      renderList(
                                        W(O.value),
                                        (e) => (
                                          openBlock(),
                                          createElementBlock(
                                            "option",
                                            {
                                              key: e.category_id,
                                              value: e.category_id,
                                              disabled: e.is_placeholder,
                                            },
                                            toDisplayString(e.name),
                                            9,
                                            Bt,
                                          )
                                        ),
                                      ),
                                      128,
                                    )),
                                  ],
                                  512,
                                ),
                                [[vModelSelect, $.value]],
                              ),
                            ]),
                            t[41] ||
                              (t[41] = createElementVNode(
                                "div",
                                {
                                  class: "hint",
                                  style: {
                                    "font-size": "11px",
                                    color: "var(--text3)",
                                  },
                                },
                                "调整后按新分类校验属性必填项；改动记录到历史",
                                -1,
                              )),
                          ]),
                          createElementVNode("div", Kt, [
                            createElementVNode(
                              "button",
                              {
                                class: "btn plain sm",
                                onClick:
                                  t[20] || (t[20] = (e) => (w.value = !1)),
                              },
                              "取消",
                            ),
                            createElementVNode(
                              "button",
                              {
                                class: "btn sm",
                                onClick: q,
                              },
                              "确认调整",
                            ),
                          ]),
                        ]),
                      ],
                    ))
                  : createCommentVNode("", !0),
                createVNode(
                  ConfirmDlg,
                  {
                    show: k.value.show,
                    title: k.value.title,
                    message: k.value.message,
                    onConfirm: R,
                    onCancel: t[22] || (t[22] = (e) => (k.value.show = !1)),
                  },
                  null,
                  8,
                  ["show", "title", "message"],
                ),
                createVNode(
                  InfoBox,
                  {
                    show: T.value.show,
                    title: T.value.title,
                    onClose: t[23] || (t[23] = (e) => (T.value.show = !1)),
                  },
                  {
                    default: withCtx(() => [
                      createElementVNode(
                        "div",
                        {
                          innerHTML: DOMPurify.sanitize(T.value.html),
                        },
                        null,
                        8,
                        zt,
                      ),
                    ]),
                    _: 1,
                  },
                  8,
                  ["show", "title"],
                ),
              ]))
            : (openBlock(), createElementBlock("div", Lt, "加载中…"));
        }
      );
    },
  };

export default GoodsDetail;
