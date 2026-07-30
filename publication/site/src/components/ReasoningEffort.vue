<script setup lang="ts">
import { computed } from "vue";

import { reasoningEffortLabel } from "@/lib/format";

const props = withDefaults(
  defineProps<{ effort: string; compact?: boolean; dark?: boolean }>(),
  { compact: false, dark: false },
);

const level = computed(() => {
  const value = props.effort.trim().toLowerCase();
  if (["high", "extra-high", "xhigh", "max", "maximum"].includes(value)) return 3;
  if (["medium", "default"].includes(value)) return 2;
  if (["minimal", "low"].includes(value)) return 1;
  return 0;
});
</script>

<template>
  <span
    class="reasoning-effort"
    :class="{ compact, dark }"
    :aria-label="`Reasoning effort: ${reasoningEffortLabel(effort)}`"
  >
    <span class="effort-meter" aria-hidden="true">
      <i v-for="index in 3" :key="index" :class="{ active: index <= level }"></i>
    </span>
    <span>{{ reasoningEffortLabel(effort) }}</span>
  </span>
</template>

<style scoped>
.reasoning-effort {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 680;
}

.effort-meter {
  display: inline-flex;
  align-items: end;
  gap: 2px;
  height: 13px;
}

.effort-meter i {
  display: block;
  width: 3px;
  height: 45%;
  background: var(--line);
}

.effort-meter i:nth-child(2) {
  height: 72%;
}

.effort-meter i:nth-child(3) {
  height: 100%;
}

.effort-meter i.active {
  background: var(--blue);
}

.compact > span:last-child {
  font-size: 0.68rem;
}

.dark {
  color: white;
}

.dark .effort-meter i {
  background: rgb(255 255 255 / 22%);
}

.dark .effort-meter i.active {
  background: var(--acid);
}
</style>
