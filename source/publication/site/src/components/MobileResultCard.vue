<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router";

interface ResultMetric {
  label: string;
  value: string;
}

defineProps<{
  rank: number | string;
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
    :aria-label="to === null ? undefined : `Explore full run for ${name}`"
  >
    <div class="mobile-result-card-head">
      <span class="mobile-result-rank">#{{ rank }}</span>
      <span class="mobile-result-identity">
        <strong>{{ name }}</strong>
        <small>{{ provider }}</small>
      </span>
      <span v-if="to !== null" class="mobile-result-chevron" aria-hidden="true">›</span>
    </div>

    <dl class="mobile-result-metrics">
      <div v-for="metric in metrics" :key="metric.label">
        <dt>{{ metric.label }}</dt>
        <dd>{{ metric.value }}</dd>
      </div>
    </dl>

    <div class="mobile-result-action">
      <span>
        {{
          to === null
            ? "Full run unavailable"
            : "Explore full run · questions, answers & evidence"
        }}
      </span>
      <span v-if="to !== null" aria-hidden="true">→</span>
    </div>
  </component>
</template>

<style scoped>
.mobile-result-card {
  display: block;
  overflow: hidden;
  border: 1px solid var(--line);
  background: var(--paper-bright);
  color: var(--ink);
  text-decoration: none;
  -webkit-tap-highlight-color: transparent;
  transition:
    background-color 140ms ease,
    box-shadow 140ms ease;
}

.mobile-result-card:not(.mobile-result-card--disabled):hover,
.mobile-result-card:not(.mobile-result-card--disabled):active,
.mobile-result-card:not(.mobile-result-card--disabled):focus-visible {
  background: #eef0ff;
  box-shadow: inset 4px 0 0 var(--blue);
}

.mobile-result-card:focus-visible {
  outline: 3px solid var(--blue);
  outline-offset: 3px;
}

.mobile-result-card-head {
  display: grid;
  grid-template-columns: 2.25rem minmax(0, 1fr) 1.25rem;
  gap: 0.6rem;
  align-items: center;
  padding: 0.85rem 0.9rem 0.75rem;
}

.mobile-result-rank {
  color: var(--muted);
  font-size: var(--text-small);
  font-weight: 760;
  font-variant-numeric: tabular-nums;
}

.mobile-result-identity {
  min-width: 0;
}

.mobile-result-identity strong,
.mobile-result-identity small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-result-identity strong {
  color: var(--blue-ink);
  font-size: 0.9rem;
  font-weight: 760;
}

.mobile-result-identity small {
  margin-top: 0.15rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 520;
}

.mobile-result-chevron {
  color: var(--blue-ink);
  font-size: 1.7rem;
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

.mobile-result-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  padding: 0.7rem 0.9rem 0.8rem;
  border-top: 1px solid var(--line-soft);
}

.mobile-result-metrics div {
  min-width: 0;
  padding-inline: 0.7rem;
  border-right: 1px solid var(--line-soft);
}

.mobile-result-metrics div:first-child {
  padding-left: 0;
}

.mobile-result-metrics div:last-child {
  padding-right: 0;
  border-right: 0;
}

.mobile-result-metrics dt {
  overflow: hidden;
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 710;
  letter-spacing: 0.05em;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.mobile-result-metrics dd {
  margin: 0.2rem 0 0;
  overflow: hidden;
  font-family: var(--font-body);
  font-size: 0.86rem;
  font-weight: 740;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-result-action {
  display: flex;
  min-height: 2.75rem;
  padding: 0.65rem 0.9rem;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: #eef0ff;
  color: var(--blue-ink);
  font-size: 0.7rem;
  font-weight: 720;
  line-height: 1.35;
}

.mobile-result-card--disabled .mobile-result-action {
  background: var(--paper);
  color: var(--muted);
}
</style>
