import { computed, ref, type Ref } from "vue";
import { useRouter } from "vue-router";

import {
  getLeaderboard,
  getOfficialRuns,
  peekLeaderboard,
  peekOfficialRuns,
} from "./api";
import { useRunSelection } from "./run-selection";
import { modelSummaryRoute } from "./route-location";
import type { LeaderboardRow, PublicRunSummary, RunDocument } from "./types";
import { usePublicationLoad } from "./use-publication-load";

export interface OfficialRunData {
  documents: Ref<RunDocument[]>;
  allDocuments: Readonly<Ref<RunDocument[]>>;
  latestDocuments: Readonly<Ref<RunDocument[]>>;
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
  const allDocuments = ref<RunDocument[]>(initialDocuments ?? []);
  const { allRuns } = useRunSelection();
  const documents = computed(() => allDocuments.value.filter(document => allRuns.value || leaderboard.value.some(row => row.execution_id === document.run.execution_id)));
  const leaderboard = ref<LeaderboardRow[]>(initialLeaderboard?.leaderboard ?? []);
  const latestDocuments = computed(() => allDocuments.value.filter(document => leaderboard.value.some(row => row.execution_id === document.run.execution_id)));
  const { loading, error } = usePublicationLoad(async () => {
    const [runDocuments, leaderboardDocument] = await Promise.all([
      getOfficialRuns(),
      getLeaderboard(),
    ]);
    allDocuments.value = runDocuments;
    leaderboard.value = leaderboardDocument.leaderboard;
  }, undefined, initialDocuments !== null && initialLeaderboard !== null);

  const providerFor = (modelId: string): string =>
    leaderboard.value.find((row) => row.model.model_id === modelId)?.model.provider ??
    modelId;

  const openRun = (run: PublicRunSummary): void => {
    void router.push(modelSummaryRoute(run.model_id, run.execution_id));
  };

  return {
    documents,
    allDocuments,
    latestDocuments,
    leaderboard,
    loading,
    error,
    providerFor,
    openRun,
  };
};
