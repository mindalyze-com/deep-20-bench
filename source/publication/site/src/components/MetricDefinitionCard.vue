<script setup lang="ts">
import { useId } from "vue";

withDefaults(
  defineProps<{
    title: string;
    formula: string;
    interpretation: string;
    detailSummary?: string;
  }>(),
  {
    detailSummary: "Steps, example, and limits",
  },
);

const titleId = `metric-definition-title-${useId()}`;
</script>

<template>
  <article class="metric-definition-card" :aria-labelledby="titleId">
    <div class="metric-definition-intro">
      <header>
        <p class="eyebrow">How it is calculated</p>
        <h2 :id="titleId">{{ title }}</h2>
        <p>{{ interpretation }}</p>
      </header>
      <div class="metric-definition-formula">
        <span>Formula</span>
        <code>{{ formula }}</code>
      </div>
    </div>

    <details class="disclosure metric-definition-details">
      <summary>
        <span>
          <strong>Calculation details</strong>
          <small>{{ detailSummary }}</small>
        </span>
        <span class="metric-definition-toggle" aria-hidden="true">
          <span class="metric-definition-toggle-closed">View ↓</span>
          <span class="metric-definition-toggle-open">Hide ↑</span>
        </span>
      </summary>
      <div class="metric-definition-body">
        <slot />
      </div>
    </details>
  </article>
</template>

<style scoped>
.metric-definition-card {
  margin-top: clamp(1.5rem, 4vw, 2.5rem);
  border: var(--rule-default);
  background: var(--surface-raised);
}

.metric-definition-intro {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(18rem, 1.08fr);
}

.metric-definition-intro header,
.metric-definition-formula {
  padding: clamp(1.2rem, 3vw, 2rem);
}

.metric-definition-intro header {
  border-right: var(--rule-default);
}

.metric-definition-intro h2 {
  max-width: 18ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--result-card-title-size);
  font-weight: 500;
  letter-spacing: -0.035em;
  line-height: 1;
}

.metric-definition-intro header > p:last-child {
  max-width: 40rem;
  margin: 0.85rem 0 0;
  color: var(--text-secondary);
  font-size: var(--text-small);
  line-height: 1.6;
}

.metric-definition-formula {
  display: grid;
  align-content: start;
  gap: 0.65rem;
  border-left: var(--border-emphasis-width) solid var(--result-accent);
  background: var(--result-accent-soft);
}

.metric-definition-formula > span {
  color: var(--result-accent-ink);
  font-size: var(--text-micro);
  font-weight: 760;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.metric-definition-formula code {
  overflow-wrap: anywhere;
  color: var(--ink);
  font-size: clamp(0.82rem, 1.5vw, 1rem);
  line-height: 1.55;
}

.metric-definition-details {
  border: 0;
  border-top: var(--rule-default);
}

.metric-definition-details > summary > span:last-child {
  color: var(--result-accent-ink);
}

.metric-definition-toggle-open {
  display: none;
}

.metric-definition-details[open] .metric-definition-toggle-closed {
  display: none;
}

.metric-definition-details[open] .metric-definition-toggle-open {
  display: inline;
}

.metric-definition-body {
  max-width: 52rem;
  padding: 0 clamp(1.2rem, 3vw, 2rem) clamp(1.2rem, 3vw, 2rem);
}

.metric-definition-body :deep(p),
.metric-definition-body :deep(li) {
  color: var(--ink-soft);
  line-height: 1.7;
}

.metric-definition-body :deep(ol) {
  margin-top: 0;
  padding-left: 1.25rem;
}

.metric-definition-body :deep(.metric-example) {
  padding: 1rem;
  border-left: var(--border-emphasis-width) solid var(--result-accent);
  background: var(--result-accent-soft);
}

@media (max-width: 760px) {
  .metric-definition-intro {
    grid-template-columns: 1fr;
  }

  .metric-definition-intro header {
    border-right: 0;
    border-bottom: var(--rule-default);
  }
}
</style>
