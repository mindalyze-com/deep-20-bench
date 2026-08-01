<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import EfficiencyScatter, {
  type EfficiencyPoint,
} from "@/components/EfficiencyScatter.vue";
import ErrorState from "@/components/ErrorState.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import MetricDefinitionCard from "@/components/MetricDefinitionCard.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import MobileResultCard from "@/components/MobileResultCard.vue";
import ModelRunLink from "@/components/ModelRunLink.vue";
import ResultHelp from "@/components/ResultHelp.vue";
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
    label: "Model cost range",
    value: costRange.value === null ? "—" : `${number(costRange.value, 0)}×`,
  },
  {
    key: "best",
    label: "Lowest adjusted score",
    value: number(ranked.value[0]?.cost_adjusted_question_score, 3),
    tone: "accent",
  },
  { key: "direction", label: "Direction", value: "Lower is better" },
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
          Efficiency is available when a model has a question score and a positive
          recorded model cost for completed episodes.
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

          <section
            class="panel result-chart-panel efficiency-panel"
            aria-labelledby="efficiency-title"
          >
            <header class="panel-heading panel-heading--with-help">
              <div>
                <p class="eyebrow">Official ranking</p>
                <h2 id="efficiency-title">Cost-adjusted score.</h2>
              </div>
              <p>
                This ranking multiplies question score by tested-model cost per episode.
                Lower is better: a model improves by using fewer questions, costing less,
                or both.
              </p>
              <ResultHelp label="Efficiency ranking explanations">
                <InfoPopover label="Adjusted score">
                  <p>
                    This score multiplies question score by tested-model cost per episode.
                    Lower is better. Its unit is USD·questions per episode, not raw dollar
                    cost.
                  </p>
                </InfoPopover>
                <InfoPopover label="Model cost range">
                  <p>
                    This is the highest tested-model cost per episode divided by the lowest.
                    It shows how far apart the least and most expensive models are.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <MetricBars
              :items="efficiencyBars"
              direction-label="USD·questions per episode · lower is better"
              color="efficiency"
            />
          </section>

          <section
            class="tradeoff-panel panel-frame result-chart-panel"
            aria-labelledby="tradeoff-title"
          >
            <header
              class="panel-heading panel-heading--with-help panel-heading--compact"
            >
              <div>
                <p class="eyebrow">Trade-off map</p>
                <h3 id="tradeoff-title">Cost and question score.</h3>
              </div>
              <p>
                Further left means lower model cost. Lower means a better question score.
                The lower-left is favorable; this chart does not change the efficiency rank.
              </p>
              <ResultHelp label="Trade-off map explanation">
                <InfoPopover label="Trade-off map">
                  <p>
                    The map shows the original cost and question score on separate axes. It
                    does not add another weighted score or change the efficiency rank.
                  </p>
                </InfoPopover>
              </ResultHelp>
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
                      <span>Model cost</span>
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
                  label: 'Adjusted score',
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
            not ranked because a question score or positive recorded model cost per
            completed episode is unavailable.
          </p>

          <MetricDefinitionCard
            title="Cost-adjusted score."
            formula="question score × (tested-model cost ÷ terminal episodes)"
            interpretation="Question score and tested-model cost per episode are multiplied. Lower is better."
            detail-summary="Steps, example, scoring treatment, and scope"
          >
            <ol>
              <li>
                Average penalized trial values within each subject, then average the
                subject averages.
              </li>
              <li>
                Divide the run's recorded tested-model cost by its terminal episodes.
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
          </MetricDefinitionCard>
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

.results-table {
  min-width: 980px;
}

.empty-state {
  min-height: 50vh;
}

.empty-state p:last-child {
  max-width: 40rem;
  color: var(--muted);
  line-height: 1.65;
}

</style>
