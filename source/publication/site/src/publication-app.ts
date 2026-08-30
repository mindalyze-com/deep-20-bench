import { createApp, createSSRApp, type App as VueApp } from "vue";
import type { RouterHistory } from "vue-router";

import App from "./App.vue";
import { createPublicationRouter } from "./router";

export interface PublicationApp {
  app: VueApp;
  router: ReturnType<typeof createPublicationRouter>;
}

export const createPublicationApp = (
  history: RouterHistory,
  hydrate: boolean,
): PublicationApp => {
  const app = hydrate ? createSSRApp(App) : createApp(App);
  const router = createPublicationRouter(history);
  app.use(router);
  return { app, router };
};
