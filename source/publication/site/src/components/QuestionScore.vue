<script setup lang="ts">
import { computed } from "vue";

import InfoPopover from "@/components/InfoPopover.vue";
import { number } from "@/lib/format";
import type { QuestionScoreConfidenceInterval } from "@/lib/types";

const props = withDefaults(
  defineProps<{
    score: string | null;
    maxQuestions?: number;
    label?: string;
    variant?: "default" | "compact" | "metric" | "hero" | "table";
    theme?: "light" | "dark";
    explain?: boolean;
    confidenceInterval?: QuestionScoreConfidenceInterval | null;
  }>(),
  {
    maxQuestions: 50,
    label: "Question score",
    variant: "default",
    theme: "light",
    explain: false,
    confidenceInterval: null,
  },
);

const percentage = computed(() =>
  props.score === null
    ? 0
    : Math.max(0, Math.min(100, (Number(props.score) / (props.maxQuestions + 1)) * 100)),
);
const accessibleLabel = computed(() => {
  const score = `${props.label}: ${number(props.score)}`;
  return props.confidenceInterval === null
    ? score
    : `${score}; 95% confidence interval ${number(
        props.confidenceInterval.lower,
        2,
      )} to ${number(props.confidenceInterval.upper, 2)}`;
});
</script>

<template>
  <div
    class="question-score"
    :class="[`question-score--${variant}`, `question-score--${theme}`]"
    :aria-label="accessibleLabel"
  >
    <span class="score-label">{{ label }}</span>
    <strong>{{ number(score) }}</strong>
    <span class="score-unit">{{ score === null ? "not available" : "questions · lower is better" }}</span>
    <span v-if="confidenceInterval !== null" class="score-confidence">
      <template v-if="variant !== 'table'">95% CI </template>{{
        number(confidenceInterval.lower, 2)
      }}–{{ number(confidenceInterval.upper, 2) }}
    </span>
    <span v-if="variant !== 'compact' && score !== null" class="score-scale" aria-hidden="true">
      <i :style="{ width: `${percentage}%` }"></i>
    </span>
    <InfoPopover
      v-if="explain"
      class="score-help"
      label="How this is scored"
    >
      <p class="score-help-copy">
        Trial values are averaged within each subject, then across subjects. A failed trial
        receives the declared failure penalty.
      </p>
      <p v-if="confidenceInterval !== null" class="score-help-copy">
        The interval estimates repeated-trial uncertainty on the fixed benchmark subjects. It
        uses a stratified Welch t interval over the trials within each subject.
      </p>
    </InfoPopover>
  </div>
</template>

<style scoped>
.question-score {
  display: grid;
  gap: 0.35rem;
  min-width: 7rem;
}

.score-label,
.score-unit,
.score-confidence {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.score-confidence {
  letter-spacing: 0;
  text-transform: none;
}

strong {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 5vw, 5rem);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.06em;
  line-height: 0.9;
}

.score-scale {
  position: relative;
  display: block;
  width: 100%;
  height: 5px;
  margin-top: 0.5rem;
  background: var(--line);
}

.score-scale i {
  position: absolute;
  inset: 0 auto 0 0;
  background: var(--blue);
}

.question-score--compact {
  display: inline-grid;
  gap: 0.1rem;
  min-width: 4rem;
}

.question-score--compact .score-label,
.question-score--compact .score-unit {
  display: none;
}

.question-score--compact .score-confidence {
  display: none;
}

.question-score--compact strong {
  font-family: inherit;
  font-size: 1rem;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0;
}

.question-score--table {
  display: inline-grid;
  gap: 0.18rem;
  min-width: 5.75rem;
  justify-items: end;
}

.question-score--table .score-label,
.question-score--table .score-unit,
.question-score--table .score-scale {
  display: none;
}

.question-score--table strong {
  color: var(--blue-ink);
  font-family: inherit;
  font-size: 1rem;
  font-weight: var(--font-weight-medium);
  letter-spacing: 0;
  line-height: 1.2;
}

.question-score--table .score-confidence {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0;
  text-transform: none;
}

.question-score--metric strong {
  font-size: clamp(1.65rem, 3vw, 2.6rem);
}

.question-score--hero strong {
  color: var(--acid);
  font-size: clamp(5rem, 11vw, 9rem);
}

.question-score--dark .score-label,
.question-score--dark .score-unit {
  color: white;
}

.question-score--dark .score-confidence {
  color: white;
}

.question-score--dark .score-scale {
  background: rgb(255 255 255 / 22%);
}

.question-score--dark .score-scale i {
  background: var(--acid);
}

.score-help {
  margin-top: 0.75rem;
}

.score-help-copy {
  margin: 0;
}
</style>
