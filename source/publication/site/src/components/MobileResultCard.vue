<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router";
import RankBadge from "@/components/RankBadge.vue";

interface ResultMetric {
  label: string;
  value: string;
}

defineProps<{
  rank: number | string;
  rankTied?: boolean;
  rankNote?: string;
  name: string;
  provider: string;
  metrics: ResultMetric[];
  to: RouteLocationRaw | null;
}>();
</script>

<template>
  <component
    :is="to === null ? 'article' : RouterLink"
    class="mobile-result-card"
    :class="{ 'mobile-result-card--disabled': to === null }"
    :to="to ?? undefined"
  >
    <div class="mobile-result-card-head">
      <RankBadge :rank="rank" :tied="rankTied" :note="rankNote" />
      <span class="mobile-result-identity">
        <strong>{{ name }}</strong>
        <small>{{ provider }}</small>
      </span>
      <span v-if="metrics[0]" class="mobile-result-primary">
        <strong>{{ metrics[0].value }}</strong>
        <small>{{ metrics[0].label }}</small>
      </span>
      <span v-if="to !== null" class="mobile-result-chevron" aria-hidden="true">›</span>
    </div>

    <dl v-if="metrics.length > 1" class="mobile-result-metrics">
      <div v-for="metric in metrics.slice(1)" :key="metric.label">
        <dt>{{ metric.label }}</dt>
        <dd>{{ metric.value }}</dd>
      </div>
    </dl>
    <span v-if="to !== null" class="visually-hidden">Open model results.</span>
  </component>
</template>

<style scoped>
.mobile-result-card {
  display: block;
  overflow: hidden;
  border: var(--rule-default);
  background: var(--surface-raised);
  color: var(--text-primary);
  text-decoration: none;
  -webkit-tap-highlight-color: transparent;
  transition:
    background-color 140ms ease,
    box-shadow 140ms ease;
}

.mobile-result-card:not(.mobile-result-card--disabled):hover,
.mobile-result-card:not(.mobile-result-card--disabled):active,
.mobile-result-card:not(.mobile-result-card--disabled):focus-visible {
  background: var(--surface-accent-soft);
  box-shadow: inset 4px 0 0 var(--blue);
}

.mobile-result-card:focus-visible {
  outline: var(--focus-ring);
  outline-offset: 3px;
}

.mobile-result-card-head {
  display: grid;
  grid-template-columns: 2.25rem minmax(0, 1fr) auto 0.9rem;
  gap: 0.6rem;
  align-items: center;
  padding: 0.7rem 0.8rem 0.55rem;
}

.mobile-result-identity {
  min-width: 0;
}

.mobile-result-identity strong,
.mobile-result-identity small {
  display: block;
  overflow-wrap: anywhere;
}

.mobile-result-identity strong {
  color: var(--blue-ink);
  font-size: 0.9rem;
  font-weight: var(--font-weight-bold);
}

.mobile-result-identity small,
.mobile-result-primary small {
  margin-top: 0.15rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-semibold);
}

.mobile-result-primary {
  display: grid;
  justify-items: end;
  text-align: right;
}

.mobile-result-primary strong {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-variant-numeric: tabular-nums;
  font-weight: var(--font-weight-medium);
  line-height: 1;
}

.mobile-result-chevron {
  color: var(--blue-ink);
  font-size: 1.5rem;
  line-height: 1;
  transition: transform 140ms ease;
}

.mobile-result-card:not(.mobile-result-card--disabled):hover
  .mobile-result-chevron,
.mobile-result-card:not(.mobile-result-card--disabled):active
  .mobile-result-chevron,
.mobile-result-card:not(.mobile-result-card--disabled):focus-visible
  .mobile-result-chevron {
  transform: translateX(0.2rem);
}

/* Secondary metrics share one aligned row; gaps instead of dividers keep columns even. */
.mobile-result-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0;
  padding: 0.5rem 0.8rem 0.65rem;
  border-top: var(--rule-subtle);
}

.mobile-result-metrics div {
  min-width: 0;
}

.mobile-result-metrics dt {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.04em;
  line-height: 1.3;
  text-transform: uppercase;
}

.mobile-result-metrics dd {
  margin: 0.15rem 0 0;
  font-family: var(--font-body);
  font-size: 0.82rem;
  font-weight: var(--font-weight-bold);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

@media (max-width: 360px) {
  .mobile-result-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
