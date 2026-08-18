<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

export interface ChartAccessibleItem {
  key: string;
  label: string;
  description: string;
  link?: RouteLocationRaw;
}

defineProps<{
  label: string;
  items: ChartAccessibleItem[];
}>();
</script>

<template>
  <ol class="visually-hidden" :aria-label="label">
    <li v-for="item in items" :key="item.key">
      {{ item.description }}
      <RouterLink v-if="item.link" :to="item.link" tabindex="-1">
        View full run for {{ item.label }}
      </RouterLink>
    </li>
  </ol>
</template>
