<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import ComparisonRankingTable from "@/components/ComparisonRankingTable.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import ResultHelp from "@/components/ResultHelp.vue";
import ResultsContent from "@/components/ResultsContent.vue";
import ScoreDotPlot from "@/components/ScoreDotPlot.vue";
import {
  getLeaderboard,
  getManifest,
  peekLeaderboard,
  peekManifest,
} from "@/lib/api";
import {
  confidenceIntervalLabel,
  contractPercent,
  duration,
  money,
  moneyEpisode,
  number,
  percent,
} from "@/lib/format";
import { usePageRouteContext } from "@/lib/route-context";
import { runRoute } from "@/lib/route-location";
import {
  leaderboardScoreDot,
  questionScoreChartSummary,
  type ScoreDot,
} from "@/lib/result-chart";
import type { LeaderboardRow, ManifestDocument } from "@/lib/types";
import { usePublicationLoad } from "@/lib/use-publication-load";
import { useRepeatAverages } from "@/lib/use-repeat-averages";

const initialLeaderboard = peekLeaderboard();
const initialManifest = peekManifest();
const leaderboard = ref<LeaderboardRow[]>(initialLeaderboard?.leaderboard ?? []);
const manifest = ref<ManifestDocument | null>(initialManifest);
const router = useRouter();
const {
  averages: repeatAverages,
  loading: repeatAveragesLoading,
  error: repeatAveragesError,
  load: loadRepeatAverages,
} = useRepeatAverages();

usePageRouteContext({
  title: "Results",
  description: "Compare official Deep20Bench model scores, outcomes, costs, and time.",
});

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

const selectedBenchmarkCost = computed(() =>
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
    label: "Total benchmark cost",
    value: money(selectedBenchmarkCost.value),
    tone: "accent",
  },
  {
    key: "time",
    label: "Total model time",
    value: duration(selectedGuesserTime.value),
  },
]);

const scoreDots = computed<ScoreDot[]>(() =>
  rows.value.map((row) =>
    leaderboardScoreDot(
      row,
      `Rank ${row.rank ?? "-"} · ${percent(row.success_rate)} success`,
    ),
  ),
);

const openRun = (row: LeaderboardRow): void => {
  if (row.execution_id !== null) void router.push(runRoute(row.execution_id));
};

const { loading, error } = usePublicationLoad(async () => {
  const [leaderboardDocument, manifestDocument] = await Promise.all([
    getLeaderboard(),
    getManifest(),
  ]);
  leaderboard.value = leaderboardDocument.leaderboard;
  manifest.value = manifestDocument;
}, undefined, initialLeaderboard !== null && initialManifest !== null);
</script>

<template>
  <div class="page results-view">
    <ResultsContent
      :loading="loading"
      loading-label="Loading official results"
      :error="error"
      :empty="rows.length === 0"
    >
      <template #empty>
        <p class="eyebrow">Official comparison</p>
        <h2>No official results are available.</h2>
      </template>

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
            <p>{{ questionScoreChartSummary }}</p>
            <ResultHelp label="Score metric explanations">
              <InfoPopover label="Question score">
                <p>
                  The score is the average number of questions used per subject. Lower is
                  better. Failed trials receive the benchmark penalty.
                </p>
              </InfoPopover>
              <InfoPopover label="CI width">
                <p>
                  The line is the 95% CI around the average score. A smaller CI width means the
                  model was more consistent across repeated trials on the fixed subjects.
                </p>
                <p>
                  The companion plot shows the exact CI width. Its background and dot
                  colors split the displayed width scale into three equal ranges. They are a
                  visual guide, not fixed quality thresholds.
                </p>
                <p>
                  It describes uncertainty in the aggregate mean. It is not a prediction
                  interval for an individual trial.
                </p>
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
          label="Result comparison"
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
                <td class="rank-column" data-label="Question rank">{{ row.rank ?? "-" }}</td>
                <td class="model-column" data-label="Model">
                  <ModelRunLink
                    v-if="row.execution_id !== null"
                    :to="runRoute(row.execution_id)"
                    :name="row.model.display_name"
                    :meta="row.model.provider"
                  />
                  <strong v-else>{{ row.model.display_name }}</strong>
                  <small v-if="row.execution_id === null">{{ row.model.provider }}</small>
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
                  {{
                    contractPercent(
                      row.contract?.compliance_rate ?? null,
                      row.contract?.violations ?? 0,
                    )
                  }}
                </td>
                <td class="cost-column" data-label="Guesser cost / episode" data-numeric>
                  {{
                    row.guesser_cost_per_episode_usd === null
                      ? "-"
                      : moneyEpisode(row.guesser_cost_per_episode_usd)
                  }}
                </td>
                <td class="time-column" data-label="Model time / episode" data-numeric>
                  {{
                    row.guesser_think_time_per_episode_ms === null
                      ? "-"
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
            :rank="row.rank ?? '-'"
            :name="row.model.display_name"
            :provider="row.model.provider"
            :to="row.execution_id === null ? null : runRoute(row.execution_id)"
            :metrics="[
              {
                label: 'Question score',
                value: number(row.question_score),
              },
              {
                label: '95% CI',
                value: confidenceIntervalLabel(
                  row.question_score_confidence_interval,
                ),
              },
              { label: 'Success', value: percent(row.success_rate) },
              {
                label: 'Guesser cost / episode',
                value:
                  row.guesser_cost_per_episode_usd === null
                    ? '-'
                    : moneyEpisode(row.guesser_cost_per_episode_usd),
              },
            ]"
          />
        </div>

        <p class="results-note">
          The 95% CI uses repeated seeded trials on the seven fixed subjects. The three CI width
          bands divide the displayed scale into equal ranges. They are not fixed quality
          thresholds. The 95% CI does not cover different subjects, model versions, or
          providers.
        </p>
    </ResultsContent>
  </div>
</template>

<style scoped>
.comparison-panel {
  margin-bottom: var(--results-section-gap);
}

.comparison-panel :deep(.score-dot-plot) {
  padding: 0 clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem);
}

.results-table-wrap {
  margin-top: var(--results-section-gap);
}

@media (max-width: 620px) {
  .comparison-panel :deep(.score-dot-plot) {
    padding-inline: 0.35rem;
  }
}
</style>
