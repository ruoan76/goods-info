import {
  openBlock,
  createElementBlock,
  createElementVNode,
  toDisplayString,
  withModifiers,
  createCommentVNode,
} from "vue";

const c = {
    class: "dlg-box",
  },
  d = {
    class: "row",
  },
  ConfirmDlg = {
    name: "ConfirmDlg",
    props: {
      show: Boolean,
      title: String,
      message: String,
    },
    emits: ["confirm", "cancel"],
    setup(t) {
      return (n, e) =>
        t.show
          ? (openBlock(),
            createElementBlock(
              "div",
              {
                key: 0,
                class: "mask",
                onClick: e[2] || (e[2] = withModifiers((o) => n.$emit("cancel"), ["self"])),
              },
              [
                createElementVNode("div", c, [
                  createElementVNode("h4", null, toDisplayString(t.title), 1),
                  createElementVNode("p", null, toDisplayString(t.message), 1),
                  createElementVNode("div", d, [
                    createElementVNode(
                      "button",
                      {
                        class: "btn plain sm",
                        onClick: e[0] || (e[0] = (o) => n.$emit("cancel")),
                      },
                      "再想想",
                    ),
                    createElementVNode(
                      "button",
                      {
                        class: "btn sm",
                        onClick: e[1] || (e[1] = (o) => n.$emit("confirm")),
                      },
                      "确认",
                    ),
                  ]),
                ]),
              ],
            ))
          : createCommentVNode("", !0);
    },
  };

export default ConfirmDlg;
