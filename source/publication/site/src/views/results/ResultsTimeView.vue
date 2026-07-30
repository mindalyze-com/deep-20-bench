<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import ResultsNav from "@/components/ResultsNav.vue";
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
    <section class="results-hero">
      <div class="results-hero-inner">
        <div>
          <p class="eyebrow">Time</p>
          <h1>How long each run took.</h1>
        </div>
        <p>
          Guesser response time is shown separately from the total elapsed time of each
          benchmark run. Lower time is faster.
        </p>
      </div>
    </section>

    <ResultsNav />

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
        <dl class="stats-grid results-summary">
          <div>
            <dt>Selected runs</dt>
            <dd>{{ guesserRuns.length }}</dd>
          </div>
          <div>
            <dt>Median Guesser runtime</dt>
            <dd>{{ duration(medianGuesserTime) }}</dd>
          </div>
          <div>
            <dt>Combined Guesser runtime</dt>
            <dd>{{ duration(totalGuesserTime) }}</dd>
          </div>
          <div>
            <dt>Combined benchmark runtime</dt>
            <dd>{{ duration(totalBenchmarkTime) }}</dd>
          </div>
        </dl>

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

          <section class="runtime-ledger" aria-labelledby="runtime-ledger-title">
            <header>
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
.results-hero {
  padding: clamp(3rem, 7vw, 6rem) var(--gutter);
  background: var(--ink);
  color: white;
}

.results-hero-inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(18rem, 0.52fr);
  gap: clamp(2rem, 6vw, 6rem);
  align-items: end;
  width: min(100%, var(--max));
  margin-inline: auto;
}

h1,
.empty-state h2 {
  max-width: 12ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3rem, 6.5vw, 6.5rem);
  font-weight: 500;
  letter-spacing: -0.06em;
  line-height: 0.92;
}

.results-hero-inner > p {
  margin: 0;
  color: rgb(255 255 255 / 66%);
  line-height: 1.7;
}

.results-summary,
.time-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.runtime-ledger {
  margin: 0;
  border-top: 1px solid var(--line);
}

.runtime-ledger > header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(15rem, 0.5fr);
  gap: 2rem;
  align-items: end;
  padding: clamp(1.4rem, 3vw, 2.5rem);
  border-bottom: 1px solid var(--line);
}

.runtime-ledger h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3.5rem);
  font-weight: 500;
  letter-spacing: -0.045em;
  line-height: 1;
}

.runtime-ledger > header > p {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.6;
}

.results-table {
  min-width: 1020px;
}

.results-note {
  max-width: 62rem;
  margin: 1rem 0 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.65;
}

.empty-state {
  min-height: 50vh;
}

.empty-state h2 {
  font-size: clamp(2.4rem, 5vw, 4.8rem);
}

@media (max-width: 760px) {
  .results-hero-inner {
    grid-template-columns: 1fr;
  }

  .runtime-ledger > header {
    grid-template-columns: 1fr;
    gap: 0.8rem;
  }
}
</style>
