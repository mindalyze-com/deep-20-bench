<script setup lang="ts">
import { computed } from "vue";

import { contractPercent, statusLabel } from "@/lib/format";
import type { ContractReliability } from "@/lib/types";

const props = withDefaults(
  defineProps<{
    contract: ContractReliability;
    compact?: boolean;
  }>(),
  { compact: false },
);

const metrics = computed(() => {
  const shared = [
    {
      label: "Compliance",
      value: contractPercent(
        props.contract.compliance_rate,
        props.contract.violations,
      ),
    },
    { label: "Violations", value: String(props.contract.violations) },
    {
      label: props.compact ? "Turn penalties" : "Counted-turn penalties",
      value: String(props.contract.counted_penalties),
    },
  ];
  return props.compact
    ? shared
    : [
        { label: "Status", value: statusLabel(props.contract.status) },
        { label: "Valid outputs", value: String(props.contract.valid_outputs) },
        {
          label: "Evaluated outputs",
          value: String(props.contract.evaluated_outputs),
        },
        ...shared,
      ];
});
</script>

<template>
  <dl>
    <div v-for="metric in metrics" :key="metric.label">
      <dt>{{ metric.label }}</dt>
      <dd>{{ metric.value }}</dd>
    </div>
  </dl>
</template>
