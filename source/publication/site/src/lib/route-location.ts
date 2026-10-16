import { modelSlug, selectedEditionId } from "./api";
import type { LocationQueryRaw, RouteLocationRaw } from "vue-router";

export const runRoute = (executionId: string): RouteLocationRaw => ({
  name: "run",
  params: { executionId },
});

export const subjectRoute = (
  executionId: string,
  targetId: string,
): RouteLocationRaw => ({
  name: "subject",
  params: { executionId, targetId },
});

export const episodeRoute = (
  executionId: string,
  targetId: string,
  trialId: string,
  query?: LocationQueryRaw,
): RouteLocationRaw => ({
  name: "episode",
  params: { executionId, targetId, trialId },
  ...(query === undefined ? {} : { query }),
});

export const editionRoute = (
  name: string,
  options: { hash?: string; editionId?: string } = {},
): RouteLocationRaw => ({ name, params: { editionId: options.editionId ?? selectedEditionId.value },
      ...(options.hash === undefined ? {} : { hash: options.hash }) });

export const modelRoute = (
  slug: string,
  editionId = selectedEditionId.value,
): RouteLocationRaw => ({ name: "model", params: { editionId, slug } });

/** Link a model to its stable summary page; fall back to its run before slugs are known. */
export const modelSummaryRoute = (
  modelId: string,
  executionId: string,
  editionId = selectedEditionId.value,
): RouteLocationRaw => {
  const slug = modelSlug(modelId, editionId);
  return slug === null ? runRoute(executionId) : modelRoute(slug, editionId);
};
