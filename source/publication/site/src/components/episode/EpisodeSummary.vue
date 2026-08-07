<script setup lang="ts">
import { computed } from "vue";

import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import { contractExampleRoute } from "@/lib/contract-example";
import { duration, moneyEpisode, number, statusLabel } from "@/lib/format";
import type {
  PublicEpisodeDetail,
  PublicRunSummary,
  PublicSubjectSummary,
  PublicTrialSummary,
} from "@/lib/types";

const props = defineProps<{
  run: PublicRunSummary;
  subject: PublicSubjectSummary;
  trial: PublicTrialSummary;
  episode: PublicEpisodeDetail;
}>();

const exampleTo = computed(() =>
  props.episode.contract.status === "breached"
    ? contractExampleRoute(
        props.run.execution_id,
        props.subject.target_id,
        props.trial.trial_id,
      )
    : null,
);

const facts = computed<MetricGridItem[]>(() => [
  {
    key: "outcome",
    label: "Outcome",
    value: props.episode.success
      ? "Success"
      : statusLabel(props.episode.terminal_reason),
    tone: props.episode.success ? "default" : "danger",
  },
  {
    key: "questions",
    label: "Questions",
    value: props.trial.counted_questions,
    detail: `Penalized ${number(props.trial.penalized_questions)}`,
  },
  {
    key: "contract",
    label: "Output contract",
    value: statusLabel(props.episode.contract.status),
    tone: props.episode.contract.status === "breached" ? "danger" : "default",
    linkLabel: exampleTo.value === null ? undefined : "View one example",
    to: exampleTo.value ?? undefined,
  },
  {
    key: "duration",
    label: "Duration",
    value: duration(props.episode.duration_ms),
  },
  {
    key: "cost",
    label: "Episode cost",
    value: moneyEpisode(props.episode.total_cost_usd),
    detail: `All ${props.episode.total_turns} turns`,
    tone: "accent",
  },
]);
</script>

<template>
  <header id="episode-overview" class="episode-hero">
    <div class="episode-hero-inner workspace-detail-boundary">
      <div class="episode-summary">
        <p class="eyebrow">Episode {{ trial.trial_number }}</p>
        <h1>Episode {{ trial.trial_number }}</h1>
        <p class="episode-deck">
          <template v-if="episode.success">
            Identified <em>{{ episode.subject_name }}</em> in
            {{ episode.counted_questions }} counted questions.
          </template>
          <template v-else>
            Did not identify <em>{{ episode.subject_name }}</em> after
            {{ episode.counted_questions }} counted questions.
          </template>
        </p>
        <RouterLink
          class="subject-return"
          :to="{
            name: 'subject',
            params: {
              executionId: run.execution_id,
              targetId: subject.target_id,
            },
          }"
        >
          Back to {{ subject.display_name }} attempts
          <span aria-hidden="true">↑</span>
        </RouterLink>
      </div>

      <MetricGrid
        class="episode-summary-metrics"
        :items="facts"
        label="Episode summary"
        :max-columns="5"
        density="compact"
      />
    </div>
  </header>
</template>

<style scoped>
.episode-hero {
  border-bottom: var(--rule-default);
  background: var(--surface-raised);
  color: var(--text-primary);
}

.episode-hero-inner {
  display: grid;
  grid-template-columns: minmax(13rem, 0.45fr) minmax(0, 1.55fr);
  gap: clamp(1.25rem, 2.5vw, 3rem);
  align-items: center;
  padding: clamp(1rem, 1.8vw, 1.5rem) var(--workspace-panel-padding);
}

.episode-summary .eyebrow {
  margin-bottom: 0.45rem;
  color: var(--blue-ink);
}

.episode-summary h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-workspace-detail-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.055em;
  line-height: var(--text-workspace-detail-title--line-height);
  white-space: nowrap;
}

.episode-deck {
  max-width: 38rem;
  margin: 0.75rem 0 0;
  color: var(--text-secondary);
  font-family: var(--font-text);
  font-size: 0.88rem;
  line-height: 1.55;
}

.episode-deck em {
  color: var(--text-primary);
}

.subject-return {
  display: inline-block;
  margin-top: 0.75rem;
  color: var(--blue-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

@media (max-width: 900px) {
  .subject-return {
    display: inline-flex;
    min-height: 44px;
    align-items: center;
  }
}

.episode-summary-metrics {
  margin: 0;
}

.episode-summary-metrics :deep(dd) {
  font-size: var(--text-workspace-stat);
  line-height: var(--text-workspace-stat--line-height);
}

@media (max-width: 1500px) {
  .episode-hero-inner {
    grid-template-columns: minmax(13rem, 0.5fr) minmax(0, 1.5fr);
  }
}

@media (max-width: 1024px) {
  .episode-hero-inner {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .episode-hero-inner {
    gap: 0.55rem;
    padding: 0.7rem 0.9rem 0.75rem;
  }

  .episode-summary h1 {
    font-size: var(--text-workspace-detail-title);
    line-height: var(--text-workspace-detail-title--line-height);
  }

  .episode-deck {
    margin-top: 0.3rem;
    font-size: var(--text-micro);
    line-height: 1.35;
  }

  .subject-return {
    margin-top: 0.35rem;
    font-size: var(--text-caption);
  }
}

@media (min-width: 1025px) and (max-height: 800px) {
  .episode-hero-inner {
    grid-template-columns: minmax(11rem, 0.38fr) minmax(0, 1.62fr);
    gap: 1rem;
    padding-block: 0.75rem;
  }

  .episode-summary .eyebrow {
    margin-bottom: 0.2rem;
  }

  .episode-summary h1 {
    font-size: 2rem;
    line-height: 1;
  }

  .episode-deck {
    margin-top: 0.35rem;
    font-size: 0.76rem;
    line-height: 1.4;
  }

  .subject-return {
    margin-top: 0.4rem;
  }

  .episode-hero-inner .episode-summary-metrics {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }

  .episode-hero-inner .episode-summary-metrics :deep(> div:last-child) {
    grid-column: auto;
  }

  .episode-summary-metrics :deep(> div) {
    padding: 0.65rem 0.7rem;
  }

  .episode-summary-metrics :deep(dd) {
    margin-top: 0.25rem;
    font-size: clamp(1.05rem, 1.7vw, 1.35rem);
  }

  .episode-summary-metrics :deep(dd small) {
    margin-top: 0.25rem;
  }
}
</style>
