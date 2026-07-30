<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import EfficiencyScatter, {
  type EfficiencyPoint,
} from "@/components/EfficiencyScatter.vue";
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import RunTableAction from "@/components/RunTableAction.vue";
import { getLeaderboard } from "@/lib/api";
import { moneyEpisode, number, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { LeaderboardRow } from "@/lib/types";

const leaderboard = ref<LeaderboardRow[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Efficiency results",
    description:
      "Compare the official cost-adjusted question score and cost-quality trade-off.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

const ranked = computed(() =>
  leaderboard.value
    .filter((row) => row.efficiency_rank !== null)
    .sort(
      (left, right) =>
        (left.efficiency_rank ?? Number.MAX_SAFE_INTEGER) -
          (right.efficiency_rank ?? Number.MAX_SAFE_INTEGER) ||
        left.model.display_name.localeCompare(right.model.display_name),
    ),
);

const unranked = computed(() =>
  leaderboard.value.filter((row) => row.efficiency_rank === null),
);

const costRange = computed(() => {
  const costs = ranked.value
    .map((row) => Number(row.guesser_cost_per_episode_usd))
    .filter((cost) => Number.isFinite(cost) && cost > 0);
  if (costs.length < 2) return null;
  return Math.max(...costs) / Math.min(...costs);
});

const summaryMetrics = computed<MetricGridItem[]>(() => [
  { key: "models", label: "Models", value: ranked.value.length },
  {
    key: "range",
    label: "Cost range",
    value: costRange.value === null ? "—" : `${number(costRange.value, 0)}×`,
  },
  {
    key: "best",
    label: "Best efficiency",
    value: number(ranked.value[0]?.cost_adjusted_question_score, 3),
    tone: "accent",
  },
  { key: "direction", label: "Direction", value: "Lower" },
]);

const efficiencyBars = computed(() =>
  ranked.value.map((row) => ({
    label: row.model.display_name,
    value: Number(row.cost_adjusted_question_score ?? 0),
    display: number(row.cost_adjusted_question_score, 3),
    detail: `${number(row.question_score)} questions × ${moneyEpisode(
      row.guesser_cost_per_episode_usd,
    )} per episode`,
    link:
      row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
  })),
);

const efficiencyPoints = computed<EfficiencyPoint[]>(() =>
  ranked.value.map((row) => ({
    label: row.model.display_name,
    rank: row.efficiency_rank ?? 0,
    cost: Number(row.guesser_cost_per_episode_usd ?? 0),
    costDisplay: moneyEpisode(row.guesser_cost_per_episode_usd),
    score: Number(row.question_score ?? 0),
    scoreDisplay: number(row.question_score),
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
    <LoadingState v-if="loading" label="Loading efficiency results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="ranked.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Cost efficiency</p>
        <h2>No models can be ranked.</h2>
        <p>
          Efficiency needs a question score, terminal episode, Guesser call, and
          positive recorded Guesser cost.
        </p>
      </div>
    </section>

    <template v-else>
      <section class="content-section">
        <div class="content-inner">
          <MetricGrid
            class="results-summary"
            :items="summaryMetrics"
            label="Efficiency summary"
            :max-columns="4"
          />

          <section class="panel efficiency-panel" aria-labelledby="efficiency-title">
            <header class="panel-heading">
              <div>
                <p class="eyebrow">Official ranking</p>
                <h2 id="efficiency-title">Cost-adjusted score.</h2>
              </div>
              <p>
                Lower is better. Each value combines question score with recorded
                Guesser cost per terminal episode.
              </p>
            </header>
            <MetricBars
              :items="efficiencyBars"
              direction-label="USD·questions per episode · lower is better"
              color="blue"
            />
          </section>

          <section class="tradeoff-panel panel-frame" aria-labelledby="tradeoff-title">
            <header class="panel-heading">
              <div>
                <p class="eyebrow">Trade-off map</p>
                <h2 id="tradeoff-title">Cost and result.</h2>
              </div>
              <p>
                Each point is one model. Both axes use their original linear scale.
              </p>
            </header>
            <EfficiencyScatter :items="efficiencyPoints" />
          </section>

          <div
            class="table-wrap ranking-table-wrap results-table-wrap"
            tabindex="0"
            aria-label="Scrollable efficiency ranking"
          >
            <table class="data-table ranking-table results-table">
              <thead>
                <tr>
                  <th class="rank-column">
                    <span aria-hidden="true">#</span>
                    <span class="visually-hidden">Efficiency rank</span>
                  </th>
                  <th class="model-column">Model</th>
                  <th class="run-column">Run</th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>Cost-adjusted</span>
                      <span>score</span>
                    </span>
                  </th>
                  <th data-numeric>Question rank</th>
                  <th data-numeric>Question score</th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>Guesser cost</span>
                      <span>per episode</span>
                    </span>
                  </th>
                  <th data-numeric>Success</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in ranked"
                  :key="row.model.model_id"
                  :class="{
                    'result-row--clickable': row.execution_id !== null,
                    'result-row--navigable': row.execution_id !== null,
                  }"
                  @click="openRun(row)"
                >
                  <td class="rank-column">{{ row.efficiency_rank }}</td>
                  <td class="model-column">
                    <ModelRunLink
                      v-if="row.execution_id !== null"
                      :to="runLink(row)"
                      :name="row.model.display_name"
                      :meta="row.model.provider"
                    />
                    <strong v-else>{{ row.model.display_name }}</strong>
                  </td>
                  <td class="run-column">
                    <RunTableAction
                      v-if="row.execution_id !== null"
                      :to="runLink(row)"
                      :name="row.model.display_name"
                    />
                    <span v-else aria-hidden="true">—</span>
                  </td>
                  <td data-numeric>
                    {{ number(row.cost_adjusted_question_score, 3) }}
                  </td>
                  <td data-numeric>{{ row.rank ?? "—" }}</td>
                  <td data-numeric>{{ number(row.question_score) }}</td>
                  <td data-numeric>
                    {{ moneyEpisode(row.guesser_cost_per_episode_usd) }}
                  </td>
                  <td data-numeric>{{ percent(row.success_rate) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mobile-result-list" aria-label="Efficiency ranking">
            <MobileResultCard
              v-for="row in ranked"
              :key="`mobile-${row.model.model_id}`"
              :rank="row.efficiency_rank ?? '—'"
              :name="row.model.display_name"
              :provider="row.model.provider"
              :to="row.execution_id === null ? null : runLink(row)"
              :metrics="[
                {
                  label: 'Adjusted',
                  value: number(row.cost_adjusted_question_score, 3),
                },
                { label: 'Score', value: number(row.question_score) },
                {
                  label: 'Cost',
                  value: moneyEpisode(row.guesser_cost_per_episode_usd),
                },
              ]"
            />
          </div>

          <p v-if="unranked.length > 0" class="results-note">
            {{ unranked.length }} model{{ unranked.length === 1 ? " is" : "s are" }}
            not ranked because a question score, terminal episode, Guesser call, or
            positive recorded Guesser cost is unavailable.
          </p>
        </div>
      </section>

      <section class="content-section definition-section">
        <div class="content-inner metric-definition">
          <div>
            <p class="eyebrow">Definition</p>
            <h2>Cost-adjusted question score.</h2>
          </div>
          <div>
            <code>question score × (Guesser cost ÷ terminal episodes)</code>
            <ol>
              <li>
                Average penalized trial values within each subject, then average the
                subject averages.
              </li>
              <li>
                Divide the run's recorded Guesser cost by its terminal episodes.
              </li>
              <li>Multiply the exact values. Lower is better.</li>
            </ol>
            <p class="metric-example">
              Example:
              <strong>
                12.3 questions × $0.0500 per episode = 0.615 USD·questions per
                episode.
              </strong>
            </p>
            <p>
              Failed trials already use the declared failure penalty in the Question
              Score. This metric adds no further failure penalty.
            </p>
            <p>
              Ranking uses exact values; displayed values are rounded. Full benchmark
              cost is excluded because support-model pricing describes benchmark
              operation, not the model under test.
            </p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.results-summary,
.efficiency-panel,
.tradeoff-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.metric-definition h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.2rem, 4.8vw, 4.6rem);
  font-weight: 500;
  letter-spacing: -0.05em;
  line-height: 0.98;
}

.results-table {
  min-width: 980px;
}

.definition-section {
  background: var(--paper-bright);
}

.metric-definition {
  display: grid;
  grid-template-columns: minmax(14rem, 0.42fr) minmax(0, 1fr);
  gap: clamp(2rem, 7vw, 7rem);
}

.metric-definition > div:last-child {
  max-width: 50rem;
}

.metric-definition code {
  display: block;
  padding: 1rem;
  border: var(--rule-default);
  background: white;
  overflow-wrap: anywhere;
  font-size: clamp(0.8rem, 1.6vw, 1rem);
}

.metric-definition p,
.metric-definition li {
  color: var(--ink-soft);
  line-height: 1.72;
}

.metric-definition ol {
  padding-left: 1.25rem;
}

.metric-example {
  padding: 1rem;
  border-left: var(--border-emphasis-width) solid var(--blue);
  background: var(--surface-accent-soft);
}

.empty-state {
  min-height: 50vh;
}

.empty-state p:last-child {
  max-width: 40rem;
  color: var(--muted);
  line-height: 1.65;
}

@media (max-width: 900px) {
  .metric-definition {
    grid-template-columns: 1fr;
  }
}
</style>
