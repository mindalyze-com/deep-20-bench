import { editionsIndex, modelSlug, selectedEditionId } from "./api";
import type { LocationQueryRaw, RouteLocationRaw } from "vue-router";

export const runRoute = (executionId: string, query?: LocationQueryRaw): RouteLocationRaw => ({
  name: "run",
  params: { executionId },
  ...(query === undefined ? {} : { query }),
});

export const subjectRoute = (
  executionId: string,
  targetId: string,
  query?: LocationQueryRaw,
): RouteLocationRaw => ({
  name: "subject",
  params: { executionId, targetId },
  ...(query === undefined ? {} : { query }),
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
  query?: LocationQueryRaw,
): RouteLocationRaw => ({ name: "model", params: { editionId, slug },
  ...(query === undefined ? {} : { query }) });

export const comparisonRoute = (
  modelIds: readonly string[] = [],
  editionId = selectedEditionId.value,
  baseline?: string,
): RouteLocationRaw => ({ name: "results-compare", params: { editionId },
  query: modelIds.length === 0 ? {} : modelIds.every(id => id.startsWith("BX-")) ? { runs: modelIds.join(","), ...(baseline ? { baseline } : {}) } : { models: modelIds.join(",") } });

/** Link a model to its stable summary page; fall back to its run before slugs are known. */
export const modelSummaryRoute = (
  modelId: string,
  executionId: string,
  editionId = selectedEditionId.value,
  query?: LocationQueryRaw,
): RouteLocationRaw => {
  const runs = editionsIndex.value?.editions.find(item => item.edition_id === editionId)?.runs;
  const latest = runs?.find(item => item.model_id === modelId);
  if (latest && latest.execution_id !== executionId && runs?.some(item => item.execution_id === executionId)) return runRoute(executionId, query);
  const slug = modelSlug(modelId, editionId);
  return slug === null ? runRoute(executionId, query) : modelRoute(slug, editionId, query);
};
