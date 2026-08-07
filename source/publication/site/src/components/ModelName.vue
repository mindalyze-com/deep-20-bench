<script setup lang="ts">
import { computed } from "vue";

import { reasoningEffortLabel } from "@/lib/format";
import { splitModelName } from "@/lib/model-name";

const props = withDefaults(
  defineProps<{ name: string; compact?: boolean; dark?: boolean }>(),
  { compact: false, dark: false },
);

const parts = computed(() => splitModelName(props.name));
</script>

<template>
  <span class="model-name" :class="{ compact, dark }">
    <span class="model-name-label">{{ parts.displayName }}</span>
    <span
      v-if="parts.reasoningEffort"
      class="model-name-effort"
      :aria-label="`Reasoning effort: ${reasoningEffortLabel(parts.reasoningEffort)}`"
    >
      {{ reasoningEffortLabel(parts.reasoningEffort) }}
    </span>
  </span>
</template>

<style scoped>
.model-name {
  display: flex;
  min-width: 0;
  max-width: 100%;
  flex-wrap: wrap;
  gap: 0.18em;
  align-items: flex-start;
}

.model-name-label {
  min-width: 0;
}

.model-name-effort {
  display: inline-flex;
  padding: 0.24rem 0.52rem 0.2rem;
  border: var(--rule-muted);
  border-radius: 0.35rem;
  color: var(--text-secondary);
  font-family: var(--font-sans);
  font-size: var(--text-small);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0;
  line-height: 1;
  text-transform: lowercase;
  white-space: nowrap;
}

.compact {
  column-gap: 0.28rem;
}

.compact .model-name-effort {
  padding: 0.2rem 0.42rem 0.17rem;
  font-size: var(--text-caption);
}

.dark .model-name-effort {
  border-color: var(--border-inverse-strong);
  color: var(--text-inverse);
}
</style>
