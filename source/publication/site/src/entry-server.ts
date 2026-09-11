import { renderToString } from "@vue/server-renderer";
import { createMemoryHistory } from "vue-router";

import { resetPublicationData, seedPublicationData } from "./lib/api";
import { clearRouteContext } from "./lib/route-context";
import { createPublicationApp } from "./publication-app";

export { homepageStructuredData } from "./lib/structured-data";

export interface RenderedPublicationPage {
  appHtml: string;
  modules: string[];
}

export const renderPublicationPage = async (
  route: string,
  documents: readonly unknown[],
): Promise<RenderedPublicationPage> => {
  resetPublicationData();
  seedPublicationData(documents);
  clearRouteContext();
  const { app, router } = createPublicationApp(
    createMemoryHistory(import.meta.env.BASE_URL),
    true,
  );
  await router.push(route);
  await router.isReady();
  const context: { modules?: Set<string> } = {};
  const appHtml = await renderToString(app, context);
  return { appHtml, modules: [...(context.modules ?? [])] };
};
