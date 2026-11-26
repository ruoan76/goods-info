import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  normalizeClass,
  withDirectives,
  vShow,
  createTextVNode,
  withKeys,
  vModelText,
  toDisplayString,
  normalizeStyle,
  createCommentVNode,
  Fragment,
  renderList,
  vModelSelect,
  createVNode,
  withCtx,
  ref,
} from "vue";
import { goodsApi, errorMessage, categoryApi } from "../api.js";
import { useRouter, useRoute } from "vue-router";
import InfoBox from "../components/InfoBox.js";

const de = {
    class: "tabs",
    style: {
      "margin-top": "0",
    },
  },
  ve = {
    style: {
      "padding-top": "16px",
    },
  },
  pe = {
    class: "card",
  },
  ce = {
    class: "dyn-form",
    style: {
      display: "grid",
      "grid-template-columns": "1fr 1fr",
      gap: "0 24px",
      "max-width": "720px",
    },
  },
  me = {
    class: "fitem",
  },
  be = {
    class: "fitem",
  },
  fe = ["disabled"],
  ge = {
    key: 0,
    style: {
      "margin-top": "14px",
    },
  },
  ye = {
    style: {
      "font-size": "12.5px",
      "line-height": "1.9",
    },
  },
  xe = {
    key: 0,
    style: {
      "font-size": "11.5px",
      color: "var(--text3)",
    },
  },
  _e = {
    style: {
      "font-size": "11.5px",
    },
  },
  Ce = {
    key: 0,
  },
  we = {
    class: "card",
  },
  ke = {
    class: "dyn-form",
    style: {
      display: "grid",
      "grid-template-columns": "1fr 1fr",
      gap: "0 24px",
      "max-width": "720px",
    },
  },
  he = {
    class: "fitem",
  },
  Ve = {
    class: "fitem",
  },
  Se = ["value"],
  $e = {
    class: "fitem",
  },
  qe = {
    class: "fitem",
  },
  Ue = {
    class: "fitem",
  },
  Le = {
    class: "fitem",
  },
  je = ["disabled"],
  Be = {
    style: {
      "padding-top": "16px",
    },
  },
  Re = {
    class: "card",
  },
  Ne = {
    style: {
      display: "flex",
      gap: "10px",
      margin: "14px 0",
      "flex-wrap": "wrap",
    },
  },
  Me = ["disabled"],
  Te = ["innerHTML"],
  GoodsNew = {
    name: "GoodsNew",
    setup(Oe) {
      const d = useAppStore(),
        D = useRouter(),
        F = useRoute(),
        y = ref("single"),
        m = ref(""),
        b = ref(""),
        h = ref(!1),
        o = ref(null),
        C = ref(!1),
        s = ref({
          goods_name: "",
          category_id: "",
          unit_id: "",
          inprice: "",
          outprice: "",
          quality_grade: "C",
        }),
        w = ref(!1),
        B = ref([]),
        V = ref(null),
        k = ref(!1),
        H = ref(null),
        x = ref({
          show: !1,
          title: "",
          html: "",
        });
      function R(l, e) {
        x.value = {
          show: !0,
          title: l,
          html: e,
        };
      }
      async function W() {
        try {
          const l = await categoryApi.tree(),
            e = [],
            i = (c) =>
              c.forEach((p) => {
                !p.is_placeholder &&
                  p.is_leaf &&
                  e.push({
                    id: p.category_id,
                    name: p.name,
                  });
                i(p.children || []);
              });
          i(l.tree || []);
          B.value = e;
        } catch {}
      }
      async function N() {
        if (!m.value.trim() || !b.value.trim()) {
          d.toast("条码和商品名称都要填，才能完成两路查重", "err");
          return;
        }
        C.value = !0;
        try {
          const l = await goodsApi.check(m.value.trim(), b.value.trim());
          o.value = l;
          h.value = !0;
          s.value.goods_name = b.value.trim();
        } catch (l) {
          d.toast(errorMessage(l), "err");
        } finally {
          C.value = !1;
        }
      }
      const M = {
        PASS: {
          cls: "ok",
          text: "✓ 两路查重通过（条码无重复、无同名），可填写档案",
        },
        WARN: {
          cls: "warn",
          text: "⚠ 存在相似商品名，请先人工核对是否一码多品/同名多码，确认无误后方可继续",
        },
        BLOCK: {
          cls: "err",
          text: "✗ 条码已被占用，不能重复建档，请改为维护原档案",
        },
      };
      async function P() {
        if (!o.value || o.value.verdict === "BLOCK") {
          d.toast("查重未通过，不能建档", "err");
          return;
        }
        if (!s.value.category_id) {
          d.toast("请选择分类", "err");
          return;
        }
        w.value = !0;
        try {
          const l = {
            barcode: m.value.trim(),
            goods_name: s.value.goods_name,
            category_id: s.value.category_id,
            unit_id: s.value.unit_id || null,
            inprice: s.value.inprice || null,
            outprice: s.value.outprice || null,
            quality_grade: s.value.quality_grade,
          };
          await goodsApi.create(l);
          d.toast(`建档成功 ·「${s.value.goods_name}」已留存，条码不可改，变更已留痕`, "ok");
          h.value = !1;
          o.value = null;
          m.value = "";
          b.value = "";
          s.value = {
            goods_name: "",
            category_id: "",
            unit_id: "",
            inprice: "",
            outprice: "",
            quality_grade: "C",
          };
        } catch (l) {
          d.toast(errorMessage(l), "err");
        } finally {
          w.value = !1;
        }
      }
      function J() {
        const l = `条码,商品名称,分类ID,单位,进价,售价,等级
6901234567890,新品名称,C0203,000007,100,150,C
`,
          e = document.createElement("a");
        e.href = URL.createObjectURL(
          new Blob(["\uFEFF" + l], {
            type: "text/csv",
          }),
        );
        e.download = "goods_import_template.csv";
        e.click();
        URL.revokeObjectURL(e.href);
        d.toast("CSV 模板已下载", "ok");
      }
      function Q() {
        R(
          "批量导入说明",
          `<div class="result-line"><b>四步走：</b>① 下载 CSV 模板 → ② 按模板填写 → ③ 上传校验（500 行/批事务）→ ④ 查失败清单修正重传</div>
     <ul style="margin-left:18px"><li><b>字段要求</b>：条码/名称/分类必填；条码 8 或 13 位，书号（978/979）不收</li>
     <li><b>查重规则</b>：两段式（条码命中 BLOCK 禁止、同名命中 WARN 需人工确认），建档后条码不可改</li>
     <li><b>失败处理</b>：单批失败整体回滚并输出失败行清单，可查 <code>GET /admin/import-jobs/{id}</code></li></ul>`,
        );
      }
      async function X() {
        var l, e;
        if (!V.value) {
          d.toast("请先选择 CSV 文件", "err");
          return;
        }
        k.value = !0;
        try {
          const i = await goodsApi.importCsv(V.value);
          H.value = i;
          R(
            "上传校验结果",
            `<div class="result-line ok"><b>✓ 导入完成</b>　job_id：${i.job_id || "—"}</div>
       <div class="result-line ok">成功 <b>${i.success ?? 0}</b> 行　→ 已按 500 行/批事务写入</div>
       <div class="result-line ${((l = i.failures) != null && l.length) || i.failed ? "err" : "ok"}">失败 <b>${i.failed ?? ((e = i.failures) == null ? void 0 : e.length) ?? 0}</b> 行</div>
       ${(i.failures || [])
         .slice(0, 10)
         .map((c) => `<div class="result-line err">第 ${c.row} 行：${c.reason}</div>`)
         .join("")}
       <p style="margin-top:12px">进度与失败清单：<code>GET /api/v1/admin/import-jobs/${i.job_id || "{id}"}</code></p>`,
          );
        } catch (i) {
          d.toast(errorMessage(i), "err");
        } finally {
          k.value = !1;
        }
      }
      function Y(l) {
        var e;
        V.value = ((e = l.target.files) == null ? void 0 : e[0]) || null;
      }
      onMounted(() => {
        W();
        F.query.tab === "batch" && S("batch");
      });
      function S(l) {
        y.value = l;
        D.replace({
          path: "/goods/new",
          query:
            l === "batch"
              ? {
                  tab: "batch",
                }
              : {},
        });
      }
      return (l, e) => {
        var i, c, p, T, O, z, A, K, E;
        return (
          openBlock(),
          createElementBlock("div", null, [
            e[33] ||
              (e[33] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "新增商品",
                -1,
              )),
            e[34] ||
              (e[34] = createElementVNode(
                "div",
                {
                  class: "page-desc",
                },
                "任何渠道新增都必须先查重 · 条码建档后不可修改 · 每次改动必留痕",
                -1,
              )),
            createElementVNode("div", de, [
              createElementVNode(
                "div",
                {
                  class: normalizeClass([
                    "tab",
                    {
                      active: y.value === "single",
                    },
                  ]),
                  onClick: e[0] || (e[0] = (a) => S("single")),
                },
                "单条建档",
                2,
              ),
              createElementVNode(
                "div",
                {
                  class: normalizeClass([
                    "tab",
                    {
                      active: y.value === "batch",
                    },
                  ]),
                  onClick: e[1] || (e[1] = (a) => S("batch")),
                },
                "批量导入（CSV）",
                2,
              ),
            ]),
            withDirectives(
              createElementVNode(
                "div",
                ve,
                [
                  createElementVNode("div", pe, [
                    e[16] ||
                      (e[16] = createElementVNode(
                        "h3",
                        null,
                        [
                          createTextVNode("第一步 · 两段式查重 "),
                          createElementVNode(
                            "span",
                            {
                              class: "tag tg-blue",
                            },
                            "系统强制",
                          ),
                        ],
                        -1,
                      )),
                    e[17] ||
                      (e[17] = createElementVNode(
                        "div",
                        {
                          class: "tip-note",
                        },
                        [
                          createTextVNode("录入条码与商品名称，系统自动做两路查重："),
                          createElementVNode("b", null, "条码命中"),
                          createTextVNode(" + "),
                          createElementVNode("b", null, "同名命中"),
                          createTextVNode("。命中已有商品则不允许重复建档。"),
                        ],
                        -1,
                      )),
                    createElementVNode("div", ce, [
                      createElementVNode("div", me, [
                        e[11] ||
                          (e[11] = createElementVNode(
                            "label",
                            null,
                            [
                              createTextVNode("商品条码 "),
                              createElementVNode(
                                "span",
                                {
                                  class: "req",
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
                              "onUpdate:modelValue": e[2] || (e[2] = (a) => (m.value = a)),
                              style: {
                                "font-family": "ui-monospace,Menlo,monospace",
                              },
                              placeholder: "13 位或 8 位商品条码",
                              onKeyup: withKeys(N, ["enter"]),
                            },
                            null,
                            544,
                          ),
                          [[vModelText, m.value]],
                        ),
                      ]),
                      createElementVNode("div", be, [
                        e[12] ||
                          (e[12] = createElementVNode(
                            "label",
                            null,
                            [
                              createTextVNode("商品名称 "),
                              createElementVNode(
                                "span",
                                {
                                  class: "req",
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
                              "onUpdate:modelValue": e[3] || (e[3] = (a) => (b.value = a)),
                              placeholder: "用于同名命中比对，如 青岛啤酒经典1903",
                            },
                            null,
                            512,
                          ),
                          [[vModelText, b.value]],
                        ),
                      ]),
                    ]),
                    createElementVNode(
                      "button",
                      {
                        class: "btn sm",
                        disabled: C.value,
                        onClick: N,
                      },
                      toDisplayString(C.value ? "查重中…" : "开始查重"),
                      9,
                      fe,
                    ),
                    o.value
                      ? (openBlock(),
                        createElementBlock("div", ge, [
                          createElementVNode("div", ye, [
                            createElementVNode("div", null, [
                              e[13] || (e[13] = createTextVNode("① 条码命中：", -1)),
                              createElementVNode(
                                "b",
                                {
                                  style: normalizeStyle({
                                    color:
                                      (i = o.value.barcode_hit) != null && i.hit
                                        ? "var(--danger)"
                                        : "var(--success)",
                                  }),
                                },
                                toDisplayString(
                                  (c = o.value.barcode_hit) != null && c.hit
                                    ? "✗ 已存在"
                                    : "✓ 无重复",
                                ),
                                5,
                              ),
                            ]),
                            createElementVNode("div", null, [
                              e[14] || (e[14] = createTextVNode("② 同名命中：", -1)),
                              createElementVNode(
                                "b",
                                {
                                  style: normalizeStyle({
                                    color:
                                      (p = o.value.name_hit) != null && p.hit
                                        ? "var(--warning)"
                                        : "var(--success)",
                                  }),
                                },
                                toDisplayString(
                                  (T = o.value.name_hit) != null && T.hit
                                    ? "⚠ 有相似名称（" + o.value.name_hit.similar_count + " 条）"
                                    : "✓ 无同名",
                                ),
                                5,
                              ),
                            ]),
                            (z = (O = o.value.name_hit) == null ? void 0 : O.sample) != null &&
                            z.length
                              ? (openBlock(),
                                createElementBlock(
                                  "div",
                                  xe,
                                  "样本：" +
                                    toDisplayString(
                                      o.value.name_hit.sample.slice(0, 3).join(" / "),
                                    ),
                                  1,
                                ))
                              : createCommentVNode("", !0),
                          ]),
                          createElementVNode(
                            "div",
                            {
                              class: normalizeClass([
                                "result-line",
                                (A = M[o.value.verdict]) == null ? void 0 : A.cls,
                              ]),
                              style: {
                                "margin-top": "8px",
                              },
                            },
                            [
                              createElementVNode(
                                "b",
                                null,
                                toDisplayString((K = M[o.value.verdict]) == null ? void 0 : K.text),
                                1,
                              ),
                              e[15] || (e[15] = createElementVNode("br", null, null, -1)),
                              createElementVNode("span", _e, toDisplayString(o.value.reason), 1),
                            ],
                            2,
                          ),
                        ]))
                      : createCommentVNode("", !0),
                  ]),
                  h.value && ((E = o.value) == null ? void 0 : E.verdict) !== "BLOCK"
                    ? (openBlock(),
                      createElementBlock("div", Ce, [
                        createElementVNode("div", we, [
                          e[27] ||
                            (e[27] = createElementVNode(
                              "h3",
                              null,
                              [
                                createTextVNode("第二步 · 填写档案 "),
                                createElementVNode(
                                  "span",
                                  {
                                    class: "tag tg-green",
                                  },
                                  "查重通过",
                                ),
                              ],
                              -1,
                            )),
                          createElementVNode("div", ke, [
                            createElementVNode("div", he, [
                              e[18] ||
                                (e[18] = createElementVNode(
                                  "label",
                                  null,
                                  [
                                    createTextVNode("商品名称 "),
                                    createElementVNode(
                                      "span",
                                      {
                                        class: "req",
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
                                      e[4] || (e[4] = (a) => (s.value.goods_name = a)),
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, s.value.goods_name]],
                              ),
                            ]),
                            createElementVNode("div", Ve, [
                              e[20] ||
                                (e[20] = createElementVNode(
                                  "label",
                                  null,
                                  [
                                    createTextVNode("分类 "),
                                    createElementVNode(
                                      "span",
                                      {
                                        class: "req",
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
                                      e[5] || (e[5] = (a) => (s.value.category_id = a)),
                                  },
                                  [
                                    e[19] ||
                                      (e[19] = createElementVNode(
                                        "option",
                                        {
                                          value: "",
                                        },
                                        "请选择分类",
                                        -1,
                                      )),
                                    (openBlock(!0),
                                    createElementBlock(
                                      Fragment,
                                      null,
                                      renderList(
                                        B.value,
                                        (a) => (
                                          openBlock(),
                                          createElementBlock(
                                            "option",
                                            {
                                              key: a.id,
                                              value: a.id,
                                            },
                                            toDisplayString(a.name),
                                            9,
                                            Se,
                                          )
                                        ),
                                      ),
                                      128,
                                    )),
                                  ],
                                  512,
                                ),
                                [[vModelSelect, s.value.category_id]],
                              ),
                            ]),
                            createElementVNode("div", $e, [
                              e[22] || (e[22] = createElementVNode("label", null, "单位", -1)),
                              withDirectives(
                                createElementVNode(
                                  "select",
                                  {
                                    "onUpdate:modelValue":
                                      e[6] || (e[6] = (a) => (s.value.unit_id = a)),
                                  },
                                  [
                                    ...(e[21] ||
                                      (e[21] = [
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "",
                                          },
                                          "不指定",
                                          -1,
                                        ),
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "000007",
                                          },
                                          "箱（000007）",
                                          -1,
                                        ),
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "000002",
                                          },
                                          "瓶（000002）",
                                          -1,
                                        ),
                                        createElementVNode(
                                          "option",
                                          {
                                            value: "000003",
                                          },
                                          "盒（000003）",
                                          -1,
                                        ),
                                      ])),
                                  ],
                                  512,
                                ),
                                [[vModelSelect, s.value.unit_id]],
                              ),
                            ]),
                            createElementVNode("div", qe, [
                              e[24] || (e[24] = createElementVNode("label", null, "质量等级", -1)),
                              withDirectives(
                                createElementVNode(
                                  "select",
                                  {
                                    "onUpdate:modelValue":
                                      e[7] || (e[7] = (a) => (s.value.quality_grade = a)),
                                  },
                                  [
                                    ...(e[23] ||
                                      (e[23] = [
                                        createElementVNode("option", null, "A", -1),
                                        createElementVNode("option", null, "B", -1),
                                        createElementVNode("option", null, "C", -1),
                                      ])),
                                  ],
                                  512,
                                ),
                                [[vModelSelect, s.value.quality_grade]],
                              ),
                            ]),
                            createElementVNode("div", Ue, [
                              e[25] ||
                                (e[25] = createElementVNode("label", null, "进价（元）", -1)),
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    "onUpdate:modelValue":
                                      e[8] || (e[8] = (a) => (s.value.inprice = a)),
                                    type: "number",
                                    min: "0",
                                    placeholder: "0.00",
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, s.value.inprice]],
                              ),
                            ]),
                            createElementVNode("div", Le, [
                              e[26] ||
                                (e[26] = createElementVNode("label", null, "售价（元）", -1)),
                              withDirectives(
                                createElementVNode(
                                  "input",
                                  {
                                    "onUpdate:modelValue":
                                      e[9] || (e[9] = (a) => (s.value.outprice = a)),
                                    type: "number",
                                    min: "0",
                                    placeholder: "0.00",
                                  },
                                  null,
                                  512,
                                ),
                                [[vModelText, s.value.outprice]],
                              ),
                            ]),
                          ]),
                          e[28] ||
                            (e[28] = createElementVNode(
                              "div",
                              {
                                class: "tip-note warn",
                                style: {
                                  margin: "6px 0 12px",
                                },
                              },
                              "条码建档后不可修改。请确认条码与名称准确；信息填错可在详情页变更，但条码终身不变。",
                              -1,
                            )),
                          createElementVNode(
                            "button",
                            {
                              class: "btn",
                              disabled: w.value,
                              onClick: P,
                            },
                            toDisplayString(w.value ? "建档中…" : "确认建档"),
                            9,
                            je,
                          ),
                        ]),
                      ]))
                    : createCommentVNode("", !0),
                ],
                512,
              ),
              [[vShow, y.value === "single"]],
            ),
            withDirectives(
              createElementVNode(
                "div",
                Be,
                [
                  createElementVNode("div", Re, [
                    e[29] ||
                      (e[29] = createElementVNode(
                        "h3",
                        null,
                        [
                          createTextVNode("批量导入商品 "),
                          createElementVNode(
                            "span",
                            {
                              class: "tag tg-blue",
                            },
                            "新品引进主通道",
                          ),
                        ],
                        -1,
                      )),
                    e[30] ||
                      (e[30] = createElementVNode(
                        "div",
                        {
                          class: "tip-note",
                        },
                        "432 万量级的主数据，批量录入请用 CSV 模板。系统按模板逐行校验、自动查重、写来源标记，500 行/批事务处理。",
                        -1,
                      )),
                    createElementVNode("div", Ne, [
                      createElementVNode(
                        "button",
                        {
                          class: "btn plain sm",
                          onClick: J,
                        },
                        "下载 CSV 模板",
                      ),
                      createElementVNode(
                        "button",
                        {
                          class: "btn plain sm",
                          onClick: Q,
                        },
                        "导入说明",
                      ),
                      createElementVNode(
                        "input",
                        {
                          type: "file",
                          accept: ".csv",
                          onChange: Y,
                          style: {
                            height: "32px",
                          },
                        },
                        null,
                        32,
                      ),
                      createElementVNode(
                        "button",
                        {
                          class: "btn sm",
                          disabled: k.value,
                          onClick: X,
                        },
                        toDisplayString(k.value ? "导入中…" : "上传并校验"),
                        9,
                        Me,
                      ),
                    ]),
                    e[31] ||
                      (e[31] = createElementVNode(
                        "div",
                        {
                          style: {
                            border: "1px dashed var(--border)",
                            "border-radius": "6px",
                            padding: "22px",
                            "text-align": "center",
                            color: "var(--text3)",
                            "font-size": "12.5px",
                          },
                        },
                        " 选择填写好的 CSV 文件，点「上传并校验」提交 · 重复条码与同名冲突行进入失败清单，不覆盖已有档案 ",
                        -1,
                      )),
                    e[32] ||
                      (e[32] = createElementVNode(
                        "div",
                        {
                          class: "tip-note",
                          style: {
                            margin: "14px 0 0",
                          },
                        },
                        "导入结果：成功 / 失败逐行反馈 · 全部改动留痕可追溯",
                        -1,
                      )),
                  ]),
                ],
                512,
              ),
              [[vShow, y.value === "batch"]],
            ),
            createVNode(
              InfoBox,
              {
                show: x.value.show,
                title: x.value.title,
                onClose: e[10] || (e[10] = (a) => (x.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(x.value.html),
                    },
                    null,
                    8,
                    Te,
                  ),
                ]),
                _: 1,
              },
              8,
              ["show", "title"],
            ),
          ])
        );
      };
    },
  };

export default GoodsNew;
