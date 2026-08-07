<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string;
  }>(),
  {
    label: "Metric explanations",
  },
);
</script>

<template>
  <aside class="result-help" :aria-label="label">
    <div class="result-help-items">
      <slot />
    </div>
  </aside>
</template>

<style scoped>
.result-help {
  display: grid;
  align-content: end;
  gap: 0.35rem;
  min-width: 0;
  margin: 0;
  color: var(--result-accent-ink, var(--blue-ink));
}

.result-help-items {
  display: grid;
  gap: 0;
}

.result-help :deep(.info-popover-trigger) {
  min-height: 44px;
  padding: 0.25rem 0;
  font-size: var(--text-small);
  font-weight: var(--font-weight-semibold);
}

.result-help :deep(.info-popover-trigger:hover),
.result-help :deep(.info-popover-trigger:focus-visible) {
  opacity: 1;
}

.result-help :deep(.info-popover-indicator) {
  width: 1rem;
  height: 1rem;
  font-size: 0.62rem;
}

.result-help :deep(p) {
  margin: 0;
}

.result-help :deep(p + p) {
  margin-top: 0.65rem;
}

@media (max-width: 1320px) {
  .result-help {
    display: grid;
  }

  .result-help-items {
    display: flex;
    flex-wrap: wrap;
    column-gap: clamp(0.8rem, 2vw, 1.2rem);
  }
}
</style>
