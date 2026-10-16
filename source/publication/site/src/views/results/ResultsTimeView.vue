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
import SortButton from "@/components/SortButton.vue";
import { duration, integer } from "@/lib/format";
import { usePageRouteContext } from "@/lib/route-context";
import { modelSummaryRoute } from "@/lib/route-location";
import { useOfficialRunData } from "@/lib/use-official-run-data";
import { useTableSort } from "@/lib/use-table-sort";

const { documents, loading, error, providerFor, openRun } =
  useOfficialRunData();

usePageRouteContext({
  title: "Time results",
  description:
    "Compare model time and total runtime across official Deep20Bench runs.",
});

const guesserRuns = computed(() =>
  documents.value
    .map((document) => document.run)
    .sort(
      (left, right) =>
        left.totals.guesser_think_time_ms -
          right.totals.guesser_think_time_ms ||
        left.model_name.localeCompare(right.model_name),
    ),
);

const benchmarkRuns = computed(() =>
  [...guesserRuns.value].sort(
    (left, right) =>
      left.totals.runtime_ms - right.totals.runtime_ms ||
      left.model_name.localeCompare(right.model_name),
  ),
);

// Rank comes from model time and stays fixed while sorting other columns.
const runEntries = computed(() =>
  guesserRuns.value.map((run, index) => ({ run, rank: index + 1 })),
);
const milliseconds = (value: string | number | null): number | null =>
  value === null ? null : Number(value);
const { sortedRows: sortedEntries, toggleSort, ariaSort } = useTableSort(runEntries, {
  model: (entry) => entry.run.model_name,
  model_time: (entry) => entry.run.totals.guesser_think_time_ms,
  runtime: (entry) => entry.run.totals.runtime_ms,
  per_round: (entry) => milliseconds(entry.run.comparison.guesser_think_time_per_episode_ms),
  per_call: (entry) => milliseconds(entry.run.comparison.guesser_latency_per_call_ms),
  calls: (entry) => entry.run.totals.guesser_calls,
});

const guesserTimeValues = computed(() =>
  guesserRuns.value.map((run) => run.totals.guesser_think_time_ms),
);

const medianGuesserTime = computed(() => {
  const midpoint = Math.floor(guesserTimeValues.value.length / 2);
  if (guesserTimeValues.value.length === 0) return 0;
  if (guesserTimeValues.value.length % 2 === 1) {
    return guesserTimeValues.value[midpoint] ?? 0;
  }
  return (
    ((guesserTimeValues.value[midpoint - 1] ?? 0) +
      (guesserTimeValues.value[midpoint] ?? 0)) /
    2
  );
});

const totalGuesserTime = computed(() =>
  guesserRuns.value.reduce(
    (total, run) => total + run.totals.guesser_think_time_ms,
    0,
  ),
);

const totalBenchmarkTime = computed(() =>
  benchmarkRuns.value.reduce(
    (total, run) => total + run.totals.runtime_ms,
    0,
  ),
);

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "runs", label: "Models", value: guesserRuns.value.length },
  {
    key: "median",
    label: "Median model time",
    value: duration(medianGuesserTime.value),
    tone: "accent",
  },
  {
    key: "guesser",
    label: "Total model time",
    value: duration(totalGuesserTime.value),
  },
  {
    key: "benchmark",
    label: "Total end-to-end time",
    value: duration(totalBenchmarkTime.value),
  },
]);

const guesserTimeBars = computed(() =>
  guesserRuns.value.map((run) => ({
    label: run.model_name,
    value: run.totals.guesser_think_time_ms,
    display: duration(run.totals.guesser_think_time_ms),
    detail: `${duration(
      Number(run.comparison.guesser_think_time_per_episode_ms ?? 0),
    )} per round · ${integer(run.totals.guesser_calls)} calls`,
    link: `/runs/${run.execution_id}/`,
  })),
);

const benchmarkTimeBars = computed(() =>
  benchmarkRuns.value.map((run) => ({
    label: run.model_name,
    value: run.totals.runtime_ms,
    display: duration(run.totals.runtime_ms),
    detail: `${duration(
      Number(run.comparison.runtime_per_episode_ms ?? 0),
    )} per round · ${duration(
      run.totals.guesser_think_time_ms,
    )} model time`,
    link: `/runs/${run.execution_id}/`,
  })),
);

</script>

<template>
  <div class="page results-view">
    <ResultsContent
      :loading="loading"
      loading-label="Loading time results"
      :error="error"
      :empty="guesserRuns.length === 0"
    >
      <template #empty>
        <p class="eyebrow">Time</p>
        <h2>No official runs are available.</h2>
      </template>

        <MetricGrid
          class="results-summary"
          :items="summaryMetrics"
          label="Time summary"
          :max-columns="4"
        />

        <div class="result-chart-stack">
          <section
            class="panel result-chart-panel time-panel"
            aria-labelledby="time-chart-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Model time</p>
                <h2 id="time-chart-title">Model time across the run.</h2>
              </div>
              <p>
                Each bar is the total time of all calls to the tested model, as reported by
                the provider. Shorter is faster. This is not the total benchmark runtime.
              </p>
              <ResultHelp label="Time metric explanations">
                <InfoPopover label="Model time">
                  <p>
                    Model time is the total time of all calls to the tested model (the
                    Guesser) in the run, as reported by the provider.
                  </p>
                </InfoPopover>
                <InfoPopover label="End-to-end time">
                  <p>
                    End-to-end time is the clock time from start to finish of the benchmark
                    run. It includes model calls, answer checks, and waiting. Work that runs in
                    parallel counts once.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <MetricBars
              :items="guesserTimeBars"
              direction-label="Model time · lower is faster"
              color="acid"
              value-format="duration"
            />
          </section>

          <section
            class="panel result-chart-panel runtime-ledger"
            aria-labelledby="runtime-ledger-title"
          >
            <header class="panel-heading panel-heading--compact">
              <div>
                <p class="eyebrow">End-to-end time</p>
                <h3 id="runtime-ledger-title">End-to-end benchmark time.</h3>
              </div>
              <p>
                Each bar is the clock time from start to finish of the run. It includes model
                calls, answer checks, web search, and waiting for provider rate limits, so it
                says more about the test setup than about the model. It is sorted, not ranked.
              </p>
            </header>
            <MetricBars
              :items="benchmarkTimeBars"
              direction-label="End-to-end time · lower is faster"
              color="blue"
              value-format="duration"
            />
          </section>
        </div>

        <RankingTable label="Time comparison" min-width="1020px">
            <thead>
              <tr>
                <th class="rank-column">
                  <span aria-hidden="true">#</span>
                  <span class="visually-hidden">Model-time rank</span>
                </th>
                <th class="model-column" :aria-sort="ariaSort('model')">
                  <SortButton :labels="['Model']" :direction="ariaSort('model')" @sort="toggleSort('model')" />
                </th>
                <th data-numeric :aria-sort="ariaSort('model_time')">
                  <SortButton :labels="['Model time']" :direction="ariaSort('model_time')" @sort="toggleSort('model_time')" />
                </th>
                <th data-numeric :aria-sort="ariaSort('runtime')">
                  <SortButton :labels="['End-to-end time']" :direction="ariaSort('runtime')" @sort="toggleSort('runtime')" />
                </th>
                <th data-numeric :aria-sort="ariaSort('per_round')">
                  <SortButton :labels="['Model time', 'per round']" :direction="ariaSort('per_round')" @sort="toggleSort('per_round')" />
                </th>
                <th data-numeric :aria-sort="ariaSort('per_call')">
                  <SortButton :labels="['Model time', 'per call']" :direction="ariaSort('per_call')" @sort="toggleSort('per_call')" />
                </th>
                <th data-numeric :aria-sort="ariaSort('calls')">
                  <SortButton :labels="['Model calls']" :direction="ariaSort('calls')" @sort="toggleSort('calls')" />
                </th>
              </tr>
            </thead>
            <tbody>
              <OfficialRunRankingRow
                v-for="{ run, rank } in sortedEntries"
                :key="run.execution_id"
                :rank="rank"
                :run="run"
                @click="openRun(run)"
              >
                <td data-numeric>{{ duration(run.totals.guesser_think_time_ms) }}</td>
                <td data-numeric>{{ duration(run.totals.runtime_ms) }}</td>
                <td data-numeric>
                  {{
                    run.comparison.guesser_think_time_per_episode_ms === null
                      ? "-"
                      : duration(
                          Number(run.comparison.guesser_think_time_per_episode_ms),
                        )
                  }}
                </td>
                <td data-numeric>
                  {{
                    run.comparison.guesser_latency_per_call_ms === null
                      ? "-"
                      : duration(Number(run.comparison.guesser_latency_per_call_ms))
                  }}
                </td>
                <td data-numeric>{{ integer(run.totals.guesser_calls) }}</td>
              </OfficialRunRankingRow>
            </tbody>
        </RankingTable>

        <div class="mobile-result-list" aria-label="Time comparison">
          <MobileResultCard
            v-for="(run, index) in guesserRuns"
            :key="`mobile-${run.execution_id}`"
            :rank="index + 1"
            :name="run.model_name"
            :provider="providerFor(run.model_id)"
            :to="modelSummaryRoute(run.model_id, run.execution_id)"
            :metrics="[
              {
                label: 'Model time',
                value: duration(run.totals.guesser_think_time_ms),
              },
              {
                label: 'End-to-end time',
                value: duration(run.totals.runtime_ms),
              },
              {
                label: 'Model time / round',
                value:
                  run.comparison.guesser_think_time_per_episode_ms === null
                    ? '-'
                    : duration(
                        Number(run.comparison.guesser_think_time_per_episode_ms),
                      ),
              },
            ]"
          />
        </div>

        <p class="results-note">
          Models rank by model time. The end-to-end chart is only sorted by duration,
          because answer checks and rate limits dominate it.
        </p>
    </ResultsContent>
  </div>
</template>
