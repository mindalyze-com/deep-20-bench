<script setup lang="ts">
import RankingDataRow from "@/components/RankingDataRow.vue";
import { modelSummaryRoute } from "@/lib/route-location";
import type { PublicRunSummary } from "@/lib/types";

defineProps<{
  rank: number;
  run: PublicRunSummary;
}>();
</script>

<template>
  <RankingDataRow
    class="result-row--clickable result-row--navigable"
    :rank="rank"
    :name="run.model_name"
    :meta="run.model_id"
    :to="modelSummaryRoute(run.model_id, run.execution_id)"
  >
    <slot></slot>
  </RankingDataRow>
</template>
