import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { router } from "./router.js";
import { useAppStore } from "./store.js";
import "./style.css";

const pinia = createPinia();
const store = useAppStore(pinia);
store.restore();
store.setupUnauthorized(router);
createApp(App).use(pinia).use(router).mount("#app");
