<script setup lang="ts">
import { computed } from "vue";

import InfoPopover from "@/components/InfoPopover.vue";
import MetricBars from "@/components/MetricBars.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import OfficialRunRankingRow from "@/components/OfficialRunRankingRow.vue";
import RankingTable from "@/components/RankingTable.vue";
import ResultHelp from "@/components/ResultHelp.vue";
import ResultsContent from "@/components/ResultsContent.vue";
import StackedMetricBars, {
  type StackedBarRow,
  type StackedBarSegment,
} from "@/components/StackedMetricBars.vue";
import TableHeaderStack from "@/components/TableHeaderStack.vue";
import { readChartTheme } from "@/lib/chart-theme";
import { money, moneyEpisode, percent } from "@/lib/format";
import { usePageRouteContext } from "@/lib/route-context";
import { runRoute } from "@/lib/route-location";
import type { PublicRunSummary } from "@/lib/types";
import { useOfficialRunData } from "@/lib/use-official-run-data";

const { documents, loading, error, providerFor, openRun } =
  useOfficialRunData();

usePageRouteContext({
  title: "Cost results",
  description: "Compare recorded Deep20Bench run costs by model and component.",
});

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

const excludedRepairCost = (run: PublicRunSummary): number =>
  Number(run.totals.excluded_repair?.cost_usd ?? 0);

const mobileCostMetrics = (run: PublicRunSummary) => {
  const metrics = [
    {
      label: "Guesser cost / episode",
      value: moneyEpisode(run.comparison.guesser_cost_per_episode_usd),
    },
    {
      label: "Benchmark cost / episode",
      value: moneyEpisode(run.comparison.full_cost_per_episode_usd),
    },
    { label: "Benchmark run cost", value: money(run.totals.costs_usd.total) },
  ];
  if (excludedRepairCost(run) > 0) {
    metrics.push({
      label: "Excluded repair overhead",
      value: money(excludedRepairCost(run)),
    });
  }
  return metrics;
};

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "runs", label: "Models", value: runs.value.length },
  {
    key: "spend",
    label: "Total benchmark cost",
    value: money(totalSpend.value),
  },
  {
    key: "guesser",
    label: "Total Guesser cost",
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

const chartTheme = readChartTheme();
const roleColors = chartTheme.roles;
const adjudicationRows = [
  { key: "reviewer", label: "Reviewer" },
  { key: "judge", label: "Judge" },
  { key: "validator", label: "Validator" },
] as const;
const componentRows = [
  { key: "guesser", label: "Guesser", color: roleColors.guesser },
  { key: "primary_oracle", label: "Primary Oracle", color: roleColors.oracle },
  {
    key: "adjudication",
    label: "Adjudication",
    color: chartTheme.results.stability,
  },
] as const;

const stackedSegments: StackedBarSegment[] = componentRows.map((component) => ({
  label: component.label,
  color: component.color,
}));

const componentValue = (
  run: PublicRunSummary,
  key: (typeof componentRows)[number]["key"],
): number =>
  key === "adjudication"
    ? adjudicationRows.reduce(
        (sum, component) => sum + Number(run.totals.costs_usd[component.key]),
        0,
      )
    : Number(run.totals.costs_usd[key]);

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
    breakdown: adjudicationRows.map((component) => ({
      label: component.label,
      display: money(run.totals.costs_usd[component.key]),
    })),
    link: `/runs/${run.execution_id}/`,
  })),
);

const costBand = (index: number): "good" | "middle" | "bad" => {
  const position = runs.value.length <= 1 ? 0.5 : index / (runs.value.length - 1);
  if (position <= 1 / 3) return "good";
  if (position >= 2 / 3) return "bad";
  return "middle";
};

</script>

<template>
  <div class="page results-view">
    <ResultsContent
      :loading="loading"
      loading-label="Loading cost results"
      :error="error"
      :empty="runs.length === 0"
    >
      <template #empty>
        <p class="eyebrow">Cost</p>
        <h2>No official runs are available.</h2>
      </template>

        <MetricGrid
          class="results-summary"
          :items="summaryMetrics"
          label="Cost summary"
          :max-columns="4"
        />

        <div class="result-chart-stack">
          <section
            class="panel result-chart-panel cost-panel"
            aria-labelledby="cost-chart-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Guesser cost</p>
                <h2 id="cost-chart-title">Guesser cost across the run.</h2>
              </div>
              <p>
                Each bar adds the recorded provider cost of Guesser calls in the retained terminal
                attempts. Superseded infrastructure attempts and support costs are excluded.
              </p>
              <ResultHelp label="Cost metric explanations">
                <InfoPopover label="Guesser and support cost">
                  <p>
                    Guesser cost covers calls to the model under test. Support cost covers the
                    Oracle, Reviewer, Judge, and Validator. Benchmark cost combines both.
                  </p>
                </InfoPopover>
                <InfoPopover label="Per episode">
                  <p>
                    Per-episode values divide the recorded run cost by the number of terminal
                    episodes. This keeps runs comparable if cohort sizes change.
                  </p>
                </InfoPopover>
                <InfoPopover label="Repaired trials">
                  <p>
                    A repaired trial publishes only its retained terminal attempt. Superseded
                    infrastructure attempts remain in the signed benchmark audit but do not
                    increase the published model or benchmark cost. Any excluded repair overhead
                    is listed beneath the run total.
                  </p>
                </InfoPopover>
                <InfoPopover label="How this page is ordered">
                  <p>
                    The first chart is ordered by Guesser cost. The breakdown and table are
                    ordered by benchmark cost, so their order can differ.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <MetricBars
              :items="guesserCostBars"
              direction-label="Guesser cost · lower is better"
              color="coral"
              value-format="currency"
            />
          </section>

          <section
            class="panel result-chart-panel component-ledger"
            aria-labelledby="component-ledger-title"
          >
            <header class="panel-heading panel-heading--compact">
              <div>
                <p class="eyebrow">Total benchmark cost</p>
                <h3 id="component-ledger-title">Where the total cost came from.</h3>
              </div>
              <p>
                Bar length shows the retained terminal attempts' benchmark cost. Color separates
                the Guesser, Primary Oracle, and Adjudication. Expand the exact breakdown to
                compare Reviewer, Judge, and Validator cost.
              </p>
            </header>
            <StackedMetricBars
              :rows="stackedRows"
              :segments="stackedSegments"
              direction-label="Total benchmark cost by component"
            />
          </section>
        </div>

        <RankingTable label="Cost comparison" min-width="960px">
            <thead>
              <tr>
                <th class="rank-column">
                  <span aria-hidden="true">#</span>
                  <span class="visually-hidden">Benchmark cost rank</span>
                </th>
                <th class="model-column">Model</th>
                <th data-numeric>
                  <TableHeaderStack first="Guesser cost" second="per episode" />
                </th>
                <th data-numeric>
                  <TableHeaderStack first="Benchmark cost" second="per episode" />
                </th>
                <th data-numeric>
                  <TableHeaderStack first="Support cost" second="per episode" />
                </th>
                <th data-numeric>Support share</th>
                <th data-numeric>Benchmark run cost</th>
              </tr>
            </thead>
            <tbody>
              <OfficialRunRankingRow
                v-for="(run, index) in runs"
                :key="run.execution_id"
                :rank="index + 1"
                :run="run"
                @click="openRun(run)"
              >
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
                  <div class="run-cost-value">
                    <span :class="`value-signal value-signal--${costBand(index)}`">
                      {{ money(run.totals.costs_usd.total) }}
                    </span>
                    <small v-if="excludedRepairCost(run) > 0">
                      Excluded repair overhead: {{ money(excludedRepairCost(run)) }}
                    </small>
                  </div>
                </td>
              </OfficialRunRankingRow>
            </tbody>
        </RankingTable>

        <div class="mobile-result-list" aria-label="Cost comparison">
          <MobileResultCard
            v-for="(run, index) in runs"
            :key="`mobile-${run.execution_id}`"
            :rank="index + 1"
            :name="run.model_name"
            :provider="providerFor(run.model_id)"
            :to="runRoute(run.execution_id)"
            :metrics="mobileCostMetrics(run)"
          />
        </div>

        <p class="results-note">
          Costs are provider-reported values for retained terminal attempts in the selected
          official runs. Superseded infrastructure attempts are excluded. A missing or unreported
          provider price can affect the comparison.
        </p>
    </ResultsContent>
  </div>
</template>

<style scoped>
.value-signal {
  display: inline-block;
  min-width: 4rem;
  padding: 0.28rem 0.5rem;
  border-left: var(--border-emphasis-width) solid;
  background: var(--surface-raised);
  text-align: right;
  white-space: nowrap;
}

.run-cost-value {
  display: inline-grid;
  justify-items: end;
  gap: 0.35rem;
}

.run-cost-value small {
  max-width: 12rem;
  color: var(--muted);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
  line-height: 1.35;
  text-align: right;
  white-space: normal;
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

</style>
