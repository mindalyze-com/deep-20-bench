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
import { getLeaderboard } from "@/lib/api";
import { duration, money, moneyEpisode, number, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow } from "@/lib/types";

const leaderboard = ref<LeaderboardRow[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Results",
    description: "Compare official Deep20Bench model scores, outcomes, costs, and time.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

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

const selectedCost = computed(() =>
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

const scoreBars = computed(() =>
  rows.value.map((row) => ({
    label: row.model.display_name,
    value: Number(row.question_score ?? 0),
    display: number(row.question_score),
    detail: `Rank ${row.rank ?? "—"} · ${percent(row.success_rate)} success`,
    link:
      row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
  })),
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
    <section class="results-hero">
      <div class="results-hero-inner">
        <div>
          <p class="eyebrow">Official comparison</p>
          <h1>All results, one cohort.</h1>
        </div>
        <p>
          Compare model quality, reliability, recorded cost, and Guesser response time.
          Every value comes from the selected official run for the active cohort.
        </p>
      </div>
    </section>

    <ResultsNav />

    <LoadingState v-if="loading" label="Loading official results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="rows.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Official comparison</p>
        <h2>No official results are available.</h2>
      </div>
    </section>

    <section v-else class="content-section">
      <div class="content-inner">
        <dl class="stats-grid results-summary">
          <div>
            <dt>Models</dt>
            <dd>{{ rows.length }}</dd>
          </div>
          <div>
            <dt>Episodes / model</dt>
            <dd>{{ rows[0]?.terminal_trials ?? 0 }}</dd>
          </div>
          <div>
            <dt>Recorded spend</dt>
            <dd>{{ money(selectedCost) }}</dd>
          </div>
          <div>
            <dt>Combined Guesser time</dt>
            <dd>{{ duration(selectedGuesserTime) }}</dd>
          </div>
        </dl>

        <section class="panel comparison-panel" aria-labelledby="overview-chart-title">
          <header class="panel-heading">
            <div>
              <p class="eyebrow">Primary result</p>
              <h2 id="overview-chart-title">Question score.</h2>
            </div>
            <p>
              Lower is better. Scores are ordered from best to worst. Cost and time
              describe only the model under test where stated.
            </p>
          </header>
          <MetricBars
            :items="scoreBars"
            direction-label="Question score · lower is better"
            color="blue"
          />
        </section>

        <div
          class="table-wrap ranking-table-wrap results-table-wrap"
          tabindex="0"
          aria-label="Scrollable result comparison"
        >
          <table class="data-table ranking-table results-table results-table--overview">
            <thead>
              <tr>
                <th class="rank-column">
                  <span aria-hidden="true">#</span>
                  <span class="visually-hidden">Rank</span>
                </th>
                <th class="model-column">Model</th>
                <th class="run-column">Run</th>
                <th data-numeric>Score</th>
                <th data-numeric>Success</th>
                <th data-numeric>Contract</th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Guesser cost</span>
                    <span>per episode</span>
                  </span>
                </th>
                <th data-numeric>
                  <span class="table-header-stack">
                    <span>Guesser time</span>
                    <span>per episode</span>
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in rows"
                :key="row.model.model_id"
                :class="{
                  'result-row--clickable': row.execution_id !== null,
                  'result-row--navigable': row.execution_id !== null,
                }"
                @click="openRun(row)"
              >
                <td class="rank-column" data-label="Question rank">{{ row.rank ?? "—" }}</td>
                <td class="model-column" data-label="Model">
                  <ModelRunLink
                    v-if="row.execution_id !== null"
                    :to="runLink(row)"
                    :name="row.model.display_name"
                    :meta="row.model.provider"
                  />
                  <strong v-else>{{ row.model.display_name }}</strong>
                  <small v-if="row.execution_id === null">{{ row.model.provider }}</small>
                </td>
                <td class="run-column" data-label="Run">
                  <RunTableAction
                    v-if="row.execution_id !== null"
                    :to="runLink(row)"
                    :name="row.model.display_name"
                  />
                  <span v-else aria-hidden="true">—</span>
                </td>
                <td data-label="Question score" data-numeric>
                  {{ number(row.question_score) }}
                </td>
                <td data-label="Success" data-numeric>{{ percent(row.success_rate) }}</td>
                <td data-label="Contract" data-numeric>
                  {{ percent(row.contract?.compliance_rate ?? null) }}
                </td>
                <td data-label="Guesser cost / episode" data-numeric>
                  {{
                    row.guesser_cost_per_episode_usd === null
                      ? "—"
                      : moneyEpisode(row.guesser_cost_per_episode_usd)
                  }}
                </td>
                <td data-label="Guesser time / episode" data-numeric>
                  {{
                    row.guesser_think_time_per_episode_ms === null
                      ? "—"
                      : duration(Number(row.guesser_think_time_per_episode_ms))
                  }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobile-result-list" aria-label="Result comparison">
          <MobileResultCard
            v-for="row in rows"
            :key="`mobile-${row.model.model_id}`"
            :rank="row.rank ?? '—'"
            :name="row.model.display_name"
            :provider="row.model.provider"
            :to="row.execution_id === null ? null : runLink(row)"
            :metrics="[
              { label: 'Score', value: number(row.question_score) },
              { label: 'Success', value: percent(row.success_rate) },
              {
                label: 'Cost',
                value:
                  row.guesser_cost_per_episode_usd === null
                    ? '—'
                    : moneyEpisode(row.guesser_cost_per_episode_usd),
              },
            ]"
          />
        </div>

        <p class="results-note">
          Guesser time is provider-reported model response latency. It excludes Oracle,
          Reviewer, Judge, Validator, scheduling, and benchmark overhead.
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

.results-summary {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.comparison-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.results-table-wrap {
  margin-top: clamp(1.5rem, 4vw, 2.5rem);
}

.results-table--overview {
  min-width: 920px;
}

.results-note {
  max-width: 62rem;
  margin: 1rem 0 0;
  color: var(--muted);
  font-size: var(--text-small);
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
