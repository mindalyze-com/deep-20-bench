<script setup lang="ts">
import { computed } from "vue";

import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
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
    <div class="episode-hero-inner">
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
  grid-template-columns: minmax(14rem, 0.55fr) minmax(0, 1.45fr);
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: end;
  width: 100%;
  padding: clamp(1.1rem, 2.5vw, 2rem) clamp(1rem, 3vw, 2.5rem);
}

.episode-summary .eyebrow {
  margin-bottom: 0.45rem;
  color: var(--blue-ink);
}

.episode-summary h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.7rem, 4vw, 4rem);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.055em;
  line-height: 0.92;
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

.episode-summary-metrics {
  margin: 0;
}

@media (max-width: 1500px) {
  .episode-hero-inner {
    grid-template-columns: minmax(15rem, 0.55fr) minmax(0, 1.45fr);
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
    font-size: clamp(1.85rem, 9vw, 2.6rem);
    line-height: 0.96;
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
</style>
