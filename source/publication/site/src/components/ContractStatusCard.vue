<script setup lang="ts">
import { computed } from "vue";

import type { ContractReliability } from "@/lib/types";

const props = withDefaults(
  defineProps<{
    contract: ContractReliability;
    affectedUnit: "episodes" | "attempts";
    headingLevel?: "h2" | "h3";
  }>(),
  {
    headingLevel: "h2",
  },
);

const heading = computed(() => {
  if (props.contract.status === "breached") return "Output contract breached.";
  if (props.contract.status === "clean") return "Output contract clean.";
  return "Output contract not evaluable.";
});
</script>

<template>
  <section class="contract-status-card" :data-status="contract.status">
    <p class="eyebrow">Reliability</p>
    <component :is="headingLevel">{{ heading }}</component>
    <p v-if="contract.status === 'breached'">
      {{ contract.violations }} invalid outputs affected
      {{ contract.affected_trials }} {{ affectedUnit }} and consumed
      {{ contract.counted_penalties }} counted turns.
    </p>
    <p v-else-if="contract.status === 'clean'">
      All {{ contract.evaluated_outputs }} evaluated outputs matched the public
      structured-action contract.
    </p>
    <p v-else>
      No structured outputs were available for contract evaluation.
    </p>
  </section>
</template>
