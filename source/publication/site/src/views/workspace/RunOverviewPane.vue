<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { RouteLocationRaw } from "vue-router";

import ContractStatusCard from "@/components/ContractStatusCard.vue";
import CostDonut, { type CostDonutItem } from "@/components/CostDonut.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import ModelName from "@/components/ModelName.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import RunModelsSection from "@/components/run/RunModelsSection.vue";
import { getSubject } from "@/lib/api";
import { readChartTheme } from "@/lib/chart-theme";
import {
  contractExampleRoute,
  firstBreachedTrial,
} from "@/lib/contract-example";
import {
  contractPercent,
  dateTime,
  duration,
  integer,
  money,
  number,
  percent,
} from "@/lib/format";
import { runRoleCopy, runRoleOrder } from "@/lib/run-roles";
import { useRunWorkspace } from "@/lib/workspace-context";

const { run, subjects } = useRunWorkspace();
const exampleTo = ref<RouteLocationRaw | null>(null);
let exampleRequest = 0;

watch(
  [run, subjects],
  ([currentRun, currentSubjects]) => {
    const request = ++exampleRequest;
    exampleTo.value = null;
    const breachedSubject = currentSubjects.find(
      (subject) => subject.contract.status === "breached",
    );
    if (currentRun === null || breachedSubject === undefined) return;
    void getSubject(currentRun.execution_id, breachedSubject.target_id)
      .then((document) => {
        if (request !== exampleRequest) return;
        const example = firstBreachedTrial(document.trials);
        if (example === null) return;
        exampleTo.value = contractExampleRoute(
          currentRun.execution_id,
          breachedSubject.target_id,
          example.trial_id,
        );
      })
      .catch(() => {
        if (request === exampleRequest) exampleTo.value = null;
      });
  },
  { immediate: true },
);

const costLedger = computed<CostDonutItem[]>(() => {
  const current = run.value;
  if (current === null) return [];
  const colors = readChartTheme().roles;
  return [
    {
      label: runRoleCopy.guesser.costLabel,
      value: Number(current.totals.costs_usd.guesser),
      display: money(current.totals.costs_usd.guesser),
      color: colors.guesser,
      primary: true,
    },
    {
      label: runRoleCopy.oracle.costLabel,
      value: Number(current.totals.costs_usd.primary_oracle),
      display: money(current.totals.costs_usd.primary_oracle),
      color: colors.oracle,
    },
    {
      label: runRoleCopy.reviewer.costLabel,
      value: Number(current.totals.costs_usd.reviewer),
      display: money(current.totals.costs_usd.reviewer),
      color: colors.reviewer,
    },
    {
      label: runRoleCopy.judge.costLabel,
      value: Number(current.totals.costs_usd.judge),
      display: money(current.totals.costs_usd.judge),
      color: colors.judge,
    },
    {
      label: runRoleCopy.validator.costLabel,
      value: Number(current.totals.costs_usd.validator),
      display: money(current.totals.costs_usd.validator),
      color: colors.validator,
    },
  ];
});

const summaryMetrics = computed<MetricGridItem[]>(() => {
  const current = run.value;
  if (current === null) return [];
  return [
    {
      key: "success",
      label: "Success",
      value: percent(current.success_rate),
    },
    {
      key: "contract",
      label: "Contract compliance",
      value: contractPercent(
        current.contract.compliance_rate,
        current.contract.violations,
      ),
      tone: current.contract.status === "breached" ? "danger" : "default",
      linkLabel: exampleTo.value === null ? undefined : "View one example",
      to: exampleTo.value ?? undefined,
    },
    {
      key: "cost",
      label: "Guesser cost",
      value: money(current.totals.costs_usd.guesser),
      tone: "accent",
    },
    {
      key: "time",
      label: "Guesser time",
      value: duration(current.totals.guesser_think_time_ms),
    },
  ];
});

const roleGuide = runRoleOrder.map((role) => ({
  role,
  ...runRoleCopy[role],
}));
</script>

<template>
  <article v-if="run" class="run-overview-pane pane-scroll">
    <header class="run-workspace-hero workspace-detail-boundary">
      <div>
        <p class="eyebrow">Official run</p>
        <h1><ModelName :name="run.model_name" /></h1>
        <p class="run-deck">
          {{ run.terminal_trials }} scored episodes = {{ subjects.length }} subjects ×
          {{ run.iterations }} trials. Choose a subject to inspect its attempts.
        </p>
      </div>
      <QuestionScore
        class="run-primary-score"
        :score="run.question_score"
        :max-questions="run.max_questions"
        label="Question score"
        variant="wide"
        explain
        :confidence-interval="run.question_score_confidence_interval"
      />
    </header>

    <MetricGrid
      class="workspace-metrics workspace-detail-boundary"
      :items="summaryMetrics"
      label="Run summary"
      :max-columns="4"
    />

    <section class="mobile-subjects" aria-labelledby="mobile-subjects-title">
      <header>
        <p class="eyebrow">Drill down</p>
        <h2 id="mobile-subjects-title">Subjects.</h2>
      </header>
      <RouterLink
        v-for="(subject, index) in subjects"
        :key="subject.target_id"
        :to="{
          name: 'subject',
          params: {
            executionId: run.execution_id,
            targetId: subject.target_id,
          },
        }"
      >
        <span>{{ String(index + 1).padStart(2, "0") }}</span>
        <strong>{{ subject.display_name }}</strong>
        <small>{{ number(subject.average_questions) }} avg</small>
        <span aria-hidden="true">→</span>
      </RouterLink>
    </section>

    <div class="run-overview-grid workspace-detail-boundary">
      <div class="run-overview-stack">
        <section class="workspace-card run-totals" aria-labelledby="run-totals-title">
          <header class="workspace-card-heading">
            <div>
              <p class="eyebrow">Complete benchmark</p>
              <h2 id="run-totals-title">Run ledger.</h2>
            </div>
            <p>All Guesser and benchmark-support activity.</p>
          </header>
          <dl>
            <div>
              <dt>Total tokens</dt>
              <dd>{{ integer(run.totals.total_tokens) }}</dd>
            </div>
            <div>
              <dt>Wall-clock runtime</dt>
              <dd>{{ duration(run.totals.runtime_ms) }}</dd>
            </div>
            <div>
              <dt>Guesser calls</dt>
              <dd>{{ integer(run.totals.guesser_calls) }}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{{ dateTime(run.completed_at) }}</dd>
            </div>
          </dl>
        </section>

        <ContractStatusCard
          :contract="run.contract"
          affected-unit="episodes"
          :example-to="exampleTo"
        />

        <section class="workspace-card provenance-card">
          <p class="eyebrow">Provenance</p>
          <dl>
            <div><dt>Execution</dt><dd><code>{{ run.execution_id }}</code></dd></div>
            <div><dt>Model ID</dt><dd><code>{{ run.model_id }}</code></dd></div>
            <div><dt>Benchmark</dt><dd><code>{{ run.benchmark_id }}</code></dd></div>
            <div><dt>Base seed</dt><dd><code>{{ run.base_seed }}</code></dd></div>
            <div><dt>Git commit</dt><dd><code>{{ run.git_commit.slice(0, 12) }}</code></dd></div>
          </dl>
        </section>
      </div>

      <section class="workspace-card role-ledger" aria-labelledby="role-ledger-title">
        <header class="workspace-card-heading">
          <div>
            <p class="eyebrow">Recorded cost</p>
            <h2 id="role-ledger-title">By role.</h2>
          </div>
        </header>
        <CostDonut
          :items="costLedger"
          :total-display="money(run.totals.costs_usd.total)"
        />
        <div class="role-guide">
          <p>Roles in this cost:</p>
          <dl>
            <div v-for="role in roleGuide" :key="role.role">
              <dt>{{ role.costLabel }}</dt>
              <dd>{{ role.description }}</dd>
            </div>
          </dl>
          <RouterLink :to="{ name: 'methodology', hash: '#answer-checks' }">
            Read the role and answer-checking method →
          </RouterLink>
        </div>
      </section>
    </div>

    <RunModelsSection
      v-if="run.models.length > 0"
      class="workspace-detail-boundary"
      :models="run.models"
    />

  </article>
</template>

<style scoped>
.pane-scroll {
  height: 100%;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  scrollbar-gutter: stable;
}

.run-overview-pane {
  --run-overview-column: minmax(0, 1fr);

  padding: var(--workspace-gutter);
}

.run-workspace-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(19rem, 0.65fr);
  gap: clamp(2rem, 5vw, 5rem);
  align-items: center;
  padding: clamp(0.5rem, 1vw, 1rem) 0 clamp(1.5rem, 3vw, 2.5rem);
}

.run-workspace-hero > div:first-child {
  margin-top: 0;
}

.run-workspace-hero h1 {
  max-width: 14ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-workspace-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.058em;
  line-height: var(--text-workspace-title--line-height);
}

.run-workspace-hero h1 :deep(.model-name) {
  row-gap: 0.35rem;
}

.run-deck {
  max-width: 46rem;
  margin: 1.2rem 0 0;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.65;
}

.run-primary-score {
  padding: clamp(0.95rem, 1.25vw, 1.15rem);
  border-top: var(--border-emphasis-width) solid var(--blue);
  background: var(--paper-bright);
}

.workspace-metrics {
  grid-template-columns: repeat(4, var(--run-overview-column));
  margin-bottom: 0;
}

.run-totals dt,
.provenance-card dt {
  color: var(--muted);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.run-overview-grid {
  display: grid;
  grid-template-columns: repeat(2, var(--run-overview-column));
  align-items: stretch;
  margin-top: -1px;
  background: transparent;
  gap: 0;
}

.run-overview-stack {
  display: grid;
  min-width: 0;
  grid-template-rows: auto auto minmax(0, 1fr);
}

.run-overview-stack > * + * {
  margin-top: -1px;
}

.role-ledger {
  margin-left: -1px;
}

.workspace-card {
  min-width: 0;
  padding: var(--workspace-panel-padding);
  border: var(--rule-default);
  background: var(--paper-bright);
}

.workspace-card-heading {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: end;
  margin-bottom: 1.4rem;
}

.workspace-card-heading h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-card-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.045em;
  line-height: 1;
}

.workspace-card-heading > p {
  max-width: 18rem;
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
  line-height: 1.5;
}

.run-totals dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
  border: var(--rule-subtle);
}

.run-totals dl > div {
  min-width: 0;
  padding: 1rem;
  border-right: var(--rule-subtle);
  border-bottom: var(--rule-subtle);
}

.run-totals dl > div:nth-child(even) {
  border-right: 0;
}

.run-totals dl > div:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.run-totals dd {
  margin: 0.4rem 0 0;
  font-size: 0.9rem;
  font-weight: var(--font-weight-bold);
}

.provenance-card dl {
  display: grid;
  gap: 0.7rem;
  margin: 0;
}

.provenance-card dl > div {
  display: grid;
  grid-template-columns: 5rem minmax(0, 1fr);
  gap: 0.8rem;
}

.provenance-card dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 0.72rem;
}

.role-guide {
  margin-top: 1.2rem;
  padding-top: 1rem;
  border-top: var(--rule-subtle);
}

.role-guide > p {
  margin: 0 0 0.75rem;
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.role-guide dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem 1rem;
  margin: 0 0 1rem;
}

.role-guide dl > div {
  min-width: 0;
}

.role-guide dt {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.role-guide dd {
  margin: 0.18rem 0 0;
  color: var(--muted);
  font-size: var(--text-caption);
  line-height: 1.45;
}

.role-guide a {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.mobile-subjects {
  display: none;
}

@media (max-width: 1050px) {
  .run-workspace-hero,
  .run-overview-grid {
    grid-template-columns: 1fr;
  }

  .role-ledger {
    margin-top: -1px;
    margin-left: 0;
  }
}

@media (max-width: 760px) {
  .pane-scroll {
    height: auto;
    overflow: visible;
    scrollbar-gutter: auto;
  }

  .run-overview-pane {
    padding: 1.2rem 1rem 2rem;
    scrollbar-gutter: auto;
  }

  .run-workspace-hero {
    gap: 1rem;
    padding: 0.35rem 0 1.35rem;
  }

  .run-workspace-hero h1 {
    max-width: 12ch;
    font-size: clamp(2.6rem, 11vw, 3.6rem);
    line-height: 0.94;
  }

  .run-deck {
    margin-top: 0.9rem;
    font-size: 0.9rem;
    line-height: 1.55;
  }

  .run-primary-score {
    padding: 1rem 1.15rem;
  }

  .workspace-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .run-totals dl {
    grid-template-columns: 1fr;
  }

  .role-guide dl {
    grid-template-columns: 1fr;
  }

  .run-totals dl > div {
    border-right: 0;
  }

  .run-totals dl > div:nth-last-child(2) {
    border-bottom: var(--rule-subtle);
  }

  .mobile-subjects {
    display: grid;
    margin: 1px 0;
    border: var(--rule-default);
    background: var(--paper-bright);
  }

  .mobile-subjects header {
    padding: 1.3rem 1rem;
    border-bottom: var(--rule-default);
  }

  .mobile-subjects h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 2.5rem;
    font-weight: var(--font-weight-medium);
  }

  .mobile-subjects a {
    display: grid;
    grid-template-columns: 1.7rem minmax(0, 1fr) auto auto;
    gap: 0.7rem;
    align-items: center;
    min-height: 58px;
    padding: 0.75rem 1rem;
    border-bottom: var(--rule-subtle);
    text-decoration: none;
  }

  .mobile-subjects a:last-child {
    border-bottom: 0;
  }

  .mobile-subjects a:hover {
    background: var(--surface-accent-soft);
  }

  .mobile-subjects a:active {
    background: var(--surface-rail);
  }

  .mobile-subjects a:focus-visible {
    z-index: 1;
    outline: var(--focus-ring);
    outline-offset: -3px;
  }

  .mobile-subjects a > span:first-child,
  .mobile-subjects small {
    color: var(--muted);
    font-size: var(--text-caption);
  }

  .mobile-subjects strong {
    overflow: hidden;
    font-size: 0.78rem;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mobile-subjects a > span:last-child {
    color: var(--blue-ink);
    font-size: 0.9rem;
    font-weight: var(--font-weight-bold);
  }
}
</style>
