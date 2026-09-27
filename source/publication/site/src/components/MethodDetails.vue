<script setup lang="ts">
defineProps<{ title: string; anchor: string }>();
</script>

<template>
  <details class="disclosure method-details">
    <summary>
      <span><strong>{{ title }}</strong></span>
      <span aria-hidden="true"><span class="when-closed">Details +</span><span class="when-open">Close −</span></span>
    </summary>
    <div :id="anchor" class="method-detail-body"><slot /></div>
  </details>
</template>

<style scoped>
.method-details {
  margin-top: 0.75rem;
}

.method-details summary {
  gap: 1rem;
}

.method-details summary strong {
  font-size: var(--text-ui);
  letter-spacing: 0;
  text-transform: none;
}

.method-details summary > span:last-child {
  flex-shrink: 0;
}

.method-details .when-open,
.method-details[open] .when-closed {
  display: none;
}

.method-details[open] .when-open {
  display: inline;
}

.method-detail-body {
  padding: 0 1.15rem 1.15rem;
}

.method-detail-body :deep(> :first-child) {
  margin-top: 0;
}

.method-detail-body :deep(> :last-child) {
  margin-bottom: 0;
}
</style>
