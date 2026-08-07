<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import { benchmarkWorkspaceView } from "@/router";

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
    @mouseenter="benchmarkWorkspaceView.preload()"
    @focus="benchmarkWorkspaceView.preload()"
  >
    <span class="model-run-link-copy">
      <span class="model-run-link-name">{{ name }}</span>
      <span v-if="meta" class="model-run-link-meta">{{ meta }}</span>
    </span>
    <span class="model-run-link-chevron" aria-hidden="true">→</span>
  </RouterLink>
</template>

<style scoped>
.model-run-link {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.65rem;
  align-items: center;
  color: var(--blue-ink);
  line-height: 1.3;
  text-decoration: none;
}

.model-run-link-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
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

.model-run-link-chevron {
  color: var(--blue-ink);
  font-size: 1rem;
  transition: transform 140ms ease;
}

.model-run-link:hover .model-run-link-name {
  text-decoration-color: currentColor;
}

.model-run-link:hover .model-run-link-chevron,
.model-run-link:focus-visible .model-run-link-chevron {
  transform: translateX(0.2rem);
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
