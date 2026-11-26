import DOMPurify from "dompurify";
import { useAppStore } from "../store.js";
import {
  onMounted,
  openBlock,
  createElementBlock,
  createElementVNode,
  createTextVNode,
  unref,
  createCommentVNode,
  toDisplayString,
  Fragment,
  renderList,
  normalizeClass,
  createVNode,
  withCtx,
  ref,
} from "vue";
import { adminApi, errorMessage } from "../api.js";
import InfoBox from "../components/InfoBox.js";

const S = {
    class: "card",
  },
  U = {
    class: "tip-note warn",
  },
  A = {
    style: {
      "font-family": "Menlo",
    },
  },
  V = ["onClick"],
  P = {
    key: 1,
    style: {
      color: "var(--text3)",
    },
  },
  D = {
    class: "pager",
  },
  F = {
    class: "card",
  },
  H = {
    style: {
      "font-family": "Menlo",
    },
  },
  j = ["innerHTML"],
  Dictionary = {
    name: "Dictionary",
    setup(z) {
      const a = useAppStore(),
        i = ref([]),
        m = ref([]),
        r = ref({
          show: !1,
          title: "",
          html: "",
        }),
        k = (l) => (l ?? 0).toLocaleString("en-US");
      function $(l, t) {
        r.value = {
          show: !0,
          title: l,
          html: t,
        };
      }
      async function v() {
        try {
          const [l, t] = await Promise.all([adminApi.units(), adminApi.sources()]);
          i.value = l || [];
          m.value = t || [];
        } catch (l) {
          a.toast(errorMessage(l), "err");
        }
      }
      function g(l) {
        if (!a.isAdmin) {
          a.toast("仅管理员可维护字典", "err");
          return;
        }
        const t = !l;
        $(
          t ? "新增单位" : "编辑单位 · " + l.code,
          `<div class="result-line ok"><b>${t ? "POST /admin/units" : "PUT /admin/units/" + l.code}</b></div>
     <div class="field" style="max-width:360px;margin-top:12px"><label>单位编码</label><input id="u-code" value="${(l == null ? void 0 : l.code) || ""}" ${t ? "" : "disabled"} placeholder="如 000008" style="width:100%;height:32px;border:1px solid var(--border);border-radius:4px;padding:0 9px" /></div>
     <div class="field" style="max-width:360px"><label>单位名称（需业务确认后录入）</label><input id="u-name" value="${(l == null ? void 0 : l.name) === "（待确认）" ? "" : (l == null ? void 0 : l.name) || ""}" placeholder="如 箱" style="width:100%;height:32px;border:1px solid var(--border);border-radius:4px;padding:0 9px" /></div>
     <div class="field" style="max-width:360px"><label>排序</label><input id="u-sort" value="${(l == null ? void 0 : l.sort_order) ?? ""}" placeholder="23" style="width:100%;height:32px;border:1px solid var(--border);border-radius:4px;padding:0 9px" /></div>
     <div class="tip-note" style="margin:8px 0 0">使用商品数由系统预聚合生成（不可手填），导入任务结束时刷新，避免实时扫 432 万表。</div>
     <div style="margin-top:12px;text-align:right"><button class="btn sm" id="u-save">保存</button></div>`,
        );
        setTimeout(() => {
          var s;
          (s = document.getElementById("u-save")) == null ||
            s.addEventListener("click", async () => {
              const h = document.getElementById("u-code").value.trim(),
                u = document.getElementById("u-name").value.trim(),
                y = parseInt(document.getElementById("u-sort").value) || 0;
              if (!u) {
                a.toast("单位名称需业务确认后录入", "err");
                return;
              }
              try {
                t
                  ? await adminApi.createUnit({
                      code: h,
                      name: u,
                      sort_order: y,
                      enabled: !0,
                    })
                  : await adminApi.updateUnit(l.code, {
                      name: u,
                      sort_order: y,
                    });
                a.toast((t ? "已新增单位" : "已保存单位修改") + "「" + u + "」", "ok");
                r.value.show = !1;
                v();
              } catch (B) {
                a.toast(errorMessage(B), "err");
              }
            });
        }, 0);
      }
      return (
        onMounted(v),
        (l, t) => (
          openBlock(),
          createElementBlock("div", null, [
            t[8] ||
              (t[8] = createElementVNode(
                "div",
                {
                  class: "page-title",
                },
                "基础字典",
                -1,
              )),
            t[9] ||
              (t[9] = createElementVNode(
                "div",
                {
                  class: "page-desc",
                },
                "维护系统用到的基础数据：单位、数据来源 · 面向管理员",
                -1,
              )),
            createElementVNode("div", S, [
              createElementVNode("h3", null, [
                t[2] || (t[2] = createTextVNode("单位字典 ", -1)),
                t[3] ||
                  (t[3] = createElementVNode(
                    "span",
                    {
                      class: "tag tg-orange",
                    },
                    "名称待业务确认",
                    -1,
                  )),
                unref(a).isAdmin
                  ? (openBlock(),
                    createElementBlock(
                      "button",
                      {
                        key: 0,
                        class: "btn plain sm",
                        style: {
                          float: "right",
                        },
                        onClick: t[0] || (t[0] = (s) => g(null)),
                      },
                      "+ 新增单位",
                    ))
                  : createCommentVNode("", !0),
              ]),
              createElementVNode(
                "div",
                U,
                "单位编码含义尚未确认：以下名称仅为示意，正式名称须业务确认后录入（库中共 " +
                  toDisplayString(i.value.length) +
                  " 种单位编码）",
                1,
              ),
              createElementVNode("table", null, [
                t[4] ||
                  (t[4] = createElementVNode(
                    "thead",
                    null,
                    [
                      createElementVNode("tr", null, [
                        createElementVNode("th", null, "编码"),
                        createElementVNode("th", null, "名称（示意）"),
                        createElementVNode("th", null, "使用商品数"),
                        createElementVNode("th", null, "排序"),
                        createElementVNode("th", null, "状态"),
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
                      i.value,
                      (s) => (
                        openBlock(),
                        createElementBlock(
                          "tr",
                          {
                            key: s.code,
                          },
                          [
                            createElementVNode("td", A, toDisplayString(s.code), 1),
                            createElementVNode("td", null, toDisplayString(s.name), 1),
                            createElementVNode("td", null, toDisplayString(k(s.goods_count)), 1),
                            createElementVNode("td", null, toDisplayString(s.sort_order), 1),
                            createElementVNode("td", null, [
                              createElementVNode(
                                "span",
                                {
                                  class: normalizeClass([
                                    "tag",
                                    s.enabled ? "tg-green" : "tg-gray",
                                  ]),
                                },
                                toDisplayString(s.enabled ? "启用" : "停用"),
                                3,
                              ),
                            ]),
                            createElementVNode("td", null, [
                              unref(a).isAdmin
                                ? (openBlock(),
                                  createElementBlock(
                                    "a",
                                    {
                                      key: 0,
                                      onClick: (h) => g(s),
                                    },
                                    "编辑",
                                    8,
                                    V,
                                  ))
                                : (openBlock(), createElementBlock("span", P, "—")),
                            ]),
                          ],
                        )
                      ),
                    ),
                    128,
                  )),
                ]),
              ]),
              createElementVNode("div", D, "共 " + toDisplayString(i.value.length) + " 条", 1),
            ]),
            createElementVNode("div", F, [
              t[6] || (t[6] = createElementVNode("h3", null, "数据来源说明", -1)),
              t[7] ||
                (t[7] = createElementVNode(
                  "div",
                  {
                    class: "tip-note",
                  },
                  "商品资料有两个来源。数据打架时，系统按可靠程度自动采用更可靠的一方",
                  -1,
                )),
              createElementVNode("table", null, [
                t[5] ||
                  (t[5] = createElementVNode(
                    "thead",
                    null,
                    [
                      createElementVNode("tr", null, [
                        createElementVNode("th", null, "来源编码"),
                        createElementVNode("th", null, "来源名称"),
                        createElementVNode("th", null, "可靠程度"),
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
                      m.value,
                      (s) => (
                        openBlock(),
                        createElementBlock(
                          "tr",
                          {
                            key: s.source_code,
                          },
                          [
                            createElementVNode("td", H, toDisplayString(s.source_code), 1),
                            createElementVNode("td", null, toDisplayString(s.source_name), 1),
                            createElementVNode("td", null, [
                              createElementVNode(
                                "span",
                                {
                                  class: normalizeClass([
                                    "tag",
                                    s.reliability === "更可靠" ? "tg-green" : "tg-orange",
                                  ]),
                                },
                                toDisplayString(s.reliability),
                                3,
                              ),
                            ]),
                          ],
                        )
                      ),
                    ),
                    128,
                  )),
                ]),
              ]),
            ]),
            createVNode(
              InfoBox,
              {
                show: r.value.show,
                title: r.value.title,
                onClose: t[1] || (t[1] = (s) => (r.value.show = !1)),
              },
              {
                default: withCtx(() => [
                  createElementVNode(
                    "div",
                    {
                      innerHTML: DOMPurify.sanitize(r.value.html),
                    },
                    null,
                    8,
                    j,
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

export default Dictionary;
