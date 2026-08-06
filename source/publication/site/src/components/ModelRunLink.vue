<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

defineProps<{
  name: string;
  meta?: string;
  to: RouteLocationRaw;
}>();
</script>

<template>
  <RouterLink
    class="result-row-link model-run-link"
    :to="to"
    :aria-label="`View full run for ${name}`"
    @click.stop
  >
    <span class="model-run-link-name">{{ name }}</span>
    <span v-if="meta" class="model-run-link-meta">{{ meta }}</span>
  </RouterLink>
</template>

<style scoped>
.model-run-link {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  color: var(--blue-ink);
  line-height: 1.3;
  text-decoration: none;
}

.model-run-link-name {
  font-weight: var(--font-weight-bold);
  text-decoration-color: transparent;
  text-decoration-line: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  white-space: nowrap;
}

.model-run-link-meta {
  margin-top: 0.12rem;
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.model-run-link:hover .model-run-link-name {
  text-decoration-color: currentColor;
}

.model-run-link:focus-visible {
  border-radius: 2px;
  outline: 2px solid var(--blue);
  outline-offset: 3px;
}

@media (max-width: 620px) {
  .model-run-link-name {
    white-space: normal;
  }

  .model-run-link-meta {
    display: none;
  }
}
</style>
