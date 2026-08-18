<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

export interface ChartModelKeyItem {
  key: string;
  label: string;
  detail: string;
  link?: RouteLocationRaw;
  marker?: "circle" | "diamond";
}

defineProps<{
  items: ChartModelKeyItem[];
  color: string;
}>();
</script>

<template>
  <ul class="chart-model-key" aria-label="Models in the chart">
    <li v-for="item in items" :key="item.key">
      <i
        :class="{ 'chart-model-key-marker--diamond': item.marker === 'diamond' }"
        :style="{ backgroundColor: color }"
        aria-hidden="true"
      ></i>
      <RouterLink v-if="item.link" :to="item.link">{{ item.label }}</RouterLink>
      <strong v-else>{{ item.label }}</strong>
      <span>{{ item.detail }}</span>
    </li>
  </ul>
</template>

<style scoped>
.chart-model-key {
  display: none;
}

@media (max-width: 620px) {
  .chart-model-key {
    display: grid;
    margin: 0.2rem 0.5rem 0;
    padding: 0;
    border-top: var(--rule-subtle);
    list-style: none;
  }

  .chart-model-key li {
    display: grid;
    grid-template-columns: 0.55rem minmax(0, 1fr) auto;
    gap: 0.5rem;
    align-items: center;
    min-height: 2.4rem;
    border-bottom: var(--rule-subtle);
    font-size: var(--text-micro);
  }

  .chart-model-key i {
    width: 0.55rem;
    height: 0.55rem;
    border: var(--rule-strong);
    border-radius: 50%;
  }

  .chart-model-key-marker--diamond {
    border-radius: 0 !important;
    transform: rotate(45deg);
  }

  .chart-model-key a,
  .chart-model-key strong {
    overflow: hidden;
    color: var(--ink);
    font-weight: var(--font-weight-bold);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chart-model-key span {
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }
}
</style>
