import { computed, ref, type Ref } from "vue";
import { useRouter } from "vue-router";

import { getLeaderboard, peekLeaderboard } from "./api";
import { useRunSelection } from "./run-selection";
import { modelSummaryRoute } from "./route-location";
import type { LeaderboardRow } from "./types";
import { usePublicationLoad } from "./use-publication-load";

export interface LeaderboardResults {
  leaderboard: Ref<LeaderboardRow[]>;
  allRows: Readonly<Ref<LeaderboardRow[]>>;
  latestRows: Readonly<Ref<LeaderboardRow[]>>;
  loading: Readonly<Ref<boolean>>;
  error: Readonly<Ref<string | null>>;
  openRun: (row: LeaderboardRow) => void;
}

export const useLeaderboardResults = (): LeaderboardResults => {
  const initial = peekLeaderboard();
  const data = ref(initial);
  const { allRuns } = useRunSelection();
  const latestRows = computed(() => data.value?.leaderboard ?? []);
  const allRows = computed(() => data.value?.runs ?? latestRows.value);
  const leaderboard = computed(() => allRuns.value ? allRows.value : latestRows.value);
  const router = useRouter();
  const { loading, error } = usePublicationLoad(async () => {
    data.value = await getLeaderboard();
  }, undefined, initial !== null);
  const openRun = (row: LeaderboardRow): void => {
    if (row.execution_id !== null) void router.push(modelSummaryRoute(row.model.model_id, row.execution_id));
  };
  return { leaderboard, allRows, latestRows, loading, error, openRun };
};
