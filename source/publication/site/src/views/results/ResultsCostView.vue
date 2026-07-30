<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import RunTableAction from "@/components/RunTableAction.vue";
import StackedMetricBars, {
  type StackedBarRow,
  type StackedBarSegment,
} from "@/components/StackedMetricBars.vue";
import { getLeaderboard, getOfficialRuns } from "@/lib/api";
import { readChartTheme } from "@/lib/chart-theme";
import { money, moneyEpisode, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow, PublicRunSummary, RunDocument } from "@/lib/types";

const documents = ref<RunDocument[]>([]);
const leaderboard = ref<LeaderboardRow[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Cost results",
    description: "Compare recorded Deep20Bench run costs by model and component.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

const runs = computed(() =>
  documents.value
    .map((document) => document.run)
    .sort(
      (left, right) =>
        Number(left.totals.costs_usd.total) - Number(right.totals.costs_usd.total) ||
        left.model_name.localeCompare(right.model_name),
    ),
);

const guesserRuns = computed(() =>
  [...runs.value].sort(
    (left, right) =>
      Number(left.totals.costs_usd.guesser) -
        Number(right.totals.costs_usd.guesser) ||
      left.model_name.localeCompare(right.model_name),
  ),
);

const totalSpend = computed(() =>
  runs.value.reduce((sum, run) => sum + Number(run.totals.costs_usd.total), 0),
);

const guesserSpend = computed(() =>
  runs.value.reduce((sum, run) => sum + Number(run.totals.costs_usd.guesser), 0),
);

const supportShare = computed(() =>
  totalSpend.value > 0
    ? String((totalSpend.value - guesserSpend.value) / totalSpend.value)
    : null,
);

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "runs", label: "Selected runs", value: runs.value.length },
  {
    key: "spend",
    label: "Recorded spend",
    value: money(totalSpend.value),
  },
  {
    key: "guesser",
    label: "Guesser spend",
    value: money(guesserSpend.value),
    tone: "accent",
  },
  {
    key: "support",
    label: "Support share",
    value: percent(supportShare.value),
  },
]);

const guesserCostBars = computed(() =>
  guesserRuns.value.map((run) => ({
    label: run.model_name,
    value: Number(run.totals.costs_usd.guesser),
    display: money(run.totals.costs_usd.guesser),
    link: `/runs/${run.execution_id}/`,
  })),
);

const roleColors = readChartTheme().roles;
const componentRows = [
  { key: "guesser", label: "Guesser", color: roleColors.guesser },
  { key: "primary_oracle", label: "Primary Oracle", color: roleColors.oracle },
  { key: "reviewer", label: "Reviewer", color: roleColors.reviewer },
  { key: "judge", label: "Judge", color: roleColors.judge },
  { key: "validator", label: "Validator", color: roleColors.validator },
] as const;

const stackedSegments: StackedBarSegment[] = componentRows.map((component) => ({
  label: component.label,
  color: component.color,
}));

const componentValue = (
  run: PublicRunSummary,
  key: (typeof componentRows)[number]["key"],
): number => Number(run.totals.costs_usd[key]);

const stackedRows = computed<StackedBarRow[]>(() =>
  runs.value.map((run) => ({
    label: run.model_name,
    display: money(run.totals.costs_usd.total),
    values: componentRows.map((component) =>
      componentValue(run, component.key),
    ),
    details: componentRows.map((component) =>
      money(componentValue(run, component.key)),
    ),
    link: `/runs/${run.execution_id}/`,
  })),
);

const costBand = (index: number): "good" | "middle" | "bad" => {
  const position = runs.value.length <= 1 ? 0.5 : index / (runs.value.length - 1);
  if (position <= 1 / 3) return "good";
  if (position >= 2 / 3) return "bad";
  return "middle";
};

const runLink = (run: PublicRunSummary) => ({
  name: "run",
  params: { executionId: run.execution_id },
});

const openRun = (run: PublicRunSummary): void => {
  void router.push(runLink(run));
};

const providerFor = (modelId: string): string =>
  leaderboard.value.find((row) => row.model.model_id === modelId)?.model.provider ??
  modelId;

const load = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  try {
    const [runDocuments, leaderboardDocument] = await Promise.all([
      getOfficialRuns(),
      getLeaderboard(),
    ]);
    documents.value = runDocuments;
    leaderboard.value = leaderboardDocument.leaderboard;
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
    <LoadingState v-if="loading" label="Loading cost results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="runs.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Cost</p>
        <h2>No official runs are available.</h2>
      </div>
    </section>

    <section v-else class="content-section">
      <div class="content-inner">
        <MetricGrid
          class="results-summary"
          :items="summaryMetrics"
          label="Cost summary"
          :max-columns="4"
        />

        <section class="panel cost-panel" aria-labelledby="cost-chart-title">
          <header class="panel-heading">
            <div>
              <p class="eyebrow">Guesser-only cost</p>
              <h2 id="cost-chart-title">Least to most expensive model.</h2>
            </div>
            <p>
              Only the model under test is counted here. Oracle, Reviewer, Judge, and
              Validator costs appear in the total-cost breakdown below.
            </p>
          </header>
          <MetricBars
            :items="guesserCostBars"
            direction-label="Guesser cost · lower is better"
            color="coral"
            value-format="currency"
          />

          <section class="component-ledger panel-frame" aria-labelledby="component-ledger-title">
            <header class="panel-heading panel-heading--compact">
              <div>
                <p class="eyebrow">Total benchmark cost</p>
                <h3 id="component-ledger-title">Where each run spent.</h3>
              </div>
              <p>
                Bar length shows the total cost of each benchmark run. Color separates
                the Guesser, Primary Oracle, Reviewer, Judge, and Validator.
              </p>
            </header>
            <StackedMetricBars
              :rows="stackedRows"
              :segments="stackedSegments"
              direction-label="Total benchmark cost by component"
            />
          </section>
        </section>

        <div
          class="table-wrap ranking-table-wrap results-table-wrap"
          tabindex="0"
          aria-label="Scrollable cost comparison"
        >
          <table class="data-table ranking-table results-table">
            <thead>
              <tr>
                <th class="rank-column">
                  <span aria-hidden="true">#</span>
                  <span class="visually-hidden">Cost rank</span>
                </th>
                <th class="model-column">Model</th>
                <th class="run-column">Run</th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Guesser cost</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Full cost</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Support cost</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>Support share</th>
                <th data-numeric>Full run</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(run, index) in runs"
                :key="run.execution_id"
                class="result-row--clickable result-row--navigable"
                @click="openRun(run)"
              >
                <td class="rank-column">{{ index + 1 }}</td>
                <td class="model-column">
                  <ModelRunLink
                    :to="runLink(run)"
                    :name="run.model_name"
                    :meta="run.model_id"
                  />
                </td>
                <td class="run-column">
                  <RunTableAction :to="runLink(run)" :name="run.model_name" />
                </td>
                <td data-numeric>
                  {{ moneyEpisode(run.comparison.guesser_cost_per_episode_usd) }}
                </td>
                <td data-numeric>
                  {{ moneyEpisode(run.comparison.full_cost_per_episode_usd) }}
                </td>
                <td data-numeric>
                  {{ moneyEpisode(run.comparison.support_cost_per_episode_usd) }}
                </td>
                <td data-numeric>{{ percent(run.comparison.support_cost_share) }}</td>
                <td data-numeric>
                  <span :class="`value-signal value-signal--${costBand(index)}`">
                    {{ money(run.totals.costs_usd.total) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobile-result-list" aria-label="Cost comparison">
          <MobileResultCard
            v-for="(run, index) in runs"
            :key="`mobile-${run.execution_id}`"
            :rank="index + 1"
            :name="run.model_name"
            :provider="providerFor(run.model_id)"
            :to="runLink(run)"
            :metrics="[
              {
                label: 'Guesser / ep.',
                value: moneyEpisode(run.comparison.guesser_cost_per_episode_usd),
              },
              {
                label: 'Full / ep.',
                value: moneyEpisode(run.comparison.full_cost_per_episode_usd),
              },
              { label: 'Full run', value: money(run.totals.costs_usd.total) },
            ]"
          />
        </div>

        <p class="results-note">
          Per-episode figures use terminal episodes as the denominator. This keeps
          comparisons consistent if cohort sizes change.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.results-summary,
.cost-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.component-ledger {
  margin: 0;
}

.results-table {
  min-width: 960px;
}

.value-signal {
  display: inline-block;
  min-width: 4rem;
  padding: 0.28rem 0.5rem;
  border-left: var(--border-emphasis-width) solid;
  background: var(--surface-raised);
  text-align: right;
  white-space: nowrap;
}

.value-signal--good {
  border-color: var(--state-clean);
}

.value-signal--middle {
  border-color: var(--state-warning);
}

.value-signal--bad {
  border-color: var(--coral);
}

.empty-state {
  min-height: 50vh;
}
</style>
