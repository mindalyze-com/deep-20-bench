<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import { formatCount } from "@/lib/format";
import type { ContractReliability } from "@/lib/types";

const props = withDefaults(
  defineProps<{
    contract: ContractReliability;
    affectedUnit: "rounds";
    headingLevel?: "h2" | "h3";
    exampleTo?: RouteLocationRaw | null;
  }>(),
  {
    headingLevel: "h2",
    exampleTo: null,
  },
);

const heading = computed(() => {
  if (props.contract.status === "breached") return "Format errors found.";
  if (props.contract.status === "clean") return "No format errors.";
  return "Format not checked.";
});
</script>

<template>
  <section class="contract-status-card" :data-status="contract.status">
    <p class="eyebrow">Reply format</p>
    <component :is="headingLevel">{{ heading }}</component>
    <p v-if="contract.status === 'breached'">
      {{ formatCount(contract.violations, "invalid reply", "invalid replies") }} in
      {{ formatCount(contract.affected_trials, "round") }} used up
      {{ formatCount(contract.counted_penalties, "counted turn") }}.
    </p>
    <p v-else-if="contract.status === 'clean'">
      All {{ contract.evaluated_outputs }} checked replies used the required format.
    </p>
    <p v-else>
      No replies were available to check.
    </p>
    <RouterLink
      v-if="contract.status === 'breached' && exampleTo"
      class="contract-example-link"
      :to="exampleTo"
    >
      View one recorded example <span aria-hidden="true">→</span>
    </RouterLink>
  </section>
</template>

<style scoped>
.contract-example-link {
  display: inline-block;
  margin-top: 0.8rem;
  color: var(--blue-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}
</style>
