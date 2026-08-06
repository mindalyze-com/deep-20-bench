<script setup lang="ts">
import { computed, onActivated, ref } from "vue";
import { useRouter } from "vue-router";

import EfficiencyScatter, {
  type EfficiencyPoint,
} from "@/components/EfficiencyScatter.vue";
import EfficiencyMarkerLegend from "@/components/EfficiencyMarkerLegend.vue";
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
const expandedChartDialog = ref<HTMLDialogElement | null>(null);
const expandedChartOpen = ref(false);
const router = useRouter();

const openExpandedChart = (): void => {
  const dialog = expandedChartDialog.value;
  if (dialog === null || dialog.open) return;
  dialog.showModal();
  expandedChartOpen.value = true;
};

const closeExpandedChart = (): void => {
  expandedChartDialog.value?.close();
};

const handleExpandedChartClose = (): void => {
  expandedChartOpen.value = false;
};

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Efficiency results",
    description: "Compare normalized distance from the lower-left cost and quality ideal.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);

const idealDistanceRank = (row: LeaderboardRow): number | null =>
  row.ideal_distance_rank ?? row.efficiency_rank;

const ranked = computed(() =>
  leaderboard.value
    .filter(
      (row) => idealDistanceRank(row) !== null && row.ideal_distance_score !== null,
    )
    .sort(
      (left, right) =>
        (idealDistanceRank(left) ?? Number.MAX_SAFE_INTEGER) -
          (idealDistanceRank(right) ?? Number.MAX_SAFE_INTEGER) ||
        left.model.display_name.localeCompare(right.model.display_name),
    ),
);

const unranked = computed(() =>
  leaderboard.value.filter((row) => idealDistanceRank(row) === null),
);

const paretoCount = computed(
  () => ranked.value.filter((row) => row.pareto_efficient).length,
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
    value: costRange.value === null ? "-" : `${number(costRange.value, 0)}×`,
  },
  {
    key: "pareto",
    label: "Pareto-efficient",
    value: `${paretoCount.value} of ${ranked.value.length}`,
    tone: "accent",
  },
  { key: "direction", label: "Direction", value: "Lower is better" },
]);

const efficiencyBars = computed(() =>
  ranked.value.map((row) => ({
    label: row.model.display_name,
    value: Number(row.ideal_distance_score),
    display: number(row.ideal_distance_score, 3),
    detail: `${number(row.normalized_question_score, 3)} normalized questions · ${number(
      row.normalized_guesser_cost,
      3,
    )} normalized cost`,
    link:
      row.execution_id === null ? undefined : `/runs/${row.execution_id}/`,
  })),
);

const efficiencyPoints = computed<EfficiencyPoint[]>(() =>
  ranked.value.map((row) => ({
    label: row.model.display_name,
    rank: idealDistanceRank(row) ?? 0,
    cost: Number(row.guesser_cost_per_episode_usd ?? 0),
    costDisplay: moneyEpisode(row.guesser_cost_per_episode_usd),
    score: Number(row.question_score ?? 0),
    scoreDisplay: number(row.question_score),
    normalizedCost: Number(row.normalized_guesser_cost ?? 0),
    normalizedScore: Number(row.normalized_question_score ?? 0),
    distanceDisplay: number(row.ideal_distance_score, 3),
    paretoEfficient: row.pareto_efficient,
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
                <p class="eyebrow">Official efficiency ranking</p>
                <h2 id="efficiency-title">Distance from the lower-left ideal.</h2>
              </div>
              <p>
                Question score and model cost are each normalized from 0 to 1 across
                this cohort. The ranking measures equal-weight distance from their
                combined minimum. Lower is better.
              </p>
              <ResultHelp label="Efficiency ranking explanations">
                <InfoPopover label="Ideal distance">
                  <p>
                    A score of 0 would match the cohort's lowest question score and lowest
                    model cost. The theoretical maximum is 1.414. The score changes when
                    the compared cohort changes.
                  </p>
                </InfoPopover>
              </ResultHelp>
            </header>
            <MetricBars
              :items="efficiencyBars"
              direction-label="Normalized distance · lower is better"
              color="efficiency"
            />
          </section>

          <section
            class="tradeoff-panel panel-frame"
            aria-labelledby="tradeoff-title"
          >
            <div class="tradeoff-layout">
              <header class="tradeoff-copy">
                <p class="eyebrow">Trade-off map</p>
                <h3 id="tradeoff-title">Normalized cost and question score.</h3>
                <p>
                  Both axes use the same 0-to-1 scale. Dashed curves mark equal distance
                  from the lower-left ideal.
                </p>
                <ResultHelp label="Trade-off map explanation">
                  <InfoPopover label="Trade-off map">
                    <p>
                      The map uses the normalized values emitted by the compiler. Axis tick
                      labels and tooltips show the original question score and model cost per
                      episode.
                    </p>
                  </InfoPopover>
                </ResultHelp>
                <EfficiencyMarkerLegend />
                <button
                  class="button button-secondary chart-expand-button"
                  type="button"
                  aria-haspopup="dialog"
                  @click="openExpandedChart"
                >
                  Expand graph
                  <span class="chart-expand-icon" aria-hidden="true">↗</span>
                </button>
              </header>
              <div class="tradeoff-visual">
                <EfficiencyScatter :items="efficiencyPoints" />
              </div>
            </div>
          </section>

          <dialog
            ref="expandedChartDialog"
            class="expanded-chart-dialog"
            aria-labelledby="expanded-tradeoff-title"
            aria-describedby="expanded-tradeoff-description"
            @close="handleExpandedChartClose"
          >
            <div class="expanded-chart-layout">
              <header class="expanded-chart-copy">
                <div>
                  <p class="eyebrow">Expanded trade-off map</p>
                  <h2 id="expanded-tradeoff-title">
                    Normalized cost and question score.
                  </h2>
                </div>
                <p id="expanded-tradeoff-description">
                  Lower-left is better. Curves show equal distance from the ideal.
                </p>
                <div class="expanded-chart-legend">
                  <EfficiencyMarkerLegend />
                </div>
                <button
                  class="button button-secondary expanded-chart-close"
                  type="button"
                  @click="closeExpandedChart"
                >
                  Close expanded graph
                </button>
              </header>
              <div class="expanded-chart-visual">
                <EfficiencyScatter
                  v-if="expandedChartOpen"
                  :items="efficiencyPoints"
                  expanded
                />
              </div>
            </div>
          </dialog>

          <div
            class="table-wrap ranking-table-wrap results-table-wrap"
            tabindex="0"
            aria-label="Scrollable efficiency ranking"
          >
            <table
              class="data-table ranking-table results-table efficiency-results-table"
            >
              <colgroup>
                <col class="efficiency-col--rank" />
                <col class="efficiency-col--model" />
                <col class="efficiency-col--run" />
                <col class="efficiency-col--distance" />
                <col class="efficiency-col--pareto" />
                <col class="efficiency-col--question-rank" />
                <col class="efficiency-col--question-score" />
                <col class="efficiency-col--cost" />
                <col class="efficiency-col--success" />
              </colgroup>
              <thead>
                <tr>
                  <th class="rank-column">
                    <span aria-hidden="true">#</span>
                    <span class="visually-hidden">Ideal-distance rank</span>
                  </th>
                  <th class="model-column">Model</th>
                  <th class="run-column">Run</th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>Ideal</span>
                      <span>distance</span>
                    </span>
                  </th>
                  <th class="pareto-column">
                    <span class="table-header-stack table-header-stack--center">
                      <span>Pareto</span>
                      <span>efficient</span>
                    </span>
                  </th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>Question</span>
                      <span>rank</span>
                    </span>
                  </th>
                  <th data-numeric>
                    <span class="table-header-stack">
                      <span>Question</span>
                      <span>score</span>
                    </span>
                  </th>
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
                  <td class="rank-column">{{ idealDistanceRank(row) }}</td>
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
                    <span v-else aria-hidden="true">-</span>
                  </td>
                  <td data-numeric>
                    {{ number(row.ideal_distance_score, 3) }}
                  </td>
                  <td class="pareto-column">
                    <span v-if="row.pareto_efficient" class="pareto-badge">
                      Yes
                    </span>
                    <span v-else aria-hidden="true">-</span>
                  </td>
                  <td data-numeric>{{ row.rank ?? "-" }}</td>
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
              :rank="idealDistanceRank(row) ?? '-'"
              :name="row.model.display_name"
              :provider="row.model.provider"
              :to="row.execution_id === null ? null : runLink(row)"
              :metrics="[
                {
                  label: 'Ideal distance',
                  value: number(row.ideal_distance_score, 3),
                },
                { label: 'Pareto-efficient', value: row.pareto_efficient ? 'Yes' : 'No' },
                { label: 'Question score', value: number(row.question_score) },
                {
                  label: 'Model cost / episode',
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
            title="Normalized ideal distance."
            formula="√(normalized question score² + normalized model cost²)"
            interpretation="Both measures have equal weight after cohort min/max normalization. Lower is better."
            detail-summary="Steps and limits"
          >
            <ol>
              <li>
                Normalize question score as (value − cohort minimum) ÷ cohort range.
              </li>
              <li>
                Normalize model cost per episode with the same calculation.
              </li>
              <li>Measure Euclidean distance from (0, 0). Lower is better.</li>
            </ol>
            <p class="metric-example">
              <strong>
                A model with normalized question score 0.06 and normalized cost 0.08
                has distance √(0.06² + 0.08²) = 0.10.
              </strong>
            </p>
            <p>
              Question score still uses the average penalized trial values. Failed trials
              therefore remain part of the quality dimension.
            </p>
            <p>
              Adding or removing a model can change every normalized value and rank.
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

.tradeoff-panel {
  overflow: hidden;
}

.tradeoff-layout {
  display: grid;
}

.tradeoff-copy {
  display: grid;
  gap: 1rem;
  align-content: start;
  padding: clamp(1.2rem, 2.5vw, 2rem);
  border-bottom: var(--rule-default);
}

.tradeoff-copy .eyebrow,
.tradeoff-copy h3,
.tradeoff-copy > p {
  margin: 0;
}

.tradeoff-copy h3,
.expanded-chart-copy h2 {
  font-family: var(--font-display);
  font-size: var(--text-card-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.035em;
  line-height: 1;
}

.tradeoff-copy > p,
.expanded-chart-copy > p {
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.55;
}

.tradeoff-copy .result-help {
  padding-block: 0.25rem 0.85rem;
  border-bottom: var(--rule-subtle);
}

.chart-expand-button,
.expanded-chart-close {
  width: max-content;
  max-width: 100%;
}

.chart-expand-button {
  margin-top: 0.35rem;
  padding-inline: 0;
  border: 0;
  border-bottom: 1px solid color-mix(in srgb, currentColor 34%, transparent);
  border-radius: 0;
  color: var(--muted);
  background: transparent;
  box-shadow: none;
  font-size: var(--text-micro);
  letter-spacing: 0.015em;
}

.chart-expand-button:hover {
  border-bottom-color: currentColor;
  color: var(--result-accent-ink);
  background: transparent;
}

.chart-expand-icon {
  margin-left: 0.2rem;
  font-size: 0.85em;
}

.tradeoff-visual,
.expanded-chart-visual {
  min-width: 0;
}

.expanded-chart-dialog {
  width: min(96vw, 1740px);
  max-width: none;
  height: min(94dvh, 1000px);
  max-height: none;
  padding: 0;
  overflow: hidden;
  border: var(--rule-strong);
  background: var(--surface-raised);
  color: var(--ink);
}

.expanded-chart-dialog::backdrop {
  background: rgb(12 17 27 / 78%);
}

.expanded-chart-layout {
  display: grid;
  grid-template-columns: minmax(15rem, 18rem) minmax(0, 1fr);
  height: 100%;
}

.expanded-chart-copy {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  padding: clamp(1.3rem, 2.5vw, 2.25rem);
  overflow: auto;
  border-right: var(--rule-default);
}

.expanded-chart-copy .eyebrow,
.expanded-chart-copy h2,
.expanded-chart-copy > p {
  margin: 0;
}

.expanded-chart-close {
  margin-top: auto;
}

.expanded-chart-visual {
  overflow: auto;
}

@media (min-width: 1100px) {
  .tradeoff-layout {
    grid-template-columns: minmax(17rem, 22rem) minmax(0, 1fr);
  }

  .tradeoff-copy {
    border-right: var(--rule-default);
    border-bottom: 0;
  }
}

@media (max-width: 760px) {
  .tradeoff-panel {
    margin-bottom: 2rem;
    overflow: hidden;
    border: var(--rule-default);
    background: var(--surface-raised);
  }

  .tradeoff-layout {
    gap: 0;
  }

  .tradeoff-copy,
  .tradeoff-visual {
    border: 0;
    background: transparent;
  }

  .tradeoff-copy {
    border-bottom: var(--rule-default);
  }

  .expanded-chart-dialog {
    width: 100vw;
    height: 100dvh;
    margin: 0;
    overflow: hidden;
    border: 0;
  }

  .expanded-chart-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    height: 100%;
    min-height: 0;
  }

  .expanded-chart-copy {
    display: grid;
    grid-template-areas:
      "title close"
      "description description";
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.4rem 0.75rem;
    align-items: start;
    padding: max(0.8rem, env(safe-area-inset-top))
      max(1rem, env(safe-area-inset-right)) 0.8rem
      max(1rem, env(safe-area-inset-left));
    overflow: visible;
    border-right: 0;
    border-bottom: var(--rule-default);
  }

  .expanded-chart-copy > div:first-child {
    grid-area: title;
  }

  .expanded-chart-copy .eyebrow,
  .expanded-chart-legend {
    display: none;
  }

  .expanded-chart-copy h2 {
    font-size: clamp(1.15rem, 5vw, 1.4rem);
    line-height: 1.05;
  }

  .expanded-chart-copy > p {
    grid-area: description;
    font-size: var(--text-micro);
    line-height: 1.4;
  }

  .expanded-chart-close {
    grid-area: close;
    min-height: 44px;
    margin: 0;
  }

  .expanded-chart-visual {
    display: grid;
    min-height: 0;
    align-items: center;
    overflow: hidden;
  }
}

@media (max-width: 620px) {
  .mobile-result-list {
    margin-top: 0;
  }
}

.results-table {
  min-width: 980px;
}

.efficiency-results-table {
  min-width: 72rem;
  table-layout: fixed;
}

.efficiency-results-table .rank-column,
.efficiency-results-table .model-column,
.efficiency-results-table .run-column {
  width: auto;
  min-width: 0;
}

.efficiency-results-table .efficiency-col--rank {
  width: 4%;
}

.efficiency-results-table .efficiency-col--model {
  width: 20%;
}

.efficiency-results-table .efficiency-col--run {
  width: 8%;
}

.efficiency-results-table .efficiency-col--distance {
  width: 10%;
}

.efficiency-results-table .efficiency-col--pareto {
  width: 10%;
}

.efficiency-results-table .efficiency-col--question-rank {
  width: 11%;
}

.efficiency-results-table .efficiency-col--question-score {
  width: 12%;
}

.efficiency-results-table .efficiency-col--cost {
  width: 15%;
}

.efficiency-results-table .efficiency-col--success {
  width: 10%;
}

.efficiency-results-table .pareto-column {
  padding-inline: 0.5rem;
  text-align: center;
}

.table-header-stack--center {
  align-items: center;
}

.pareto-badge {
  display: inline-flex;
  align-items: center;
  min-height: 1.6rem;
  padding: 0.15rem 0.45rem;
  border: 1px solid var(--result-accent);
  border-radius: 999px;
  color: var(--result-accent-ink);
  background: var(--result-accent-soft);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
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
