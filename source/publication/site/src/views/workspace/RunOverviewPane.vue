<script setup lang="ts">
import { computed } from "vue";

import ContractStatusCard from "@/components/ContractStatusCard.vue";
import CostDonut, { type CostDonutItem } from "@/components/CostDonut.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import { readChartTheme } from "@/lib/chart-theme";
import {
  dateTime,
  duration,
  integer,
  money,
  number,
  percent,
} from "@/lib/format";
import { useRunWorkspace } from "@/lib/workspace-context";

const { run, subjects } = useRunWorkspace();

const costLedger = computed<CostDonutItem[]>(() => {
  const current = run.value;
  if (current === null) return [];
  const colors = readChartTheme().roles;
  return [
    {
      label: "Guesser",
      value: Number(current.totals.costs_usd.guesser),
      display: money(current.totals.costs_usd.guesser),
      color: colors.guesser,
      primary: true,
    },
    {
      label: "Primary Oracle",
      value: Number(current.totals.costs_usd.primary_oracle),
      display: money(current.totals.costs_usd.primary_oracle),
      color: colors.oracle,
    },
    {
      label: "Reviewer",
      value: Number(current.totals.costs_usd.reviewer),
      display: money(current.totals.costs_usd.reviewer),
      color: colors.reviewer,
    },
    {
      label: "Judge",
      value: Number(current.totals.costs_usd.judge),
      display: money(current.totals.costs_usd.judge),
      color: colors.judge,
    },
    {
      label: "Validator",
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
      value: percent(current.contract.compliance_rate),
      tone: current.contract.status === "breached" ? "danger" : "default",
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
</script>

<template>
  <article v-if="run" class="run-overview-pane pane-scroll">
    <header class="run-workspace-hero">
      <div>
        <p class="eyebrow">Certified official run</p>
        <h1>{{ run.model_name }}</h1>
        <p class="run-deck">
          One model, {{ subjects.length }} subjects, and {{ run.terminal_trials }} scored
          episodes. Choose a subject to inspect its attempts.
        </p>
      </div>
      <QuestionScore
        class="run-primary-score"
        :score="run.question_score"
        :max-questions="run.max_questions"
        label="Question score"
        explain
        :confidence-interval="run.question_score_confidence_interval"
      />
    </header>

    <MetricGrid
      class="workspace-metrics"
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

    <div class="run-overview-grid">
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
      </section>

      <ContractStatusCard
        :contract="run.contract"
        affected-unit="episodes"
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
  padding: clamp(1.5rem, 3.5vw, 3.5rem);
}

.run-workspace-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(17rem, 0.55fr);
  gap: clamp(2rem, 6vw, 6rem);
  align-items: end;
  max-width: var(--workspace-content);
  margin: 0 auto;
  padding: clamp(1.2rem, 3vw, 3rem) 0 clamp(2rem, 4vw, 3.5rem);
}

.run-workspace-hero h1 {
  max-width: 10ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.2rem, 6vw, 6rem);
  font-weight: 500;
  letter-spacing: -0.058em;
  line-height: 0.92;
}

.run-deck {
  max-width: 46rem;
  margin: 1.2rem 0 0;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.65;
}

.run-primary-score {
  padding: 1.35rem;
  border-top: var(--border-emphasis-width) solid var(--blue);
  background: var(--paper-bright);
}

.run-primary-score :deep(strong) {
  font-size: clamp(3.5rem, 7vw, 6rem);
}

.workspace-metrics {
  max-width: var(--workspace-content);
  margin: 0 auto 1px;
}

.run-totals dt,
.provenance-card dt {
  color: var(--muted);
  font-size: var(--text-caption);
  font-weight: 760;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.run-overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(18rem, 0.85fr);
  max-width: var(--workspace-content);
  margin: 0 auto;
  border: solid var(--line);
  border-width: 0 1px 1px;
  background: var(--line);
  gap: 1px;
}

.workspace-card {
  min-width: 0;
  padding: clamp(1.25rem, 2.5vw, 2rem);
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
  font-size: clamp(1.8rem, 3vw, 2.7rem);
  font-weight: 500;
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
  font-weight: 700;
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

.mobile-subjects {
  display: none;
}

@media (max-width: 1050px) {
  .run-workspace-hero,
  .run-overview-grid {
    grid-template-columns: 1fr;
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
    font-size: clamp(2.8rem, 12vw, 3.8rem);
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

  .run-primary-score :deep(strong) {
    font-size: 3.6rem;
  }

  .workspace-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .run-overview-grid {
    border-top-width: 0;
  }

  .run-totals dl {
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
    font-weight: 500;
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
    font-weight: 760;
  }
}
</style>
