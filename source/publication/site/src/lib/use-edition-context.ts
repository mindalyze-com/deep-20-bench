import { computed } from "vue";
import type { RouteLocationNormalizedLoaded, RouteLocationRaw } from "vue-router";

import { editionsIndex, peekManifest, selectedEditionId } from "./api";
import { comparisonState } from "./comparison";
import type { CohortConfig, EditionReference } from "./types";

export const editionAnswers = (cohort: CohortConfig | null): readonly string[] =>
  cohort?.eligibility.kind === "qualified_release"
    ? ["YES", "RATHER_YES", "RATHER_NO", "NO", "UNKNOWN"]
    : ["YES", "NO", "UNKNOWN"];

export const useEditionContext = () => {
  const selectedEdition = computed(() => editionsIndex.value?.editions.find(
    edition => edition.edition_id === selectedEditionId.value,
  ));
  const currentEdition = computed(() => editionsIndex.value?.editions.find(
    edition => edition.status === "current",
  ));
  const isPreviousEdition = computed(() => selectedEdition.value?.status === "previous");
  const manifest = computed(() => peekManifest(selectedEditionId.value));
  const cohort = computed(() => manifest.value?.active_cohort ?? null);
  const qualified = computed(() => cohort.value?.eligibility.kind === "qualified_release");
  const answers = computed(() => editionAnswers(cohort.value));
  return { editionId: selectedEditionId, selectedEdition, currentEdition, isPreviousEdition,
    manifest, cohort, qualified, answers, editionsIndex };
};

export const editionDestination = (
  route: RouteLocationNormalizedLoaded,
  edition: EditionReference,
): RouteLocationRaw => {
  if (edition.edition_id === selectedEditionId.value) return route.fullPath;
  if (route.name === "results-compare") {
    const state = comparisonState(route.query);
    const kept = state.modelIds.filter(id => edition.models.some(model => model.model_id === id));
    const targets = new Set(edition.runs.filter(run => kept.includes(run.model_id)).flatMap(run => run.target_ids));
    return { name: "results-compare", params: { editionId: edition.edition_id }, query: {
      ...route.query, models: kept.join(",") || undefined,
      baseline: kept.includes(state.baseline) ? state.baseline : undefined,
      expanded: state.expanded.filter(id => targets.has(id)).join(",") || undefined,
      comparisonNotice: kept.length < state.modelIds.length ? "missing-models" : undefined,
    } };
  }
  const executionId = route.params.executionId;
  if (typeof executionId === "string") {
    const source = editionsIndex.value?.editions.flatMap(item => item.runs)
      .find(run => run.execution_id === executionId);
    const target = edition.runs.find(run => run.model_id === source?.model_id);
    if (target === undefined) {
      return { name: "results", params: { editionId: edition.edition_id },
        query: { editionNotice: "missing-model" } };
    }
    const targetId = route.params.targetId;
    if (typeof targetId === "string" && target.target_ids.includes(targetId)) {
      return { name: "subject", params: { executionId: target.execution_id, targetId },
        query: route.name === "episode" ? { editionNotice: "episode-scope" } : {} };
    }
    return { name: "run", params: { executionId: target.execution_id },
      query: typeof targetId === "string" ? { editionNotice: "missing-subject" } : {} };
  }
  const slug = route.params.slug;
  if (route.name === "model" && typeof slug === "string") {
    const source = editionsIndex.value?.editions.find(item => item.edition_id === selectedEditionId.value)
      ?.models.find(model => model.slug === slug);
    const target = edition.models.find(model => model.model_id === source?.model_id);
    return target === undefined
      ? { name: "models", params: { editionId: edition.edition_id },
        query: { editionNotice: "missing-model-page" } }
      : { name: "model", params: { editionId: edition.edition_id, slug: target.slug } };
  }
  const name = typeof route.name === "string" &&
    ["home", "results", "results-cost", "results-time", "results-efficiency",
      "results-reliability", "why", "methodology", "about", "data", "models"].includes(route.name)
    ? route.name : "home";
  const query = { ...route.query };
  delete query.editionNotice;
  return { name, params: { editionId: edition.edition_id }, query, hash: route.hash };
};

const answerLabels: Readonly<Record<string, string>> = {
  YES: "Yes",
  RATHER_YES: "Rather yes",
  RATHER_NO: "Rather no",
  NO: "No",
  UNKNOWN: "Unknown",
};

// Visible text uses one case for every answer; wire tokens stay unchanged in data and code.
export const answerLabel = (answer: string): string => answerLabels[answer] ?? answer;
