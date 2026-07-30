<script setup lang="ts">
export interface MetricGridItem {
  key: string;
  label: string;
  value: string | number;
  detail?: string;
  tone?: "default" | "accent" | "danger";
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
      </dd>
    </div>
  </dl>
</template>
