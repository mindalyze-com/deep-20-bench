import { selectedEditionId } from "./api";
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
