import { ref, type Ref } from "vue";
import { useRouter } from "vue-router";

import { getLeaderboard, peekLeaderboard } from "./api";
import { runRoute } from "./route-location";
import type { LeaderboardRow } from "./types";
import { usePublicationLoad } from "./use-publication-load";

export interface LeaderboardResults {
  leaderboard: Ref<LeaderboardRow[]>;
  loading: Readonly<Ref<boolean>>;
  error: Readonly<Ref<string | null>>;
  openRun: (row: LeaderboardRow) => void;
}

export const useLeaderboardResults = (): LeaderboardResults => {
  const initial = peekLeaderboard();
  const leaderboard = ref<LeaderboardRow[]>(initial?.leaderboard ?? []);
  const router = useRouter();
  const { loading, error } = usePublicationLoad(async () => {
    leaderboard.value = (await getLeaderboard()).leaderboard;
  }, undefined, initial !== null);
  const openRun = (row: LeaderboardRow): void => {
    if (row.execution_id !== null) void router.push(runRoute(row.execution_id));
  };
  return { leaderboard, loading, error, openRun };
};
