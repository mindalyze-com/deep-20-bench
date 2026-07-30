<script setup lang="ts">
import { computed, onActivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import MetricBars from "@/components/MetricBars.vue";
import ResultsNav from "@/components/ResultsNav.vue";
import StackedMetricBars, {
  type StackedBarRow,
  type StackedBarSegment,
} from "@/components/StackedMetricBars.vue";
import { getOfficialRuns } from "@/lib/api";
import { money, moneyDetailed, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { PublicRunSummary, RunDocument } from "@/lib/types";

const documents = ref<RunDocument[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Cost results",
    description: "Compare recorded Deep20Bench run costs by model and component.",
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
        Number(left.totals.costs_usd.total) - Number(right.totals.costs_usd.total) ||
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

const totalCostBars = computed(() =>
  runs.value.map((run) => ({
    label: run.model_name,
    value: Number(run.totals.costs_usd.total),
    display: moneyDetailed(run.totals.costs_usd.total),
    detail: `${moneyDetailed(run.totals.costs_usd.guesser)} Guesser · ${moneyDetailed(
      Number(run.totals.costs_usd.total) - Number(run.totals.costs_usd.guesser),
    )} support`,
    link: `/runs/${run.execution_id}/`,
  })),
);

const componentRows = [
  { key: "guesser", label: "Guesser", color: "#4e64ff" },
  { key: "primary_oracle", label: "Primary Oracle", color: "#ef5435" },
  { key: "reviewer", label: "Reviewer", color: "#91a72b" },
  { key: "judge", label: "Judge", color: "#8a72cf" },
  { key: "validator", label: "Validator", color: "#8b8f99" },
] as const;

const stackedSegments: StackedBarSegment[] = componentRows.map((component) => ({
  label: component.label,
  color: component.color,
}));

const componentValue = (
  run: PublicRunSummary,
  key: (typeof componentRows)[number]["key"],
): number => Number(run.totals.costs_usd[key]);

const stackedRows = computed<StackedBarRow[]>(() =>
  runs.value.map((run) => ({
    label: run.model_name,
    display: moneyDetailed(run.totals.costs_usd.total),
    values: componentRows.map((component) =>
      componentValue(run, component.key),
    ),
    details: componentRows.map((component) =>
      moneyDetailed(componentValue(run, component.key)),
    ),
    link: `/runs/${run.execution_id}/`,
  })),
);

const costBand = (index: number): "good" | "middle" | "bad" => {
  const position = runs.value.length <= 1 ? 0.5 : index / (runs.value.length - 1);
  if (position <= 1 / 3) return "good";
  if (position >= 2 / 3) return "bad";
  return "middle";
};

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
          <p class="eyebrow">Cost</p>
          <h1>What each run cost.</h1>
        </div>
        <p>
          Provider-reported costs recorded when each run completed. These are historical
          measurements, not current price estimates.
        </p>
      </div>
    </section>

    <ResultsNav />

    <LoadingState v-if="loading" label="Loading cost results" />
    <ErrorState v-else-if="error !== null" :message="error" />

    <section v-else-if="runs.length === 0" class="content-section empty-state">
      <div class="content-inner">
        <p class="eyebrow">Cost</p>
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
            <dt>Recorded spend</dt>
            <dd>{{ money(totalSpend) }}</dd>
          </div>
          <div>
            <dt>Guesser spend</dt>
            <dd>{{ money(guesserSpend) }}</dd>
          </div>
          <div>
            <dt>Support share</dt>
            <dd>{{ percent(supportShare) }}</dd>
          </div>
        </dl>

        <section class="panel cost-panel" aria-labelledby="cost-chart-title">
          <header class="panel-heading">
            <div>
              <p class="eyebrow">Full-run cost</p>
              <h2 id="cost-chart-title">Least to most expensive.</h2>
            </div>
            <p>
              Guesser is the model under test. Primary Oracle, Reviewer, Judge, and
              Validator are benchmark-support costs.
            </p>
          </header>
          <MetricBars
            :items="totalCostBars"
            direction-label="Full-run cost · lower is better"
            color="coral"
            value-format="currency"
          />

          <section class="component-ledger" aria-labelledby="component-ledger-title">
            <header>
              <div>
                <p class="eyebrow">Composition</p>
                <h3 id="component-ledger-title">Where each run spent.</h3>
              </div>
              <p>
                Bar length shows full-run cost. Color separates the Guesser from
                benchmark-support roles.
              </p>
            </header>
            <StackedMetricBars
              :rows="stackedRows"
              :segments="stackedSegments"
              direction-label="Full-run cost by component"
            />
          </section>
        </section>

        <div
          class="table-wrap results-table-wrap"
          tabindex="0"
          aria-label="Scrollable cost comparison"
        >
          <table class="data-table results-table">
            <thead>
              <tr>
                <th>Cost rank</th>
                <th>Model</th>
                <th data-numeric>Guesser / episode</th>
                <th data-numeric>Full / episode</th>
                <th data-numeric>Support / episode</th>
                <th data-numeric>Support share</th>
                <th data-numeric>Full run</th>
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
                <td data-numeric>
                  {{ moneyDetailed(run.comparison.guesser_cost_per_episode_usd) }}
                </td>
                <td data-numeric>
                  {{ moneyDetailed(run.comparison.full_cost_per_episode_usd) }}
                </td>
                <td data-numeric>
                  {{ moneyDetailed(run.comparison.support_cost_per_episode_usd) }}
                </td>
                <td data-numeric>{{ percent(run.comparison.support_cost_share) }}</td>
                <td data-numeric>
                  <span :class="`value-signal value-signal--${costBand(index)}`">
                    {{ moneyDetailed(run.totals.costs_usd.total) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="results-note">
          Per-episode figures use terminal episodes as the denominator. This keeps
          comparisons consistent if cohort sizes change.
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
.cost-panel {
  margin-bottom: clamp(1.5rem, 4vw, 2.5rem);
}

.component-ledger {
  margin: 0;
  border-top: 1px solid var(--line);
}

.component-ledger > header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(15rem, 0.5fr);
  gap: 2rem;
  align-items: end;
  padding: clamp(1.4rem, 3vw, 2.5rem);
  border-bottom: 1px solid var(--line);
}

.component-ledger h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3.5rem);
  font-weight: 500;
  letter-spacing: -0.045em;
  line-height: 1;
}

.component-ledger > header > p {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.6;
}

.results-table {
  min-width: 960px;
}

.rank-badge {
  display: inline-grid;
  width: 1.8rem;
  aspect-ratio: 1;
  place-items: center;
  border: 1px solid var(--line);
  font-weight: 760;
}

.value-signal {
  display: inline-block;
  padding: 0.28rem 0.5rem;
  border-left: 3px solid;
  background: white;
}

.value-signal--good {
  border-color: #7ba321;
}

.value-signal--middle {
  border-color: #dd9a2f;
}

.value-signal--bad {
  border-color: var(--coral);
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

  .component-ledger > header {
    grid-template-columns: 1fr;
    gap: 0.8rem;
  }
}
</style>
