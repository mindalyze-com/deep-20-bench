<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import ResultHelp from "@/components/ResultHelp.vue";
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
      "Compare tested-model response time and end-to-end runtime across official Deep20Bench runs.",
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
  { key: "runs", label: "Models", value: guesserRuns.value.length },
  {
    key: "median",
    label: "Median model time",
    value: duration(medianGuesserTime.value),
    tone: "accent",
  },
  {
    key: "guesser",
    label: "Combined model time",
    value: duration(totalGuesserTime.value),
  },
  {
    key: "benchmark",
    label: "Combined end-to-end time",
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
    )} model time`,
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

        <div class="result-chart-stack">
          <section
            class="panel result-chart-panel time-panel"
            aria-labelledby="time-chart-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Tested-model latency</p>
                <h2 id="time-chart-title">Model response time across the run.</h2>
              </div>
              <p>
                Each bar adds the provider-reported latency of every call to the model under
                test. Shorter is faster. This is not the wall-clock benchmark runtime.
              </p>
              <ResultHelp label="Time metric explanations">
                <InfoPopover label="Model time">
                  <p>
                    The model under test is called the Guesser in the methodology. Model time
                    adds the provider-reported latency of all its calls in the run.
                  </p>
                </InfoPopover>
                <InfoPopover label="End-to-end time">
                  <p>
                    End-to-end time is the wall-clock runtime of the full benchmark run. It
                    includes model calls, adjudication, scheduling, concurrency, and other
                    benchmark work.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <MetricBars
              :items="guesserTimeBars"
              direction-label="Model response time · lower is faster"
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
                <p class="eyebrow">Total benchmark runtime</p>
                <h3 id="runtime-ledger-title">End-to-end elapsed time.</h3>
              </div>
              <p>
                Each bar is the wall-clock time from run creation to final status. It includes
                model calls, adjudication, scheduling, concurrency, and other benchmark work.
              </p>
            </header>
            <MetricBars
              :items="benchmarkTimeBars"
              direction-label="Total benchmark runtime · lower is faster"
              color="blue"
              value-format="duration"
            />
          </section>
        </div>

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
                  <span class="visually-hidden">Model-time rank</span>
                </th>
                <th class="model-column">Model</th>
                <th class="run-column">Run</th>
                <th data-numeric>Model time</th>
                <th data-numeric>End-to-end time</th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Model time</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Model latency</span>
                    <span>per call</span>
                  </span>
                </th>
                <th data-numeric>Model calls</th>
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
                label: 'Model',
                value: duration(run.totals.guesser_think_time_ms),
              },
              {
                label: 'End-to-end',
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
          The first chart ranks model-call time. The second ranks end-to-end runtime, so the
          order can change.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.results-summary {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.results-table {
  min-width: 1020px;
}

.empty-state {
  min-height: 50vh;
}
</style>
