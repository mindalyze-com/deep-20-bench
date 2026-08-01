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
    <slot />
  </aside>
</template>

<style scoped>
.result-help {
  display: grid;
  align-content: end;
  gap: 0;
  min-width: 0;
  margin: 0;
  color: var(--result-accent-ink, var(--blue-ink));
}

.result-help :deep(.info-popover-trigger) {
  min-height: 44px;
  padding: 0.25rem 0;
  font-size: var(--text-caption);
  font-weight: 660;
  opacity: 0.78;
}

.result-help :deep(.info-popover-trigger:hover),
.result-help :deep(.info-popover-trigger:focus-visible) {
  opacity: 1;
}

.result-help :deep(.info-popover-indicator) {
  width: 0.9rem;
  height: 0.9rem;
  font-size: 0.56rem;
}

.result-help :deep(p) {
  margin: 0;
}

.result-help :deep(p + p) {
  margin-top: 0.65rem;
}

@media (max-width: 1320px) {
  .result-help {
    display: flex;
    flex-wrap: wrap;
    column-gap: clamp(0.8rem, 2vw, 1.2rem);
    row-gap: 0;
  }
}
</style>
