<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricDefinitionCard from "@/components/MetricDefinitionCard.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import ReliabilityScatter from "@/components/ReliabilityScatter.vue";
import ResultHelp from "@/components/ResultHelp.vue";
import RunTableAction from "@/components/RunTableAction.vue";
import { getLeaderboard } from "@/lib/api";
import { number, percent } from "@/lib/format";
import type { ReliabilityChartItem } from "@/lib/reliability-chart";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow } from "@/lib/types";

interface ReliabilityEntry {
  row: LeaderboardRow;
  intervalWidth: number;
  reliabilityRank: number;
}

const leaderboard = ref<LeaderboardRow[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Stability results",
    description:
      "Compare whether model scores remain consistent or vary across repeated runs.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

const confidenceIntervalWidth = (row: LeaderboardRow): number | null => {
  const interval = row.question_score_confidence_interval;
  if (interval === null) return null;
  return Number(interval.upper) - Number(interval.lower);
};

const ranked = computed<ReliabilityEntry[]>(() => {
  const entries = leaderboard.value.flatMap(
    (row): Omit<ReliabilityEntry, "reliabilityRank">[] => {
      const intervalWidth = confidenceIntervalWidth(row);
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
  { key: "direction", label: "More repeatable", value: "Smaller width" },
]);

const reliabilityChartItems = computed<ReliabilityChartItem[]>(() =>
  ranked.value.map(({ row, intervalWidth, reliabilityRank }) => {
    const interval = row.question_score_confidence_interval;
    if (interval === null) throw new Error("ranked reliability row has no interval");
    return {
      label: row.model.display_name,
      score: Number(row.question_score ?? 0),
      scoreDisplay: number(row.question_score),
      confidenceDisplay: `${number(interval.lower, 2)}–${number(interval.upper, 2)}`,
      intervalWidth,
      intervalWidthDisplay: number(intervalWidth, 2),
      reliabilityRank,
      link:
        row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
    };
  }),
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
    leaderboard.value = (await getLeaderboard()).leaderboard;
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
    <LoadingState v-if="loading" label="Loading stability results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="ranked.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Repeated-trial consistency</p>
        <h2>No models can be ranked.</h2>
        <p>Stability ranking requires a published repeated-trial confidence interval.</p>
      </div>
    </section>

    <template v-else>
      <section class="content-section">
        <div class="content-inner">
          <MetricGrid
            class="results-summary"
            :items="summaryMetrics"
            label="Stability summary"
            :max-columns="4"
          />

          <section
            class="panel reliability-scatter-panel"
            aria-labelledby="reliability-scatter-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Two-dimensional view</p>
                <h2 id="reliability-scatter-title">Repeatability.</h2>
              </div>
              <p>
                Each dot compares two results. Lower means a better average question score.
                Further left means a smaller repeatability range, so the model produced more
                consistent results across repeated runs.
              </p>
              <ResultHelp label="Stability metric explanations">
                <InfoPopover label="Repeatability width">
                  <p>
                    This width is the upper 95% confidence bound minus the lower bound. A
                    smaller width means the estimated average score varied less across the
                    current repeated runs.
                  </p>
                  <p>It is not the range expected for one future run.</p>
                </InfoPopover>
                <InfoPopover label="Score and stability">
                  <p>
                    Score and stability answer different questions. A model can repeat a
                    poor score consistently, or achieve a strong average with more variation
                    between runs.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <ReliabilityScatter :items="reliabilityChartItems" />
          </section>

          <div
            class="table-wrap ranking-table-wrap results-table-wrap"
            tabindex="0"
            aria-label="Scrollable stability ranking"
          >
            <table class="data-table ranking-table results-table">
              <thead>
                <tr>
                  <th class="rank-column">
                    <span aria-hidden="true">#</span>
                    <span class="visually-hidden">Repeatability rank</span>
                  </th>
                  <th class="model-column">Model</th>
                  <th class="run-column">Run</th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>95% CI</span>
                      <span>width</span>
                    </span>
                  </th>
                  <th data-numeric>Question rank</th>
                  <th data-numeric>Question score</th>
                  <th data-numeric>95% CI</th>
                  <th data-numeric>Success</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="entry in ranked"
                  :key="entry.row.model.model_id"
                  :class="{
                    'result-row--clickable': entry.row.execution_id !== null,
                    'result-row--navigable': entry.row.execution_id !== null,
                  }"
                  @click="openRun(entry.row)"
                >
                  <td class="rank-column">{{ entry.reliabilityRank }}</td>
                  <td class="model-column">
                    <ModelRunLink
                      v-if="entry.row.execution_id !== null"
                      :to="runLink(entry.row)"
                      :name="entry.row.model.display_name"
                      :meta="entry.row.model.provider"
                    />
                    <strong v-else>{{ entry.row.model.display_name }}</strong>
                  </td>
                  <td class="run-column">
                    <RunTableAction
                      v-if="entry.row.execution_id !== null"
                      :to="runLink(entry.row)"
                      :name="entry.row.model.display_name"
                    />
                    <span v-else aria-hidden="true">—</span>
                  </td>
                  <td data-numeric>{{ number(entry.intervalWidth, 2) }}</td>
                  <td data-numeric>{{ entry.row.rank ?? "—" }}</td>
                  <td data-numeric>{{ number(entry.row.question_score) }}</td>
                  <td data-numeric>
                    <template v-if="entry.row.question_score_confidence_interval">
                      {{ number(entry.row.question_score_confidence_interval.lower, 2) }}–{{
                        number(entry.row.question_score_confidence_interval.upper, 2)
                      }}
                    </template>
                    <span v-else aria-hidden="true">—</span>
                  </td>
                  <td data-numeric>{{ percent(entry.row.success_rate) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mobile-result-list" aria-label="Stability ranking">
            <MobileResultCard
              v-for="entry in ranked"
              :key="`mobile-${entry.row.model.model_id}`"
              :rank="entry.reliabilityRank"
              :name="entry.row.model.display_name"
              :provider="entry.row.model.provider"
              :to="entry.row.execution_id === null ? null : runLink(entry.row)"
              :metrics="[
                { label: 'CI width', value: number(entry.intervalWidth, 2) },
                { label: 'Score', value: number(entry.row.question_score) },
                {
                  label: '95% CI',
                  value:
                    entry.row.question_score_confidence_interval === null
                      ? '—'
                      : `${number(
                          entry.row.question_score_confidence_interval.lower,
                          2,
                        )}–${number(
                          entry.row.question_score_confidence_interval.upper,
                          2,
                        )}`,
                },
                { label: 'Success', value: percent(entry.row.success_rate) },
              ]"
            />
          </div>

          <p v-if="unranked.length > 0" class="results-note">
            {{ unranked.length }} evaluated model{{ unranked.length === 1 ? " is" : "s are" }}
            not ranked because a repeated-trial confidence interval is unavailable.
          </p>

          <MetricDefinitionCard
            title="Repeatability width."
            formula="95% CI width = upper confidence bound − lower confidence bound"
            interpretation="A smaller confidence interval width means the model produced more consistent aggregate results across the current repeated runs."
            detail-summary="Steps, example, interpretation, and limits"
          >
            <ol>
              <li>Calculate the fixed-subject repeated-trial confidence interval.</li>
              <li>Subtract its lower bound from its upper bound.</li>
              <li>Sort exact widths from smallest to largest.</li>
            </ol>
            <p class="metric-example">
              Example:
              <strong>17.46 − 9.79 = 7.67 questions.</strong>
            </p>
            <p>
              Every model uses the same 95% confidence level, so the level itself cannot
              define the order. The confidence interval width is the comparison measure.
            </p>
            <p>
              Repeatable does not mean good. A model can repeat a poor score closely and
              rank well here. A strong average with a large confidence interval width ranks
              lower because its repeated results vary more.
            </p>
            <p>
              This is an approximate repeatability measure for the current fixed
              subjects. It is not a prediction interval for individual trials or a
              pairwise significance test.
            </p>
          </MetricDefinitionCard>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.results-summary,
.reliability-scatter-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.results-table {
  min-width: 900px;
}

</style>
