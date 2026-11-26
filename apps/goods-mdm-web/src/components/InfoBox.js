import {
  openBlock,
  createElementBlock,
  createElementVNode,
  toDisplayString,
  renderSlot,
  withModifiers,
  createCommentVNode,
} from "vue";

const c = {
    class: "info-box",
  },
  f = {
    class: "hd",
  },
  v = {
    class: "bd",
  },
  k = {
    class: "ft",
  },
  InfoBox = {
    name: "InfoBox",
    props: {
      title: String,
      show: Boolean,
    },
    emits: ["close"],
    setup(o) {
      return (t, e) =>
        o.show
          ? (openBlock(),
            createElementBlock(
              "div",
              {
                key: 0,
                class: "mask",
                onClick: e[2] || (e[2] = withModifiers((n) => t.$emit("close"), ["self"])),
              },
              [
                createElementVNode("div", c, [
                  createElementVNode("div", f, [
                    createElementVNode("span", null, toDisplayString(o.title), 1),
                    createElementVNode(
                      "a",
                      {
                        onClick: e[0] || (e[0] = (n) => t.$emit("close")),
                      },
                      "✕ 关闭",
                    ),
                  ]),
                  createElementVNode("div", v, [renderSlot(t.$slots, "default")]),
                  createElementVNode("div", k, [
                    createElementVNode(
                      "button",
                      {
                        class: "btn sm",
                        onClick: e[1] || (e[1] = (n) => t.$emit("close")),
                      },
                      "知道了",
                    ),
                  ]),
                ]),
              ],
            ))
          : createCommentVNode("", !0);
    },
  };

export default InfoBox;
