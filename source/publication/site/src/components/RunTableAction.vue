<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

defineProps<{
  name: string;
  to: RouteLocationRaw;
}>();
</script>

<template>
  <RouterLink
    class="run-table-action"
    :to="to"
    :aria-label="`View full run for ${name}`"
    @click.stop
  >
    View <span aria-hidden="true">→</span>
  </RouterLink>
</template>

<style scoped>
.run-table-action {
  display: inline-block;
  margin: -0.7rem -0.25rem;
  padding: 0.7rem 0.25rem;
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
  text-decoration: none;
  white-space: nowrap;
}

.run-table-action:hover {
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
}

.run-table-action:focus-visible {
  border-radius: 2px;
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}
</style>
