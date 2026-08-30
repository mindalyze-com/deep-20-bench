import { createWebHistory } from "vue-router";
import "@fontsource-variable/inter-tight";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/newsreader/wght-italic.css";

import { seedEmbeddedPageState } from "./lib/page-state";
import { createPublicationApp } from "./publication-app";
import "./styles/app.css";

const hydrate = seedEmbeddedPageState();
const { app, router } = createPublicationApp(
  createWebHistory(import.meta.env.BASE_URL),
  hydrate,
);
await router.isReady();
app.mount("#app");
