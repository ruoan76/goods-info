import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  openBlock,
  createElementBlock,
  createElementVNode,
  withDirectives,
  vModelText,
  withKeys,
  toDisplayString,
  createTextVNode,
  vModelSelect,
  createVNode,
  withCtx,
  ref,
} from "vue";
import { barcodeApi, errorMessage } from "../api.js";
import InfoBox from "../components/InfoBox.js";

const O = {
    class: "card",
  },
  U = {
    class: "filter-row",
  },
  D = ["disabled"],
  P = {
    class: "card",
  },
  A = ["disabled"],
  H = {
    class: "filter-row",
  },
  K = ["innerHTML"],
  Barcode = {
    name: "Barcode",
    setup(L) {
      const i = useAppStore(),
        o = ref("6901035623162"),
        u = ref(!1),
        n = ref("6904444555566"),
        r = ref("6905555666677"),
        p = ref("换码（旧码换新码）"),
        c = ref(!1),
        d = ref({
          show: !1,
          title: "",
          html: "",
        });
      function b(l, e) {
        d.value = {
          show: !0,
          title: l,
          html: e,
        };
      }
      async function w() {
        if (!o.value.trim()) {
          i.toast("请输入条码", "err");
          return;
        }
        u.value = !0;
        try {
          const l = await barcodeApi.validate(o.value.trim()),
            e = (x, $) => `<div class="result-line ${x ? "ok" : "warn"}">${$}</div>`;
          let t = "";
          t += e(
            l.format_ok,
            `${l.format_ok ? "✓" : "✗"} 条码格式（${l.is_isbn ? "书号" : "8/13 位商品条码"}）`,
          );
          l.is_isbn && (t += e(!1, "⚠ 这是书号（978/979 开头），不是商品条码，不予收录"));
          t += e(
            !l.in_ban_period,
            `${l.in_ban_period ? "✗ 在作废 90 天禁复用期内" : "✓ 无使用限制（不在作废 90 天禁复用期内）"}`,
          );
          t += e(
            !l.alias_reverse,
            l.alias_reverse ? "⚠ 已归并到其他主条码" : "✓ 未归并到其他主条码",
          );
          t += e(
            !l.barcode_exist,
            l.barcode_exist ? "⚠ 该条码已有商品，不能重复建档" : "✓ 未被占用",
          );
          t += `<div class="result-line ${l.allowed ? "ok" : "err"}"><b>${l.allowed ? "✓ 允许建档" : "✗ 不允许建档"}</b></div>`;
          t +=
            "<p>来源：<code>POST /api/v1/barcodes/validate</code>（格式 + 禁复用期 + 别名反向 + 书号识别）</p>";
          b("条码检查结果 · " + o.value, t);
        } catch (l) {
          i.toast(errorMessage(l), "err");
        } finally {
          u.value = !1;
        }
      }
      async function k() {
        if (!i.isAdmin) {
          i.toast("仅管理员可提交换码", "err");
          return;
        }
        if (!n.value.trim() || !r.value.trim()) {
          i.toast("旧条码与新主条码都要填", "err");
          return;
        }
        c.value = !0;
        try {
          const l = await barcodeApi.reassign(n.value.trim(), r.value.trim(), p.value);
          b(
            "换码登记 · 已提交",
            `<div class="result-line ok"><b>✓ 换码已登记</b>　POST <code>/api/v1/barcodes/reassign</code></div>
       <div class="drow"><span class="k">旧条码</span><span class="v" style="font-family:Menlo">${n.value}</span></div>
       <div class="drow"><span class="k">新主条码</span><span class="v" style="font-family:Menlo">${r.value}</span></div>
       <div class="result-line warn" style="margin-top:10px">⏳ 旧条码已登记为「旧码」，<b>90 天内不能被其他商品使用</b>（自动锁定，到期解锁）</div>
       ${l ? `<pre>${JSON.stringify(l, null, 2)}</pre>` : ""}`,
          );
        } catch (l) {
          i.toast(errorMessage(l), "err");
        } finally {
          c.value = !1;
        }
      }
      return (l, e) => (
        openBlock(),
        createElementBlock("div", null, [
          e[10] ||
            (e[10] = createElementVNode(
              "div",
              {
                class: "page-title",
              },
              "条码管理",
              -1,
            )),
          e[11] ||
            (e[11] = createElementVNode(
              "div",
              {
                class: "page-desc",
              },
              "条码检查 · 换码登记 · 多包装条码归并 · 面向管理员",
              -1,
            )),
          createElementVNode("div", O, [
            e[5] || (e[5] = createElementVNode("h3", null, "条码检查", -1)),
            createElementVNode("div", U, [
              withDirectives(
                createElementVNode(
                  "input",
                  {
                    style: {
                      width: "240px",
                    },
                    "onUpdate:modelValue": e[0] || (e[0] = (t) => (o.value = t)),
                    placeholder: "输入条码",
                    onKeyup: withKeys(w, ["enter"]),
                  },
                  null,
                  544,
                ),
                [[vModelText, o.value]],
              ),
              createElementVNode(
                "button",
                {
                  class: "btn sm",
                  disabled: u.value,
                  onClick: w,
                },
                toDisplayString(u.value ? "检查中…" : "检查"),
                9,
                D,
              ),
            ]),
            e[6] ||
              (e[6] = createElementVNode(
                "div",
                {
                  class: "tip-note",
                },
                "系统自动检查 4 项：① 条码格式（8 或 13 位）② 使用限制期（作废后 90 天禁复用）③ 是否已归并到主条码 ④ 是否为书号",
                -1,
              )),
          ]),
          createElementVNode("div", P, [
            createElementVNode("h3", null, [
              e[7] || (e[7] = createTextVNode("换码登记 ", -1)),
              createElementVNode(
                "button",
                {
                  class: "btn plain sm",
                  disabled: c.value,
                  onClick: k,
                },
                "提交换码",
                8,
                A,
              ),
            ]),
            createElementVNode("div", H, [
              withDirectives(
                createElementVNode(
                  "input",
                  {
                    style: {
                      width: "180px",
                    },
                    "onUpdate:modelValue": e[1] || (e[1] = (t) => (n.value = t)),
                    placeholder: "旧条码",
                  },
                  null,
                  512,
                ),
                [[vModelText, n.value]],
              ),
              e[9] ||
                (e[9] = createElementVNode(
                  "span",
                  {
                    style: {
                      color: "var(--text3)",
                    },
                  },
                  "→",
                  -1,
                )),
              withDirectives(
                createElementVNode(
                  "input",
                  {
                    style: {
                      width: "180px",
                    },
                    "onUpdate:modelValue": e[2] || (e[2] = (t) => (r.value = t)),
                    placeholder: "新主条码",
                  },
                  null,
                  512,
                ),
                [[vModelText, r.value]],
              ),
              withDirectives(
                createElementVNode(
                  "select",
                  {
                    "onUpdate:modelValue": e[3] || (e[3] = (t) => (p.value = t)),
                    style: {
                      height: "32px",
                    },
                  },
                  [
                    ...(e[8] ||
                      (e[8] = [
                        createElementVNode("option", null, "换码（旧码换新码）", -1),
                        createElementVNode("option", null, "多包装（大包装条码）", -1),
                      ])),
                  ],
                  512,
                ),
                [[vModelSelect, p.value]],
              ),
            ]),
          ]),
          e[12] ||
            (e[12] = createElementVNode(
              "div",
              {
                class: "card",
              },
              [
                createElementVNode("h3", null, "别名归并（多包装 / 旧码 → 主码）"),
                createElementVNode(
                  "div",
                  {
                    class: "tip-note",
                  },
                  [
                    createTextVNode("别名归并由 "),
                    createElementVNode("code", null, "POST /barcodes/alias"),
                    createTextVNode(
                      " 登记，映射规则由系统生成；上表换码会自动写入别名并锁定旧码 90 天。",
                    ),
                  ],
                ),
              ],
              -1,
            )),
          createVNode(
            InfoBox,
            {
              show: d.value.show,
              title: d.value.title,
              onClose: e[4] || (e[4] = (t) => (d.value.show = !1)),
            },
            {
              default: withCtx(() => [
                createElementVNode(
                  "div",
                  {
                    innerHTML: DOMPurify.sanitize(d.value.html),
                  },
                  null,
                  8,
                  K,
                ),
              ]),
              _: 1,
            },
            8,
            ["show", "title"],
          ),
        ])
      );
    },
  };

export default Barcode;
