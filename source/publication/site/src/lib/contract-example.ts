import type { RouteLocationRaw } from "vue-router";

import type { PublicTrialSummary } from "./types";

export const firstBreachedTrial = (
  trials: readonly PublicTrialSummary[],
): PublicTrialSummary | null =>
  trials.find((trial) => trial.contract?.status === "breached") ?? null;

export const contractExampleRoute = (
  executionId: string,
  targetId: string,
  trialId: string,
): RouteLocationRaw => ({
  name: "episode",
  params: {
    executionId,
    targetId,
    trialId,
  },
  query: {
    violation: "first",
  },
});
