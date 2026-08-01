<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import ComparisonRankingTable from "@/components/ComparisonRankingTable.vue";
import ErrorState from "@/components/ErrorState.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import ResultHelp from "@/components/ResultHelp.vue";
import RunTableAction from "@/components/RunTableAction.vue";
import ScoreDotPlot, { type ScoreDot } from "@/components/ScoreDotPlot.vue";
import { getLeaderboard, getManifest } from "@/lib/api";
import { duration, money, moneyEpisode, number, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow, ManifestDocument } from "@/lib/types";
import { useRepeatAverages } from "@/lib/use-repeat-averages";

const leaderboard = ref<LeaderboardRow[]>([]);
const manifest = ref<ManifestDocument | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();
const {
  averages: repeatAverages,
  loading: repeatAveragesLoading,
  error: repeatAveragesError,
  load: loadRepeatAverages,
} = useRepeatAverages();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Results",
    description: "Compare official Deep20Bench model scores, outcomes, costs, and time.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

const rows = computed(() =>
  leaderboard.value
    .filter((row) => row.status === "evaluated")
    .sort(
      (left, right) =>
        (left.rank ?? Number.MAX_SAFE_INTEGER) -
          (right.rank ?? Number.MAX_SAFE_INTEGER) ||
        left.model.display_name.localeCompare(right.model.display_name),
    ),
);

const selectedCost = computed(() =>
  rows.value.reduce((total, row) => total + Number(row.total_cost_usd ?? 0), 0),
);

const selectedGuesserTime = computed(() =>
  rows.value.reduce(
    (total, row) =>
      total +
      Number(row.guesser_think_time_per_episode_ms ?? 0) * row.terminal_trials,
    0,
  ),
);

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "models", label: "Models", value: rows.value.length },
  {
    key: "episodes",
    label: "Episodes / model",
    value: rows.value[0]?.terminal_trials ?? 0,
  },
  {
    key: "spend",
    label: "Recorded spend",
    value: money(selectedCost.value),
    tone: "accent",
  },
  {
    key: "time",
    label: "Combined model time",
    value: duration(selectedGuesserTime.value),
  },
]);

const scoreDots = computed<ScoreDot[]>(() =>
  rows.value.map((row) => ({
    modelId: row.model.model_id,
    label: row.model.display_name,
    value: Number(row.question_score ?? 0),
    display: number(row.question_score),
    confidenceLower:
      row.question_score_confidence_interval === null
        ? undefined
        : Number(row.question_score_confidence_interval.lower),
    confidenceUpper:
      row.question_score_confidence_interval === null
        ? undefined
        : Number(row.question_score_confidence_interval.upper),
    confidenceDisplay:
      row.question_score_confidence_interval === null
        ? undefined
        : `${number(row.question_score_confidence_interval.lower, 2)}–${number(
            row.question_score_confidence_interval.upper,
            2,
          )}`,
    detail: `Rank ${row.rank ?? "—"} · ${percent(row.success_rate)} success`,
    link:
      row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
  })),
);

const runLink = (row: LeaderboardRow) => ({
  name: "run",
  params: { executionId: row.execution_id },
});

const openRun = (row: LeaderboardRow): void => {
  if (row.execution_id !== null) void router.push(runLink(row));
};

const load = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  try {
    const [leaderboardDocument, manifestDocument] = await Promise.all([
      getLeaderboard(),
      getManifest(),
    ]);
    leaderboard.value = leaderboardDocument.leaderboard;
    manifest.value = manifestDocument;
  } catch (reason: unknown) {
    error.value =
      reason instanceof Error ? reason.message : "Publication data could not be loaded.";
  } finally {
    loading.value = false;
  }
};

void load();
</script>

<template>
  <div class="page results-view">
    <LoadingState v-if="loading" label="Loading official results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="rows.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Official comparison</p>
        <h2>No official results are available.</h2>
      </div>
    </section>

    <section v-else class="content-section">
      <div class="content-inner">
        <MetricGrid
          class="results-summary"
          :items="summaryMetrics"
          label="Results summary"
          :max-columns="4"
        />

        <section
          class="panel result-chart-panel comparison-panel"
          aria-labelledby="overview-chart-title"
        >
          <header class="panel-heading panel-heading--with-help">
            <div>
              <p class="eyebrow">Primary result</p>
              <h2 id="overview-chart-title">Question score.</h2>
            </div>
            <p>
              Lower is better. The blue marker is the average question score. The blue line is
              its 95% confidence interval across repeated runs. Shorter lines suggest
              more consistent performance; longer lines indicate more variation between runs.
            </p>
            <ResultHelp label="Overview metric explanations">
              <InfoPopover label="Question score">
                <p>
                  The score is the average number of questions used per subject. Lower is
                  better. Failed trials receive the benchmark penalty.
                </p>
              </InfoPopover>
              <InfoPopover label="Repeatability range">
                <p>
                  The line is a 95% confidence interval around the average score. A shorter
                  line means the model was more consistent across the repeated runs in this
                  benchmark.
                </p>
                <p>It is not the range of scores expected in one future run.</p>
              </InfoPopover>
              <InfoPopover label="Success and contract">
                <p>
                  Success is the share of trials that count toward scoring and ended with a
                  correct answer. Contract is the share of evaluated model outputs that
                  followed the required structured format.
                </p>
              </InfoPopover>
            </ResultHelp>
          </header>
          <ScoreDotPlot
            :items="scoreDots"
            :repeat-averages="repeatAverages"
            :repeat-averages-loading="repeatAveragesLoading"
            :repeat-averages-error="repeatAveragesError"
            @request-repeat-averages="loadRepeatAverages"
          />
        </section>

        <ComparisonRankingTable
          class="results-table-wrap"
          variant="results-overview"
          label="Scrollable result comparison"
        >
            <tbody>
              <tr
                v-for="row in rows"
                :key="row.model.model_id"
                :class="{
                  'result-row--clickable': row.execution_id !== null,
                  'result-row--navigable': row.execution_id !== null,
                }"
                @click="openRun(row)"
              >
                <td class="rank-column" data-label="Question rank">{{ row.rank ?? "—" }}</td>
                <td class="model-column" data-label="Model">
                  <ModelRunLink
                    v-if="row.execution_id !== null"
                    :to="runLink(row)"
                    :name="row.model.display_name"
                    :meta="row.model.provider"
                  />
                  <strong v-else>{{ row.model.display_name }}</strong>
                  <small v-if="row.execution_id === null">{{ row.model.provider }}</small>
                </td>
                <td class="run-column" data-label="Run">
                  <RunTableAction
                    v-if="row.execution_id !== null"
                    :to="runLink(row)"
                    :name="row.model.display_name"
                  />
                  <span v-else aria-hidden="true">—</span>
                </td>
                <td
                  class="primary-metric-column"
                  data-label="Question score"
                  data-numeric
                >
                  <QuestionScore
                    :score="row.question_score"
                    :confidence-interval="row.question_score_confidence_interval"
                    variant="table"
                  />
                </td>
                <td class="success-column" data-label="Success" data-numeric>
                  {{ percent(row.success_rate) }}
                </td>
                <td class="contract-column" data-label="Contract" data-numeric>
                  {{ percent(row.contract?.compliance_rate ?? null) }}
                </td>
                <td class="cost-column" data-label="Model cost / episode" data-numeric>
                  {{
                    row.guesser_cost_per_episode_usd === null
                      ? "—"
                      : moneyEpisode(row.guesser_cost_per_episode_usd)
                  }}
                </td>
                <td class="time-column" data-label="Model time / episode" data-numeric>
                  {{
                    row.guesser_think_time_per_episode_ms === null
                      ? "—"
                      : duration(Number(row.guesser_think_time_per_episode_ms))
                  }}
                </td>
              </tr>
            </tbody>
        </ComparisonRankingTable>

        <div class="mobile-result-list" aria-label="Result comparison">
          <MobileResultCard
            v-for="row in rows"
            :key="`mobile-${row.model.model_id}`"
            :rank="row.rank ?? '—'"
            :name="row.model.display_name"
            :provider="row.model.provider"
            :to="row.execution_id === null ? null : runLink(row)"
            :metrics="[
              {
                label: 'Score',
                value: number(row.question_score),
                tone: 'primary',
              },
              {
                label: 'Repeatability',
                value:
                  row.question_score_confidence_interval === null
                    ? '—'
                    : `${number(row.question_score_confidence_interval.lower, 2)}–${number(
                        row.question_score_confidence_interval.upper,
                        2,
                      )}`,
              },
              { label: 'Success', value: percent(row.success_rate) },
              {
                label: 'Cost',
                value:
                  row.guesser_cost_per_episode_usd === null
                    ? '—'
                    : moneyEpisode(row.guesser_cost_per_episode_usd),
              },
            ]"
          />
        </div>

        <p class="results-note">
          The range uses repeated seeded runs on the seven fixed subjects. It does not cover
          different subjects, model versions, or providers.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.results-summary {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.comparison-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.comparison-panel :deep(.score-dot-plot) {
  padding: 0 clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem);
}

.results-table-wrap {
  margin-top: clamp(1.5rem, 4vw, 2.5rem);
}

.empty-state {
  min-height: 50vh;
}
</style>
