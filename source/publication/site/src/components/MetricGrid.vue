<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

export interface MetricGridItem {
  key: string;
  label: string;
  value: string | number;
  detail?: string;
  tone?: "default" | "accent" | "danger";
  linkLabel?: string;
  to?: RouteLocationRaw;
}

withDefaults(
  defineProps<{
    items: readonly MetricGridItem[];
    label: string;
    maxColumns: 2 | 3 | 4 | 5;
    density?: "default" | "compact";
  }>(),
  {
    density: "default",
  },
);
</script>

<template>
  <dl
    class="metric-grid"
    :class="[
      `metric-grid--columns-${maxColumns}`,
      { 'metric-grid--compact': density === 'compact' },
    ]"
    :aria-label="label"
  >
    <div
      v-for="item in items"
      :key="item.key"
      :data-tone="item.tone ?? 'default'"
    >
      <dt>{{ item.label }}</dt>
      <dd>
        {{ item.value }}
        <small v-if="item.detail">{{ item.detail }}</small>
        <RouterLink
          v-if="item.to && item.linkLabel"
          class="metric-grid-link"
          :to="item.to"
        >
          {{ item.linkLabel }} <span aria-hidden="true">→</span>
        </RouterLink>
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.metric-grid-link {
  display: block;
  margin-top: 0.35rem;
  color: var(--blue-ink);
  font-family: var(--font-sans);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  line-height: 1.35;
}
</style>
