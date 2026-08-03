import { createApp } from "vue";
import "@fontsource-variable/inter-tight";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/newsreader/wght-italic.css";

import App from "./App.vue";
import { router } from "./router";
import "./styles/app.css";

document.documentElement.classList.remove("app-loading", "static-document");
createApp(App).use(router).mount("#app");
