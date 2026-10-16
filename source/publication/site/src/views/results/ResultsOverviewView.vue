<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import ComparisonRankingTable from "@/components/ComparisonRankingTable.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import RankBadge from "@/components/RankBadge.vue";
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
  formatCount,
  duration,
  money,
  moneyEpisode,
  number,
  percent,
} from "@/lib/format";
import { usePageRouteContext } from "@/lib/route-context";
import { hasScoreTies, rankPresentation } from "@/lib/rank-presentation";
import { editionRoute, modelSummaryRoute } from "@/lib/route-location";
import {
  leaderboardScoreDot,
  questionScoreChartSummary,
  questionScoreRankingRule,
  type ScoreDot,
} from "@/lib/result-chart";
import type { LeaderboardRow, ManifestDocument } from "@/lib/types";
import { leaderboardSortAccessors, useTableSort } from "@/lib/use-table-sort";
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
const { sortedRows, toggleSort, ariaSort } = useTableSort(rows, leaderboardSortAccessors);

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
    label: "Rounds per model",
    value: rows.value[0]?.terminal_trials ?? 0,
  },
  {
    key: "spend",
    label: "Total benchmark cost",
    value: money(selectedBenchmarkCost.value),
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
      `Rank ${row.rank ?? "-"} · ${percent(row.success_rate)} solved`,
    ),
  ),
);

const openRun = (row: LeaderboardRow): void => {
  if (row.execution_id !== null) void router.push(modelSummaryRoute(row.model.model_id, row.execution_id));
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
          density="compact"
        />

        <section class="ranking-section" aria-labelledby="ranked-models-title">
          <header class="ranking-heading">
            <div>
              <h2 id="ranked-models-title">Ranked models</h2>
              <p>Lower question scores are better.</p>
            </div>
            <InfoPopover label="Ranking rules">
              <p>{{ questionScoreRankingRule }}</p>
              <p>The score includes failed rounds. Every subject has equal weight.</p>
            </InfoPopover>
          </header>
          <ComparisonRankingTable
            class="results-table-wrap"
            variant="results-overview"
            label="Result comparison"
            :sort-direction="ariaSort"
            @sort="toggleSort"
          >
              <tbody>
                <tr
                  v-for="row in sortedRows"
                  :key="row.model.model_id"
                  :class="{
                    'result-row--clickable': row.execution_id !== null,
                    'result-row--navigable': row.execution_id !== null,
                    'is-leading': row.rank === 1,
                  }"
                  @click="openRun(row)"
                >
                  <td class="rank-column" data-label="Question rank"><RankBadge :rank="row.rank" v-bind="rankPresentation(row, rows)" /></td>
                  <td class="model-column" data-label="Model">
                    <ModelRunLink
                      v-if="row.execution_id !== null"
                      :to="modelSummaryRoute(row.model.model_id, row.execution_id)"
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
                  <td class="success-column" data-label="Solved" data-numeric>
                    {{ percent(row.success_rate) }}
                  </td>
                  <td class="contract-column" data-label="Valid format" data-numeric>
                    {{
                      contractPercent(
                        row.contract?.compliance_rate ?? null,
                        row.contract?.violations ?? 0,
                      )
                    }}
                    <small v-if="row.contract?.status === 'breached'">
                      {{ formatCount(row.contract.violations, "violation") }}
                    </small>
                  </td>
                  <td class="cost-column" data-label="Guesser cost / round" data-numeric>
                    {{
                      row.guesser_cost_per_episode_usd === null
                        ? "-"
                        : moneyEpisode(row.guesser_cost_per_episode_usd)
                    }}
                  </td>
                  <td class="time-column" data-label="Model time / round" data-numeric>
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
              :rank-tied="rankPresentation(row, rows).tied"
              :rank-note="rankPresentation(row, rows).note"
              :name="row.model.display_name"
              :provider="row.model.provider"
              :to="row.execution_id === null ? null : modelSummaryRoute(row.model.model_id, row.execution_id)"
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
                { label: 'Solved', value: percent(row.success_rate) },
                {
                  label: 'Guesser cost / round',
                  value:
                    row.guesser_cost_per_episode_usd === null
                      ? '-'
                      : moneyEpisode(row.guesser_cost_per_episode_usd),
                },
              ]"
            />
          </div>

          <p v-if="hasScoreTies(rows)" class="results-note score-ranking-note">{{ questionScoreRankingRule }}</p>
        </section>

        <section
          class="panel result-chart-panel comparison-panel"
          aria-labelledby="overview-chart-title"
        >
          <header class="panel-heading panel-heading--with-help">
            <div>
              <p class="eyebrow">Score distribution</p>
              <h2 id="overview-chart-title">Question score.</h2>
            </div>
            <p>{{ questionScoreChartSummary }}</p>
            <ResultHelp label="Score metric explanations">
              <InfoPopover label="Question score">
                <p>
                  The average number of questions the model needed, with every subject
                  weighted equally. Lower is better. A failed round receives the fixed
                  failure score.
                </p>
                <p>{{ questionScoreRankingRule }}</p>
              </InfoPopover>
              <InfoPopover label="CI width">
                <p>
                  The line shows the 95% confidence interval (CI) of the average score. A
                  narrower CI means more consistent results across repeated rounds on these
                  subjects.
                </p>
                <p>
                  The side plot shows each CI width. Its three shaded bands split the shown
                  range into equal parts. They are a visual aid, not quality grades.
                </p>
                <p>
                  The CI describes uncertainty in the average, not the range of single
                  rounds.
                </p>
              </InfoPopover>
              <InfoPopover label="Solved and format">
                <p>
                  Solved is the share of scored rounds in which the model found the
                  subject. Failed rounds are already part of the question score. Valid
                  format is the share of model replies that used the required format.
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

        <p class="results-note">
          The 95% CI comes from repeated rounds on this edition's subjects. It does not
          cover other subjects, model versions, or providers. The three CI width bands split
          the shown range into equal parts; they are not quality grades.
          <RouterLink :to="editionRoute('models')">All models, A to Z →</RouterLink>
        </p>
    </ResultsContent>
  </div>
</template>

<style scoped>
.results-summary {
  margin-bottom: 1rem;
}

.results-summary :deep(> div) {
  padding: 0.8rem 1rem;
}

.results-summary :deep(dt) {
  font-size: 0.6875rem;
  letter-spacing: 0.055em;
}

.results-summary :deep(dd) {
  margin-top: 0.35rem;
  font-family: var(--font-body);
  font-size: 1.4rem;
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.025em;
  line-height: 1.15;
}

.ranking-section {
  margin-bottom: 2rem;
}

.ranking-heading {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 0.9rem;
}

.ranking-heading h2 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.02em;
  line-height: 1.4;
}

.ranking-heading p {
  margin: 0.25rem 0 0;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.ranking-heading :deep(.info-popover) {
  flex-shrink: 0;
  color: var(--blue-ink);
}

.ranking-heading :deep(.info-popover-trigger) {
  font-size: 0.8125rem;
}

.results-table-wrap { margin-top: 0; }

.results-table-wrap :deep(.ranking-table th) {
  padding-block: 0.75rem;
  background: var(--surface-page);
  font-size: 0.6875rem;
  letter-spacing: 0.055em;
}

.results-table-wrap :deep(.ranking-table td) {
  padding-block: 0.65rem;
}

.results-table-wrap :deep(.primary-metric-column) {
  background: var(--surface-accent-soft);
  box-shadow: none;
}

.results-table-wrap :deep(th.primary-metric-column) {
  background: var(--surface-accent-soft);
  box-shadow: inset 0 2px 0 var(--blue);
}

.results-table-wrap :deep(.is-leading) {
  background: color-mix(in srgb, var(--surface-accent-soft) 42%, var(--surface-raised));
}

.results-table-wrap :deep(.model-run-link-name) {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.results-table-wrap :deep(.model-run-link-chevron) { opacity: 0.45; }
.results-table-wrap :deep(.model-run-link:hover .model-run-link-chevron) { opacity: 1; }

.ranking-section > .mobile-result-list { margin-top: 0; }

.ranking-section :deep(.mobile-result-identity strong) {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.ranking-section :deep(.mobile-result-primary strong) {
  color: var(--blue-ink);
  font-family: var(--font-body);
  font-size: 1.125rem;
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.02em;
}

.score-ranking-note {
  margin: 0.75rem 0 0;
  font-size: 0.75rem;
  line-height: 1.5;
}

.comparison-panel { margin-bottom: 1rem; }

.comparison-panel > .panel-heading {
  grid-template-areas: "title help" "text text";
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.65rem 1.5rem;
  align-items: center;
  padding: 1.25rem 1.5rem;
}

.comparison-panel > .panel-heading h2 {
  font-family: var(--font-body);
  font-size: 1.125rem;
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.02em;
  line-height: 1.4;
}

.comparison-panel > .panel-heading .eyebrow {
  margin-bottom: 0.2rem;
  font-size: 0.625rem;
  letter-spacing: 0.06em;
}

.comparison-panel > .panel-heading > p {
  max-width: 80ch;
  font-size: 0.8125rem;
  line-height: 1.6;
}

.comparison-panel > .panel-heading > .result-help {
  align-self: center;
  padding-left: 0;
  border-left: 0;
}

.comparison-panel :deep(.result-help-items) {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 1rem;
}

.comparison-panel :deep(.info-popover-trigger) { font-size: 0.75rem; }

.comparison-panel :deep(.score-dot-plot) { padding: 0 1.25rem 1.25rem; }

@media (max-width: 760px) {
  .results-summary { margin-bottom: 1rem; }
  .results-summary :deep(> div) { padding: 0.7rem 0.8rem; }
  .results-summary :deep(dd) { font-size: 1.25rem; }

  .ranking-heading {
    align-items: start;
    gap: 0.65rem;
  }

  .ranking-heading :deep(.info-popover-trigger) { font-size: 0.75rem; }
  .ranking-section { margin-bottom: 1.5rem; }

  .comparison-panel > .panel-heading {
    grid-template-areas: "title" "text" "help";
    grid-template-columns: minmax(0, 1fr);
    gap: 0.5rem;
    padding: 1rem;
  }

  .comparison-panel :deep(.score-dot-plot) { padding: 0 0.35rem 0.75rem; }
}
</style>
