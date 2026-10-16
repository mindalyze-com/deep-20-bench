<script setup lang="ts">
import type { SortDirection } from "@/lib/use-table-sort";

defineProps<{
  labels: readonly string[];
  direction: SortDirection | "none";
}>();
defineEmits<{ sort: [] }>();
</script>

<template>
  <button
    type="button"
    class="sort-button"
    :aria-label="`Sort by ${labels.join(' ')}`"
    @click.stop="$emit('sort')"
  >
    <span v-if="labels.length > 1" class="table-header-stack">
      <span v-for="label in labels" :key="label">{{ label }}</span>
    </span>
    <span v-else>{{ labels[0] }}</span>
    <span class="sort-indicator" :data-direction="direction" aria-hidden="true">
      {{ direction === "ascending" ? "↑" : direction === "descending" ? "↓" : "↕" }}
    </span>
  </button>
</template>

<style scoped>
.sort-button {
  display: inline-flex;
  align-items: end;
  gap: 0.3rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  text-align: inherit;
  text-transform: inherit;
  cursor: pointer;
}

[data-numeric] > .sort-button {
  flex-direction: row-reverse;
}

.sort-button:hover,
.sort-button:focus-visible {
  color: var(--text-primary);
}

.sort-indicator {
  opacity: 0.45;
}

.sort-indicator:not([data-direction="none"]) {
  color: var(--blue-ink);
  opacity: 1;
}
</style>
