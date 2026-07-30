<script setup lang="ts">
import { computed, onActivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import ResultsNav from "@/components/ResultsNav.vue";
import { getOfficialRuns } from "@/lib/api";
import { duration, integer } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { RunDocument } from "@/lib/types";

const documents = ref<RunDocument[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Guesser time results",
    description:
      "Compare provider-reported Guesser response time across official Deep20Bench runs.",
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
        Number(left.comparison.guesser_think_time_per_episode_ms ?? 0) -
          Number(right.comparison.guesser_think_time_per_episode_ms ?? 0) ||
        left.model_name.localeCompare(right.model_name),
    ),
);

const guesserTimeValues = computed(() =>
  runs.value.map((run) =>
    Number(run.comparison.guesser_think_time_per_episode_ms ?? 0),
  ),
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
  runs.value.reduce((total, run) => total + run.totals.guesser_think_time_ms, 0),
);

const timeBars = computed(() =>
  runs.value.map((run) => ({
    label: run.model_name,
    value: Number(run.comparison.guesser_think_time_per_episode_ms ?? 0),
    display: duration(
      Number(run.comparison.guesser_think_time_per_episode_ms ?? 0),
    ),
    detail: `${duration(run.totals.guesser_think_time_ms)} per run · ${integer(
      run.totals.guesser_calls,
    )} calls`,
    link: `/runs/${run.execution_id}/`,
  })),
);

const load = async (): Promise<void> => {
  loading.value = true;
  error.value = null;
  try {
    documents.value = await getOfficialRuns();
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
          <h1>Guesser response time.</h1>
        </div>
        <p>
          This page shows only the provider-reported response time of the Guesser, the
          model under test. Lower time is faster.
        </p>
      </div>
    </section>

    <ResultsNav />

    <LoadingState v-if="loading" label="Loading time results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="runs.length === 0" class="content-section empty-state">
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
            <dd>{{ runs.length }}</dd>
          </div>
          <div>
            <dt>Median Guesser time / episode</dt>
            <dd>{{ duration(medianGuesserTime) }}</dd>
          </div>
          <div>
            <dt>Fastest Guesser time / episode</dt>
            <dd>{{ duration(guesserTimeValues[0] ?? 0) }}</dd>
          </div>
          <div>
            <dt>Combined Guesser time</dt>
            <dd>{{ duration(totalGuesserTime) }}</dd>
          </div>
        </dl>

        <section class="panel time-panel" aria-labelledby="time-chart-title">
          <header class="panel-heading">
            <div>
              <p class="eyebrow">Guesser only</p>
              <h2 id="time-chart-title">Response time per episode.</h2>
            </div>
            <p>
              Runs are ordered from the shortest to the longest Guesser response time
              per terminal episode.
            </p>
          </header>
          <MetricBars
            :items="timeBars"
            direction-label="Guesser response time · lower is faster"
            color="acid"
            value-format="duration"
          />
        </section>

        <div
          class="table-wrap results-table-wrap"
          tabindex="0"
          aria-label="Scrollable time comparison"
        >
          <table class="data-table results-table">
            <thead>
              <tr>
                <th>Time rank</th>
                <th>Model</th>
                <th data-numeric>Guesser time / run</th>
                <th data-numeric>Guesser time / episode</th>
                <th data-numeric>Guesser latency / call</th>
                <th data-numeric>Guesser calls</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(run, index) in runs"
                :key="run.execution_id"
                class="result-row--clickable"
              >
                <td><span class="rank-badge">{{ index + 1 }}</span></td>
                <td>
                  <RouterLink
                    class="result-row-link"
                    :to="{ name: 'run', params: { executionId: run.execution_id } }"
                    :aria-label="`Open full details for ${run.model_name}`"
                  >
                    {{ run.model_name }}
                  </RouterLink>
                </td>
                <td data-numeric>{{ duration(run.totals.guesser_think_time_ms) }}</td>
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

        <p class="results-note">
          Guesser response time excludes Oracle, Reviewer, Judge, Validator, scheduling,
          concurrency, and other benchmark overhead. It includes every recorded Guesser
          call in the run.
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

.results-table {
  min-width: 900px;
}

.rank-badge {
  display: inline-grid;
  width: 1.8rem;
  aspect-ratio: 1;
  place-items: center;
  border: 1px solid var(--line);
  font-weight: 760;
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
}
</style>
