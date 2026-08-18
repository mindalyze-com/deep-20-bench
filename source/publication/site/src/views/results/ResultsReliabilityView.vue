<script setup lang="ts">
import { computed } from "vue";

import InfoPopover from "@/components/InfoPopover.vue";
import MetricDefinitionCard from "@/components/MetricDefinitionCard.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import RankingTable from "@/components/RankingTable.vue";
import RankingDataRow from "@/components/RankingDataRow.vue";
import ReliabilityScatter from "@/components/ReliabilityScatter.vue";
import ResultHelp from "@/components/ResultHelp.vue";
import ResultsContent from "@/components/ResultsContent.vue";
import TableHeaderStack from "@/components/TableHeaderStack.vue";
import { confidenceIntervalWidth } from "@/lib/confidence-width";
import { confidenceIntervalLabel, number, percent } from "@/lib/format";
import type { ReliabilityChartItem } from "@/lib/reliability-chart";
import { usePageRouteContext } from "@/lib/route-context";
import { runRoute } from "@/lib/route-location";
import type { LeaderboardRow } from "@/lib/types";
import { useLeaderboardResults } from "@/lib/use-leaderboard-results";

interface ReliabilityEntry {
  row: LeaderboardRow;
  intervalWidth: number;
  reliabilityRank: number;
}

const { leaderboard, loading, error, openRun } = useLeaderboardResults();

usePageRouteContext({
  title: "Stability results",
  description:
    "Compare whether model scores remain consistent or vary across repeated trials on the same fixed subjects.",
});

const rowConfidenceIntervalWidth = (row: LeaderboardRow): number | null => {
  const interval = row.question_score_confidence_interval;
  if (interval === null) return null;
  return confidenceIntervalWidth(Number(interval.lower), Number(interval.upper));
};

const ranked = computed<ReliabilityEntry[]>(() => {
  const entries = leaderboard.value.flatMap(
    (row): Omit<ReliabilityEntry, "reliabilityRank">[] => {
      const intervalWidth = rowConfidenceIntervalWidth(row);
      return intervalWidth === null ? [] : [{ row, intervalWidth }];
    },
  );
  entries.sort(
    (left, right) =>
      left.intervalWidth - right.intervalWidth ||
      left.row.model.display_name.localeCompare(right.row.model.display_name),
  );
  return entries.map((entry, index) => ({
    ...entry,
    reliabilityRank: index + 1,
  }));
});

const unranked = computed(() =>
  leaderboard.value.filter(
    (row) =>
      row.status === "evaluated" && row.question_score_confidence_interval === null,
  ),
);

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "models", label: "Models", value: ranked.value.length },
  {
    key: "narrowest",
    label: "Smallest CI width",
    value: number(ranked.value[0]?.intervalWidth, 2),
    tone: "accent",
  },
  {
    key: "widest",
    label: "Largest CI width",
    value: number(ranked.value.at(-1)?.intervalWidth, 2),
  },
  { key: "direction", label: "More stable", value: "Smaller CI width" },
]);

const reliabilityChartItems = computed<ReliabilityChartItem[]>(() =>
  ranked.value.map(({ row, intervalWidth, reliabilityRank }) => {
    const interval = row.question_score_confidence_interval;
    if (interval === null) throw new Error("ranked reliability row has no interval");
    return {
      label: row.model.display_name,
      score: Number(row.question_score ?? 0),
      scoreDisplay: number(row.question_score),
      confidenceDisplay: confidenceIntervalLabel(interval),
      intervalWidth,
      intervalWidthDisplay: number(intervalWidth, 2),
      reliabilityRank,
      link:
        row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
    };
  }),
);

</script>

<template>
  <div class="page results-view">
    <ResultsContent
      :loading="loading"
      loading-label="Loading stability results"
      :error="error"
      :empty="ranked.length === 0"
    >
      <template #empty>
        <p class="eyebrow">Repeated-trial stability</p>
        <h2>No models can be ranked.</h2>
        <p>Stability ranking requires a published 95% CI.</p>
      </template>

          <MetricGrid
            class="results-summary"
            :items="summaryMetrics"
            label="Stability summary"
            :max-columns="4"
          />

          <section
            class="panel result-chart-panel reliability-scatter-panel"
            aria-labelledby="reliability-scatter-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Two-dimensional view</p>
                <h2 id="reliability-scatter-title">Stability.</h2>
              </div>
              <p>
                Each dot compares two results. Lower means a better average question score.
                Further left means a smaller CI width, so the model produced more
                consistent results across repeated trials on the fixed subjects.
              </p>
              <ResultHelp label="Stability metric explanations">
                <InfoPopover label="CI width">
                  <p>
                    CI width is the upper 95% CI bound minus the lower bound. A smaller CI
                    width means the estimated average score varied less across the current
                    repeated trials.
                  </p>
                  <p>
                    It describes uncertainty in the aggregate mean. It is not a prediction
                    interval for an individual trial.
                  </p>
                </InfoPopover>
                <InfoPopover label="Score and stability">
                  <p>
                    Score and stability answer different questions. A model can repeat a
                    poor score consistently, or achieve a strong average with more variation
                    between trials.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <ReliabilityScatter :items="reliabilityChartItems" />
          </section>

          <RankingTable label="Stability ranking" min-width="900px">
              <thead>
                <tr>
                  <th class="rank-column">
                    <span aria-hidden="true">#</span>
                    <span class="visually-hidden">Stability rank</span>
                  </th>
                  <th class="model-column">Model</th>
                  <th data-numeric>
                    <TableHeaderStack first="CI" second="width" />
                  </th>
                  <th data-numeric>Question rank</th>
                  <th data-numeric>Question score</th>
                  <th data-numeric>95% CI</th>
                  <th data-numeric>Success</th>
                </tr>
              </thead>
              <tbody>
                <RankingDataRow
                  v-for="entry in ranked"
                  :key="entry.row.model.model_id"
                  :class="{
                    'result-row--clickable': entry.row.execution_id !== null,
                    'result-row--navigable': entry.row.execution_id !== null,
                  }"
                  :rank="entry.reliabilityRank"
                  :name="entry.row.model.display_name"
                  :meta="entry.row.model.provider"
                  :to="
                    entry.row.execution_id === null
                      ? null
                      : runRoute(entry.row.execution_id)
                  "
                  @click="openRun(entry.row)"
                >
                  <td data-numeric>{{ number(entry.intervalWidth, 2) }}</td>
                  <td data-numeric>{{ entry.row.rank ?? "-" }}</td>
                  <td data-numeric>{{ number(entry.row.question_score) }}</td>
                  <td data-numeric>
                    <template v-if="entry.row.question_score_confidence_interval">
                      {{ confidenceIntervalLabel(entry.row.question_score_confidence_interval) }}
                    </template>
                    <span v-else aria-hidden="true">-</span>
                  </td>
                  <td data-numeric>{{ percent(entry.row.success_rate) }}</td>
                </RankingDataRow>
              </tbody>
          </RankingTable>

          <div class="mobile-result-list" aria-label="Stability ranking">
            <MobileResultCard
              v-for="entry in ranked"
              :key="`mobile-${entry.row.model.model_id}`"
              :rank="entry.reliabilityRank"
              :name="entry.row.model.display_name"
              :provider="entry.row.model.provider"
              :to="
                entry.row.execution_id === null
                  ? null
                  : runRoute(entry.row.execution_id)
              "
              :metrics="[
                { label: 'CI width', value: number(entry.intervalWidth, 2) },
                { label: 'Question score', value: number(entry.row.question_score) },
                {
                  label: '95% CI',
                  value: confidenceIntervalLabel(
                    entry.row.question_score_confidence_interval,
                  ),
                },
                { label: 'Success', value: percent(entry.row.success_rate) },
              ]"
            />
          </div>

          <p v-if="unranked.length > 0" class="results-note">
            {{ unranked.length }} evaluated model{{ unranked.length === 1 ? " is" : "s are" }}
            not ranked because a 95% CI is unavailable.
          </p>

          <MetricDefinitionCard
            title="CI width."
            formula="CI width = upper 95% CI bound − lower 95% CI bound"
            interpretation="A smaller CI width means the model produced more consistent aggregate results across the current repeated trials."
            detail-summary="Steps, example, interpretation, and limits"
          >
            <ol>
              <li>Calculate the fixed-subject repeated-trial 95% CI.</li>
              <li>Subtract its lower bound from its upper bound.</li>
              <li>Sort exact widths from smallest to largest.</li>
            </ol>
            <p class="metric-example">
              Example:
              <strong>17.46 − 9.79 = 7.67 questions.</strong>
            </p>
            <p>
              Every model uses the same 95% confidence level, so the level itself cannot
              define the order. CI width is the comparison measure.
            </p>
            <p>
              Stable does not mean good. A model can produce a poor score consistently and
              rank well here. A strong average with a large CI width ranks lower because its
              repeated results vary more.
            </p>
            <p>
              This is an approximate stability measure for the current fixed subjects. It is
              not a prediction interval for individual trials or a pairwise significance test.
            </p>
          </MetricDefinitionCard>
    </ResultsContent>
  </div>
</template>

<style scoped>
.reliability-scatter-panel {
  margin-bottom: var(--results-section-gap);
}

</style>
