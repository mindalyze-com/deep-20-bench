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
import { getLeaderboard, getOfficialRuns } from "@/lib/api";
import { duration, integer } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow, PublicRunSummary, RunDocument } from "@/lib/types";

const documents = ref<RunDocument[]>([]);
const leaderboard = ref<LeaderboardRow[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Time results",
    description:
      "Compare Guesser response time and total benchmark runtime across official Deep20Bench runs.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

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
  { key: "runs", label: "Selected runs", value: guesserRuns.value.length },
  {
    key: "median",
    label: "Median Guesser runtime",
    value: duration(medianGuesserTime.value),
    tone: "accent",
  },
  {
    key: "guesser",
    label: "Combined Guesser runtime",
    value: duration(totalGuesserTime.value),
  },
  {
    key: "benchmark",
    label: "Combined benchmark runtime",
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
    )} per episode · ${integer(run.totals.guesser_calls)} calls`,
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
    )} per episode · ${duration(
      run.totals.guesser_think_time_ms,
    )} Guesser runtime`,
    link: `/runs/${run.execution_id}/`,
  })),
);

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
    <LoadingState v-if="loading" label="Loading time results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="guesserRuns.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Time</p>
        <h2>No official runs are available.</h2>
      </div>
    </section>

    <section v-else class="content-section">
      <div class="content-inner">
        <MetricGrid
          class="results-summary"
          :items="summaryMetrics"
          label="Time summary"
          :max-columns="4"
        />

        <section class="panel time-panel" aria-labelledby="time-chart-title">
          <header class="panel-heading">
            <div>
              <p class="eyebrow">Guesser-only runtime</p>
              <h2 id="time-chart-title">Guesser response time.</h2>
            </div>
            <p>
              Each bar sums the provider-reported response time of the model under test.
              Runs are ordered from shortest to longest.
            </p>
          </header>
          <MetricBars
            :items="guesserTimeBars"
            direction-label="Guesser runtime · lower is faster"
            color="acid"
            value-format="duration"
          />

          <section class="runtime-ledger panel-frame" aria-labelledby="runtime-ledger-title">
            <header class="panel-heading panel-heading--compact">
              <div>
                <p class="eyebrow">Total benchmark runtime</p>
                <h3 id="runtime-ledger-title">End-to-end elapsed time.</h3>
              </div>
              <p>
                Each bar shows the recorded time from run creation to its final state,
                including adjudication and benchmark overhead.
              </p>
            </header>
            <MetricBars
              :items="benchmarkTimeBars"
              direction-label="Total benchmark runtime · lower is faster"
              color="blue"
              value-format="duration"
            />
          </section>
        </section>

        <div
          class="table-wrap ranking-table-wrap results-table-wrap"
          tabindex="0"
          aria-label="Scrollable time comparison"
        >
          <table class="data-table ranking-table results-table">
            <thead>
              <tr>
                <th class="rank-column">
                  <span aria-hidden="true">#</span>
                  <span class="visually-hidden">Guesser rank</span>
                </th>
                <th class="model-column">Model</th>
                <th class="run-column">Run</th>
                <th data-numeric>Guesser runtime</th>
                <th data-numeric>Benchmark runtime</th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Guesser time</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Guesser latency</span>
                    <span>per call</span>
                  </span>
                </th>
                <th data-numeric>Guesser calls</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(run, index) in guesserRuns"
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
                <td data-numeric>{{ duration(run.totals.guesser_think_time_ms) }}</td>
                <td data-numeric>{{ duration(run.totals.runtime_ms) }}</td>
                <td data-numeric>
                  {{
                    run.comparison.guesser_think_time_per_episode_ms === null
                      ? "—"
                      : duration(
                          Number(run.comparison.guesser_think_time_per_episode_ms),
                        )
                  }}
                </td>
                <td data-numeric>
                  {{
                    run.comparison.guesser_latency_per_call_ms === null
                      ? "—"
                      : duration(Number(run.comparison.guesser_latency_per_call_ms))
                  }}
                </td>
                <td data-numeric>{{ integer(run.totals.guesser_calls) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobile-result-list" aria-label="Time comparison">
          <MobileResultCard
            v-for="(run, index) in guesserRuns"
            :key="`mobile-${run.execution_id}`"
            :rank="index + 1"
            :name="run.model_name"
            :provider="providerFor(run.model_id)"
            :to="runLink(run)"
            :metrics="[
              {
                label: 'Guesser',
                value: duration(run.totals.guesser_think_time_ms),
              },
              {
                label: 'Benchmark',
                value: duration(run.totals.runtime_ms),
              },
              {
                label: 'Per episode',
                value:
                  run.comparison.guesser_think_time_per_episode_ms === null
                    ? '—'
                    : duration(
                        Number(run.comparison.guesser_think_time_per_episode_ms),
                      ),
              },
            ]"
          />
        </div>

        <p class="results-note">
          Guesser runtime sums every recorded Guesser call. Total benchmark runtime is
          end-to-end elapsed time, so it also includes adjudication, scheduling,
          concurrency, and other benchmark work.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.results-summary,
.time-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.runtime-ledger {
  margin: 0;
}

.results-table {
  min-width: 1020px;
}

.empty-state {
  min-height: 50vh;
}
</style>
