import { createApp } from "vue";
import "@fontsource-variable/inter-tight";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/newsreader/wght-italic.css";

import App from "./App.vue";
import { router } from "./router";
import "./styles/app.css";

createApp(App).use(router).mount("#app");
