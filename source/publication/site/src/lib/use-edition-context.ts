import { computed } from "vue";
import type { RouteLocationNormalizedLoaded, RouteLocationRaw } from "vue-router";

import { editionsIndex, peekManifest, selectedEditionId } from "./api";
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
  const name = typeof route.name === "string" &&
    ["home", "results", "results-cost", "results-time", "results-efficiency",
      "results-reliability", "methodology", "about", "data"].includes(route.name)
    ? route.name : "home";
  const query = { ...route.query };
  delete query.editionNotice;
  return { name, params: { editionId: edition.edition_id }, query, hash: route.hash };
};

export const answerLabel = (answer: string): string =>
  ({ RATHER_YES: "Rather yes", RATHER_NO: "Rather no" })[answer as "RATHER_YES" | "RATHER_NO"]
  ?? answer;
