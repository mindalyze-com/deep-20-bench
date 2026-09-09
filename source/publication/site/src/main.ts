import { createWebHistory } from "vue-router";
import "@fontsource-variable/inter-tight";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/newsreader/wght-italic.css";

import { seedEmbeddedPageState } from "./lib/page-state";
import { resetPublicationData } from "./lib/api";
import { createPublicationApp } from "./publication-app";
import "./styles/app.css";

let hydrate = false;
try {
  hydrate = seedEmbeddedPageState();
} catch {
  // An older cached HTML page may outlive its data schema. Load the current documents.
  resetPublicationData();
  document.getElementById("app")?.replaceChildren();
}
const { app, router } = createPublicationApp(
  createWebHistory(import.meta.env.BASE_URL),
  hydrate,
);
await router.isReady();
app.mount("#app");
