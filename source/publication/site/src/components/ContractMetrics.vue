<script setup lang="ts">
import { computed } from "vue";

import { contractPercent, contractStatusLabel } from "@/lib/format";
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
      label: "Valid format",
      value: contractPercent(
        props.contract.compliance_rate,
        props.contract.violations,
      ),
    },
    { label: "Format errors", value: String(props.contract.violations) },
    {
      label: "Turns used by format errors",
      value: String(props.contract.counted_penalties),
    },
  ];
  return props.compact
    ? shared
    : [
        { label: "Status", value: contractStatusLabel(props.contract.status) },
        { label: "Valid replies", value: String(props.contract.valid_outputs) },
        {
          label: "Checked replies",
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
