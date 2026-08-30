import { ref, type Ref } from "vue";
import { useRouter } from "vue-router";

import {
  getLeaderboard,
  getOfficialRuns,
  peekLeaderboard,
  peekOfficialRuns,
} from "./api";
import { runRoute } from "./route-location";
import type { LeaderboardRow, PublicRunSummary, RunDocument } from "./types";
import { usePublicationLoad } from "./use-publication-load";

export interface OfficialRunData {
  documents: Ref<RunDocument[]>;
  leaderboard: Ref<LeaderboardRow[]>;
  loading: Readonly<Ref<boolean>>;
  error: Readonly<Ref<string | null>>;
  providerFor: (modelId: string) => string;
  openRun: (run: PublicRunSummary) => void;
}

export const useOfficialRunData = (): OfficialRunData => {
  const router = useRouter();
  const initialDocuments = peekOfficialRuns();
  const initialLeaderboard = peekLeaderboard();
  const documents = ref<RunDocument[]>(initialDocuments ?? []);
  const leaderboard = ref<LeaderboardRow[]>(initialLeaderboard?.leaderboard ?? []);
  const { loading, error } = usePublicationLoad(async () => {
    const [runDocuments, leaderboardDocument] = await Promise.all([
      getOfficialRuns(),
      getLeaderboard(),
    ]);
    documents.value = runDocuments;
    leaderboard.value = leaderboardDocument.leaderboard;
  }, undefined, initialDocuments !== null && initialLeaderboard !== null);

  const providerFor = (modelId: string): string =>
    leaderboard.value.find((row) => row.model.model_id === modelId)?.model.provider ??
    modelId;

  const openRun = (run: PublicRunSummary): void => {
    void router.push(runRoute(run.execution_id));
  };

  return {
    documents,
    leaderboard,
    loading,
    error,
    providerFor,
    openRun,
  };
};
